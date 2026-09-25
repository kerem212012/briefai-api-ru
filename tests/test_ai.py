import asyncio

import app.main as main
from fastapi.testclient import TestClient

client = TestClient(main.app)


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
