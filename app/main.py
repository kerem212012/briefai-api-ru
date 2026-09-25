from fastapi import FastAPI

app = FastAPI(title="BriefAI API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "ai_backend": "demo"}


# Add request/response schemas and injectable demo/Gemini providers.
