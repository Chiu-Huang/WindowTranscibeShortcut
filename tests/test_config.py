from __future__ import annotations

import unittest

from window_transcribe_shortcut.config import Settings


class SettingsTests(unittest.TestCase):
    def test_parses_translation_fallback_services_csv(self) -> None:
        settings = Settings(
            TRANSLATION_SERVICE="google_web",
            TRANSLATION_FALLBACK_SERVICES="deepl, libretranslate",
        )

        self.assertEqual(settings.translation_service, "google_web")
        self.assertEqual(
            settings.translation_fallback_services,
            ["deepl", "libretranslate"],
        )

    def test_rejects_unknown_translation_service(self) -> None:
        with self.assertRaises(ValueError):
            Settings(TRANSLATION_SERVICE="invalid-service")


if __name__ == "__main__":
    unittest.main()
