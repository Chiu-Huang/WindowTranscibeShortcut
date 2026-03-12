from __future__ import annotations

import argparse
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

LOG_PATH = ROOT / "test" / "results" / "test_transcription.log"


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def run(sample_file: Path) -> int:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    log("=== test_transcription.py start ===")
    log(f"python={sys.version.split()[0]} platform={platform.platform()}")

    log("1) CUDA availability check")
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda_available else 0
        log(f"CUDA available: {cuda_available}, device_count: {device_count}")
    except Exception as exc:  # noqa: BLE001
        log(f"CUDA check failed: {exc}")

    log(f"2) Transcription model test input: {sample_file}")
    if not sample_file.exists():
        log("ERROR: sample file does not exist.")
        return 1

    try:
        from window_transcribe_shortcut.transcriber import Transcriber

        transcriber = Transcriber(model_name="tiny")
        result = transcriber.transcribe(sample_file)
        log(f"Transcription language={result.get('language')} segments={len(result.get('segments', []))}")
    except Exception as exc:  # noqa: BLE001
        log(f"ERROR: transcription failed: {exc}")
        log(traceback.format_exc())
        return 1

    log("3) Translation + language detection test")
    try:
        from window_transcribe_shortcut.translator import Translator

        translator = Translator()
        detected = translator.detect_source_language(["hello world"]) 
        translated = translator.translate(["hello world"], hinted_language="en")
        log(f"Detected='hello world' -> {detected}; translated sample count={len(translated)}")
    except Exception as exc:  # noqa: BLE001
        log(f"ERROR: translation failed: {exc}")
        log(traceback.format_exc())
        return 1

    log("4) SRT write test")
    try:
        from window_transcribe_shortcut.main import App

        srt_path = ROOT / "test" / "results" / "transcription_output.srt"
        segments = result.get("segments", [])
        translated_texts = [seg.get("text", "") for seg in segments]
        App._save_segments_as_srt(srt_path, segments, translated_texts)
        log(f"SRT written: {srt_path} size={srt_path.stat().st_size} bytes")
    except Exception as exc:  # noqa: BLE001
        log(f"ERROR: srt write failed: {exc}")
        log(traceback.format_exc())
        return 1

    log("=== test_transcription.py success ===")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sample_file",
        nargs="?",
        default="sample/Codex with MCP servers.mp4",
        help="Path to sample media file",
    )
    args = parser.parse_args()
    return run(Path(args.sample_file))


if __name__ == "__main__":
    raise SystemExit(main())
