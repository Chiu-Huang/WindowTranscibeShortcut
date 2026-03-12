from __future__ import annotations

import gc
import threading
from collections import Counter
from typing import Iterable, List, Sequence

LANG_ALIAS_TO_NLLB = {
    "zh": "zho_Hans",
    "zh-cn": "zho_Hans",
    "zh-hans": "zho_Hans",
    "zho_hans": "zho_Hans",
    "en": "eng_Latn",
    "eng": "eng_Latn",
    "ja": "jpn_Jpan",
    "jpn": "jpn_Jpan",
}
TARGET_LANG = "zho_Hans"


class Translator:
    """NLLB translator with language detection and keep-alive memory management."""

    def __init__(
        self,
        model_name: str = "facebook/nllb-200-distilled-600M",
        ttl_seconds: int = 600,
    ) -> None:
        self._model_name = model_name
        self._ttl_seconds = ttl_seconds
        self._model = None
        self._tokenizer = None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def detect_source_language(
        self, texts: Sequence[str], hinted_language: str | None = None
    ) -> str:
        if hinted_language:
            normalized = LANG_ALIAS_TO_NLLB.get(hinted_language.strip().lower())
            if normalized:
                return normalized

        sample = "\n".join(texts[:20]).strip()
        if not sample:
            return "eng_Latn"

        counts = Counter(
            {
                "han": _count_range(sample, 0x4E00, 0x9FFF),
                "hiragana": _count_range(sample, 0x3040, 0x309F),
                "katakana": _count_range(sample, 0x30A0, 0x30FF),
            }
        )
        if counts["han"] > 0 and counts["hiragana"] == 0 and counts["katakana"] == 0:
            return "zho_Hans"
        if counts["hiragana"] + counts["katakana"] > 0:
            return "jpn_Jpan"
        return "eng_Latn"

    def translate(
        self,
        texts: Iterable[str],
        hinted_language: str | None = None,
    ) -> List[str]:
        items = list(texts)
        if not items:
            return []

        source_lang = self.detect_source_language(items, hinted_language)
        if source_lang == TARGET_LANG:
            return items

        with self._lock:
            model, tokenizer = self._ensure_model()
            self._reset_timer()

        tokenizer.src_lang = source_lang
        encoded = tokenizer(items, return_tensors="pt", padding=True, truncation=True)

        try:
            import torch

            if torch.cuda.is_available():
                encoded = {k: v.to("cuda") for k, v in encoded.items()}
                model = model.to("cuda")
        except Exception:
            pass

        generated = model.generate(
            **encoded,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(TARGET_LANG),
            max_new_tokens=512,
        )
        return tokenizer.batch_decode(generated, skip_special_tokens=True)

    def _ensure_model(self):
        if self._model is not None and self._tokenizer is not None:
            return self._model, self._tokenizer

        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(self._model_name)
        return self._model, self._tokenizer

    def _reset_timer(self) -> None:
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self._ttl_seconds, self.unload)
        self._timer.daemon = True
        self._timer.start()

    def unload(self) -> None:
        with self._lock:
            self._model = None
            self._tokenizer = None
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass


def _count_range(text: str, start: int, end: int) -> int:
    return sum(1 for ch in text if start <= ord(ch) <= end)
