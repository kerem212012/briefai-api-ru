import asyncio
from typing import Annotated, Any, Protocol

from fastapi import Depends, FastAPI, HTTPException
from google import genai
from google.genai.errors import APIError
from pydantic import BaseModel, ConfigDict, Field

from app.setting import Settings, settings


class BriefRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product: str = Field(min_length=2, max_length=120)
    audience: str = Field(min_length=2, max_length=120)
    goal: str = Field(min_length=5, max_length=240)


class BriefResponse(BaseModel):
    improved_brief: str
    provider: str


class AIProvider(Protocol):
    name: str

    async def improve(self, brief: BriefRequest) -> str:
        """Return an improved product brief."""


class DemoProvider:
    name = "demo"

    async def improve(self, brief: BriefRequest) -> str:
        return (
            f"Product: {brief.product}. Audience: {brief.audience}. "
            f"Goal: {brief.goal}."
        )


class GeminiProvider:
    name = "gemini"

    def __init__(self, provider_settings: Settings, client: Any | None = None) -> None:
        if not provider_settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required for the Gemini backend")
        self.client = client or genai.Client(api_key=provider_settings.google_api_key)
        self.model = provider_settings.google_model

    async def improve(self, brief: BriefRequest) -> str:
        prompt = (
            "Improve the product brief using only the facts provided below.\n"
            "Do not invent facts, metrics, features, claims, or assumptions.\n"
            "Return a concise, actionable brief with this exact structure:\n"
            "Product: ...\nAudience: ...\nGoal: ...\n\n"
            f"Product: {brief.product}\n"
            f"Audience: {brief.audience}\n"
            f"Goal: {brief.goal}"
        )
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return (response.text or "").strip()


def get_ai_provider() -> AIProvider:
    if settings.ai_backend == "gemini":
        return GeminiProvider(settings)
    return DemoProvider()


AIProviderDependency = Annotated[AIProvider, Depends(get_ai_provider)]


app = FastAPI(title="BriefAI API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "ai_backend": settings.ai_backend}


@app.post("/briefs/improve", response_model=BriefResponse)
async def improve_brief(
    brief: BriefRequest,
    provider: AIProviderDependency,
) -> BriefResponse:
    try:
        improved_brief = await asyncio.wait_for(
            provider.improve(brief), timeout=settings.ai_timeout_seconds
        )
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail="AI provider timed out") from error
    except APIError as error:
        raise HTTPException(status_code=502, detail="AI provider request failed") from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI provider failed") from error

    if not improved_brief.strip():
        raise HTTPException(status_code=502, detail="AI provider returned an empty response")
    return BriefResponse(improved_brief=improved_brief, provider=provider.name)
