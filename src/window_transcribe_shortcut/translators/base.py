from __future__ import annotations

from abc import ABC, abstractmethod


class Translator(ABC):
    @abstractmethod
    def translate_lines(self, lines: list[str], source_lang: str | None, target_lang: str) -> list[str]:
        raise NotImplementedError
