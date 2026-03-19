from __future__ import annotations

import unittest

from window_transcribe_shortcut.models import Segment, Transcript
from window_transcribe_shortcut.pipeline import TranscriptionService
from window_transcribe_shortcut.translators.base import TranslationUnavailableError


class StubTranslator:
    def __init__(
        self,
        service_name: str,
        *,
        available: bool = True,
        result=None,
        error: Exception | None = None,
    ) -> None:
        self.service_name = service_name
        self._available = available
        self._result = result
        self._error = error

    def is_available(self) -> tuple[bool, str | None]:
        if self._available:
            return True, None
        return False, f"{self.service_name} unavailable"

    def translate_lines(
        self, lines: list[str], source_lang: str | None, target_lang: str
    ) -> list[str]:
        if self._error is not None:
            raise self._error
        if self._result is None:
            return lines
        return self._result


class TranslationFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TranscriptionService()
        self.transcript = Transcript(
            language="en",
            segments=[Segment(start=0.0, end=1.0, text="hello")],
        )

    def test_uses_next_available_fallback_when_primary_unavailable(self) -> None:
        self.service._build_translators = lambda: [  # type: ignore[method-assign]
            StubTranslator("deepl", available=False),
            StubTranslator("google_web", result=["你好"]),
        ]

        translated = self.service._translate_transcript(self.transcript, "en", "zh")

        self.assertEqual(translated.language, "zh")
        self.assertEqual([segment.text for segment in translated.segments], ["你好"])

    def test_keeps_original_transcript_when_all_services_fail(self) -> None:
        self.service._build_translators = lambda: [  # type: ignore[method-assign]
            StubTranslator("deepl", available=False),
            StubTranslator("google_web", error=RuntimeError("network error")),
            StubTranslator(
                "libretranslate",
                error=TranslationUnavailableError("missing config"),
            ),
        ]

        translated = self.service._translate_transcript(self.transcript, "en", "zh")

        self.assertIs(translated, self.transcript)

    def test_skips_invalid_translation_result_length(self) -> None:
        self.service._build_translators = lambda: [  # type: ignore[method-assign]
            StubTranslator("deepl", result=[]),
            StubTranslator("google_web", result=["你好"]),
        ]

        translated = self.service._translate_transcript(self.transcript, "en", "zh")

        self.assertEqual([segment.text for segment in translated.segments], ["你好"])


if __name__ == "__main__":
    unittest.main()
