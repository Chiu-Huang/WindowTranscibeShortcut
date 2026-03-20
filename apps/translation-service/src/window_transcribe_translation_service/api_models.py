from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class SubtitleSegment(BaseModel):
    start: float
    end: float
    text: str


class TranslationRequest(BaseModel):
    lines: list[str] | None = Field(default=None)
    segments: list[SubtitleSegment] | None = Field(default=None)
    source_lang: str | None = Field(default=None)
    target_lang: str = Field(default="zh")
    provider: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_input_mode(self) -> "TranslationRequest":
        has_lines = self.lines is not None
        has_segments = self.segments is not None
        if has_lines == has_segments:
            raise ValueError("Provide exactly one of 'lines' or 'segments'.")
        return self


class ProviderFailureResponse(BaseModel):
    provider: str
    message: str
    error_type: str
    retryable: bool


class ProviderInfoResponse(BaseModel):
    name: str
    enabled: bool
    configured: bool
    description: str
    priority: int


class TranslationResponse(BaseModel):
    provider: str
    translations: list[str]
    segments: list[SubtitleSegment] | None = None
    failures: list[ProviderFailureResponse] = Field(default_factory=list)


class TranslationErrorResponse(BaseModel):
    error: str
    failures: list[ProviderFailureResponse] = Field(default_factory=list)


class ProvidersResponse(BaseModel):
    providers: list[ProviderInfoResponse]


class HealthResponse(BaseModel):
    status: str
    provider_order: list[str]
    providers: list[ProviderInfoResponse]
    model: str
    device: str
    loaded: bool
