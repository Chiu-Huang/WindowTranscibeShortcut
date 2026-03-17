from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    source_language: str
    target_language: str = "zh"


PRESETS: dict[str, Preset] = {
    "en2zh": Preset(key="en2zh", label="英文 → 中文字幕", source_language="en"),
    "ja2zh": Preset(key="ja2zh", label="日文 → 中文字幕", source_language="ja"),
    "zh2zh": Preset(key="zh2zh", label="中文 → 中文字幕", source_language="zh"),
}

DEFAULT_PRESET_KEY = "en2zh"
