from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationUnavailableError(RuntimeError):
    """Raised when a translation backend is not configured or cannot be used."""


class Translator(ABC):
    service_name: str

    @abstractmethod
    def is_available(self) -> tuple[bool, str | None]:
        raise NotImplementedError

    @abstractmethod
    def translate_lines(
        self, lines: list[str], source_lang: str | None, target_lang: str
    ) -> list[str]:
        raise NotImplementedError
