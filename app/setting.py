from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)

	ai_backend: Literal["demo", "gemini"] = "demo"
	google_api_key: str | None = None
	google_model: str = "gemini-2.5-flash"
	ai_timeout_seconds: float = Field(default=10.0, gt=0, le=120)


settings = Settings()
