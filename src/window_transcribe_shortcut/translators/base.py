from __future__ import annotations


class TranslatorBackend:
    def translate_texts(self, texts: list[str], source_language: str, target_language: str) -> list[str]:  # pragma: no cover - interface only
        raise NotImplementedError
