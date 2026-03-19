from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"
_SUPPORTED_TRANSLATION_SERVICES = {"deepl", "google_web", "libretranslate"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepl_api_key: str | None = Field(default=None, alias="DEEPL_API_KEY")
    deepl_base_url: str = Field(default="https://api-free.deepl.com/v2", alias="DEEPL_BASE_URL")
    translation_service: str = Field(default="deepl", alias="TRANSLATION_SERVICE")
    translation_fallback_services: list[str] = Field(
        default_factory=lambda: ["google_web", "libretranslate"],
        alias="TRANSLATION_FALLBACK_SERVICES",
    )
    google_translate_base_url: str = Field(
        default="https://translate.googleapis.com/translate_a/single",
        alias="GOOGLE_TRANSLATE_BASE_URL",
    )
    libretranslate_base_url: str | None = Field(default=None, alias="LIBRETRANSLATE_BASE_URL")
    libretranslate_api_key: str | None = Field(default=None, alias="LIBRETRANSLATE_API_KEY")
    whisper_model: str = Field(default="small", alias="WHISPER_MODEL")
    device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    compute_type: str = Field(default="int8", alias="WHISPER_COMPUTE_TYPE")
    output_dir: Path = Field(default=Path("outputs"), alias="OUTPUT_DIR")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8765, alias="API_PORT")

    @field_validator("translation_service")
    @classmethod
    def validate_translation_service(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in _SUPPORTED_TRANSLATION_SERVICES:
            supported = ", ".join(sorted(_SUPPORTED_TRANSLATION_SERVICES))
            raise ValueError(f"Unsupported TRANSLATION_SERVICE '{value}'. Supported: {supported}")
        return normalized

    @field_validator("translation_fallback_services", mode="before")
    @classmethod
    def parse_translation_fallback_services(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            candidates = [item.strip().lower() for item in value.split(",") if item.strip()]
        elif isinstance(value, (list, tuple)):
            candidates = [str(item).strip().lower() for item in value if str(item).strip()]
        else:
            raise TypeError("TRANSLATION_FALLBACK_SERVICES must be a comma-separated string or list")

        unknown = [item for item in candidates if item not in _SUPPORTED_TRANSLATION_SERVICES]
        if unknown:
            supported = ", ".join(sorted(_SUPPORTED_TRANSLATION_SERVICES))
            raise ValueError(
                "Unsupported TRANSLATION_FALLBACK_SERVICES values: "
                f"{', '.join(unknown)}. Supported: {supported}"
            )
        return candidates


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump_json(indent=4))
