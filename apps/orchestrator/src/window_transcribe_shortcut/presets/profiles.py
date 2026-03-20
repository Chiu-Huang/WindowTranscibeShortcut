from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    name: str
    source_lang: str | None
    target_lang: str
    description: str


PRESETS: dict[str, Preset] = {
    "en2zh": Preset("en2zh", "en", "zh", "英文 → 中文字幕"),
    "ja2zh": Preset("ja2zh", "ja", "zh", "日文 → 中文字幕"),
    "zh2zh": Preset("zh2zh", "zh", "zh", "中文 → 中文字幕"),
    'auto2zh': Preset("auto2zh", None, "zh", "自动检测语言 → 中文字幕"),
}

DEFAULT_PRESET = PRESETS["en2zh"]
