import asyncio

import app.main as main
from app.setting import Settings
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_gemini_provider_uses_fake_client_and_cleans_response() -> None:
    class FakeModels:
        def __init__(self):
            self.model = None
            self.prompt = None

        async def generate_content(self, *, model, contents):
            self.model = model
            self.prompt = contents
            return type("Response", (), {"text": "  Improved brief.  "})()

    class FakeClient:
        def __init__(self, models):
            self.aio = type("Aio", (), {"models": models})()

    models = FakeModels()
    provider = main.GeminiProvider(
        Settings(google_api_key="test-key", google_model="test-model"),
        client=FakeClient(models),
    )
    brief = main.BriefRequest(
        product="Study planner",
        audience="Python students",
        goal="Plan weekly practice",
    )

    result = asyncio.run(provider.improve(brief))

    assert result == "Improved brief."
    assert models.model == "test-model"
    assert "Product: Study planner" in models.prompt
    assert "Audience: Python students" in models.prompt
    assert "Goal: Plan weekly practice" in models.prompt
    assert "Do not invent facts" in models.prompt


def test_demo_provider_works_without_key() -> None:
    response = client.post(
        "/briefs/improve",
        json={
            "product": "Study planner",
            "audience": "Python students",
            "goal": "Plan weekly practice",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "demo"
    assert "Study planner" in body["improved_brief"]


def test_invalid_brief_is_rejected_before_ai_call() -> None:
    response = client.post("/briefs/improve", json={"product": "x", "audience": "x", "goal": "x"})
    assert response.status_code == 422


def test_timeout_and_empty_provider_are_mapped() -> None:
    class SlowProvider:
        name = "slow"

        async def improve(self, brief):
            await asyncio.sleep(0.05)
            return "late"

    class EmptyProvider:
        name = "empty"

        async def improve(self, brief):
            return ""

    old_timeout = main.settings.ai_timeout_seconds
    main.settings.ai_timeout_seconds = 0.001
    main.app.dependency_overrides[main.get_ai_provider] = lambda: SlowProvider()
    payload = {
        "product": "Study planner",
        "audience": "Python students",
        "goal": "Plan weekly practice",
    }
    assert client.post("/briefs/improve", json=payload).status_code == 504
    main.app.dependency_overrides[main.get_ai_provider] = lambda: EmptyProvider()
    assert client.post("/briefs/improve", json=payload).status_code == 502
    main.app.dependency_overrides.clear()
    main.settings.ai_timeout_seconds = old_timeout


def test_api_error_is_mapped_without_exposing_provider_details() -> None:
    class FailingProvider:
        name = "gemini"

        async def improve(self, brief):
            raise main.APIError(500, {"error": {"message": "SECRET_API_KEY"}})

    main.app.dependency_overrides[main.get_ai_provider] = lambda: FailingProvider()
    response = client.post(
        "/briefs/improve",
        json={
            "product": "Study planner",
            "audience": "Python students",
            "goal": "Plan weekly practice",
        },
    )
    main.app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "AI provider request failed"}
    assert "SECRET_API_KEY" not in response.text
