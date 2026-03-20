from __future__ import annotations

from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    lines: list[str] = Field(default_factory=list)
    source_lang: str | None = Field(default=None)
    target_lang: str = Field(default="zh")


class TranslationResponse(BaseModel):
    translations: list[str]


class HealthResponse(BaseModel):
    status: str
    deepl_configured: bool
    local_translation_enabled: bool
