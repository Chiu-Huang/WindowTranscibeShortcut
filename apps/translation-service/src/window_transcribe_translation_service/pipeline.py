from __future__ import annotations

import logging
from dataclasses import asdict
from functools import lru_cache
from typing import Any

import torch
from fastapi import HTTPException
from transformers import pipeline

from window_transcribe_translation_service.api_models import SubtitleSegment
from window_transcribe_translation_service.config import settings
from window_transcribe_translation_service.providers.base import (
    ProviderDescriptor,
    TranslationAttempt,
    TranslationProviderError,
)

LOGGER = logging.getLogger(__name__)

LANGUAGE_ALIASES = {
    "ar": "arb_Arab",
    "de": "deu_Latn",
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "hi": "hin_Deva",
    "it": "ita_Latn",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "pt": "por_Latn",
    "ru": "rus_Cyrl",
    "tr": "tur_Latn",
    "uk": "ukr_Cyrl",
    "vi": "vie_Latn",
    "zh": "zho_Hans",
    "zh-cn": "zho_Hans",
    "zh-hans": "zho_Hans",
    "zh-tw": "zho_Hant",
    "zh-hant": "zho_Hant",
}

TORCH_DTYPES = {
    "auto": None,
    "float16": torch.float16,
    "float32": torch.float32,
    "bfloat16": torch.bfloat16,
}


class TranslationEngine:
    provider_name = "local_transformers"
    provider_description = "Local Transformers/Torch translation pipeline"

    def __init__(
        self,
        *,
        model_name: str,
        device: str,
        torch_dtype: str,
        max_batch_size: int,
    ) -> None:
        self.model_name = model_name
        self.max_batch_size = max_batch_size
        self.device_index, self.device_label = self._resolve_device(device)
        self.torch_dtype = self._resolve_torch_dtype(torch_dtype)
        self._pipeline = None

    @staticmethod
    def _resolve_device(device: str) -> tuple[int, str]:
        normalized = device.strip().lower()
        if normalized == "auto":
            return (0, "cuda") if torch.cuda.is_available() else (-1, "cpu")
        if normalized == "cuda":
            if not torch.cuda.is_available():
                raise TranslationProviderError(
                    TranslationEngine.provider_name,
                    "TRANSLATION_DEVICE is set to 'cuda' but CUDA is not available.",
                    error_type="configuration_error",
                )
            return 0, "cuda"
        if normalized == "cpu":
            return -1, "cpu"
        raise TranslationProviderError(
            TranslationEngine.provider_name,
            f"Unsupported TRANSLATION_DEVICE value: {device}",
            error_type="configuration_error",
        )

    @staticmethod
    def _resolve_torch_dtype(value: str) -> torch.dtype | None:
        normalized = value.strip().lower()
        if normalized == "auto":
            return torch.float16 if torch.cuda.is_available() else torch.float32
        dtype = TORCH_DTYPES.get(normalized)
        if dtype is None and normalized not in TORCH_DTYPES:
            raise TranslationProviderError(
                TranslationEngine.provider_name,
                f"Unsupported TRANSLATION_TORCH_DTYPE value: {value}",
                error_type="configuration_error",
            )
        return dtype

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.provider_name,
            enabled=True,
            configured=True,
            description=f"{self.provider_description} ({self.model_name} on {self.device_label})",
            priority=1,
        )

    def health_summary(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "model": self.model_name,
            "device": self.device_label,
            "loaded": self.is_loaded,
            "max_batch_size": self.max_batch_size,
        }

    def warmup(self) -> None:
        if self._pipeline is not None:
            return

        LOGGER.info("Loading translation pipeline for %s on %s", self.model_name, self.device_label)
        model_kwargs: dict[str, Any] = {}
        if self.torch_dtype is not None:
            model_kwargs["torch_dtype"] = self.torch_dtype
        self._pipeline = pipeline(
            task="translation",
            model=self.model_name,
            device=self.device_index,
            model_kwargs=model_kwargs,
        )

    def translate(self, lines: list[str], source_lang: str, target_lang: str) -> list[str]:
        if not lines:
            return []

        self.warmup()
        assert self._pipeline is not None
        outputs = self._pipeline(
            lines,
            src_lang=source_lang,
            tgt_lang=target_lang,
            batch_size=min(len(lines), self.max_batch_size),
            clean_up_tokenization_spaces=True,
        )
        return [str(item["translation_text"]) for item in outputs]


@lru_cache(maxsize=1)
def get_engine() -> TranslationEngine:
    return TranslationEngine(
        model_name=settings.model_name,
        device=settings.device,
        torch_dtype=settings.torch_dtype,
        max_batch_size=settings.max_batch_size,
    )


def normalize_lang(value: str | None) -> str:
    if value is None:
        raise HTTPException(status_code=400, detail="source_lang is required for the local translation model.")
    stripped = value.strip()
    normalized = stripped.replace("_", "-").lower()
    if stripped in LANGUAGE_ALIASES.values():
        return stripped
    if normalized in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[normalized]
    raise HTTPException(status_code=400, detail=f"Unsupported language code: {value}")


class TranslationService:
    def __init__(self) -> None:
        self.engine = get_engine()

    def health_summary(self) -> tuple[list[str], list[dict[str, object]], dict[str, Any]]:
        provider = asdict(self.engine.describe())
        return [self.engine.provider_name], [provider], self.engine.health_summary()

    def list_providers(self) -> list[dict[str, object]]:
        return [asdict(self.engine.describe())]

    def warmup(self) -> dict[str, Any]:
        self.engine.warmup()
        return {
            "status": "warmed",
            "provider": self.engine.provider_name,
            "model": self.engine.model_name,
            "device": self.engine.device_label,
        }

    def translate_lines(
        self,
        lines: list[str],
        *,
        source_lang: str | None,
        target_lang: str,
        provider: str | None = None,
    ) -> TranslationAttempt:
        if provider and provider != self.engine.provider_name:
            raise TranslationProviderError(
                self.engine.provider_name,
                f"Unknown provider '{provider}'. Available provider: {self.engine.provider_name}.",
                error_type="unknown_provider",
            )

        normalized_target = normalize_lang(target_lang)
        normalized_source = normalize_lang(source_lang)
        if normalized_source == normalized_target:
            translations = lines[:]
        else:
            try:
                translations = self.engine.translate(lines, normalized_source, normalized_target)
            except HTTPException:
                raise
            except TranslationProviderError:
                raise
            except Exception as exc:
                raise TranslationProviderError(
                    self.engine.provider_name,
                    f"Translation failed: {exc}",
                    error_type="provider_error",
                ) from exc

        return TranslationAttempt(
            provider=self.engine.provider_name,
            translations=translations,
            failures=[],
        )

    def translate_segments(
        self,
        segments: list[SubtitleSegment],
        *,
        source_lang: str | None,
        target_lang: str,
        provider: str | None = None,
    ) -> tuple[TranslationAttempt, list[SubtitleSegment]]:
        attempt = self.translate_lines(
            [segment.text for segment in segments],
            source_lang=source_lang,
            target_lang=target_lang,
            provider=provider,
        )
        translated_segments = [
            SubtitleSegment(start=segment.start, end=segment.end, text=text)
            for segment, text in zip(segments, attempt.translations, strict=True)
        ]
        return attempt, translated_segments
