from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = APP_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    translation_provider_order_raw: str = Field(default="deepl,http,hf_nllb", alias="TRANSLATION_PROVIDER_ORDER")
    deepl_api_key: str | None = Field(default=None, alias="DEEPL_API_KEY")
    deepl_base_url: str = Field(default="https://api-free.deepl.com/v2", alias="DEEPL_BASE_URL")
    http_translation_enabled: bool = Field(default=False, alias="HTTP_TRANSLATION_ENABLED")
    http_translation_url: str = Field(default="http://127.0.0.1:9988/translate", alias="HTTP_TRANSLATION_URL")
    huggingface_nllb_enabled: bool = Field(default=False, alias="HUGGINGFACE_NLLB_ENABLED")
    huggingface_nllb_url: str = Field(default="", alias="HUGGINGFACE_NLLB_URL")
    huggingface_nllb_model: str = Field(
        default="facebook/nllb-200-distilled-600M",
        alias="HUGGINGFACE_NLLB_MODEL",
    )
    translation_request_timeout_seconds: float = Field(
        default=60.0,
        alias="TRANSLATION_REQUEST_TIMEOUT_SECONDS",
    )
    api_host: str = Field(default="127.0.0.1", alias="TRANSLATION_API_HOST")
    api_port: int = Field(default=8876, alias="TRANSLATION_API_PORT")

    @property
    def translation_provider_order(self) -> list[str]:
        return [item.strip() for item in self.translation_provider_order_raw.split(",") if item.strip()]

    @field_validator("translation_provider_order_raw")
    @classmethod
    def validate_provider_order(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("TRANSLATION_PROVIDER_ORDER must contain at least one provider name.")
        return value


settings = Settings()
