from __future__ import annotations

from pathlib import Path

import pytest

from window_transcribe_shortcut.main import App
from window_transcribe_shortcut.transcriber import Transcriber
from window_transcribe_shortcut.translator import Translator


@pytest.fixture(scope="session")
def sample_file() -> Path:
    path = Path("sample/Codex with MCP servers.mp4")
    if not path.exists():
        pytest.skip(f"Sample media file does not exist: {path}")
    return path


@pytest.fixture(scope="session")
def transcriber(pytestconfig: pytest.Config) -> Transcriber:
    if not pytestconfig.getoption("--run-integration"):
        pytest.skip("need --run-integration to initialize whisperx model")
    return Transcriber(model_name="tiny")


@pytest.fixture(scope="session")
def translator(pytestconfig: pytest.Config) -> Translator:
    if not pytestconfig.getoption("--run-integration"):
        pytest.skip("need --run-integration to initialize transformer model")
    return Translator()


def test_cuda_availability_check() -> None:
    torch = pytest.importorskip("torch")
    available = torch.cuda.is_available()
    assert isinstance(available, bool)


@pytest.mark.integration
def test_transcribe_structure(sample_file: Path, transcriber: Transcriber) -> None:
    result = transcriber.transcribe(sample_file)

    assert "language" in result
    assert "segments" in result
    assert isinstance(result["segments"], list)
    assert len(result["segments"]) > 0

    first = result["segments"][0]
    assert "text" in first
    assert "start" in first
    assert "end" in first
    assert str(first["text"]).strip() != ""


@pytest.mark.integration
def test_translate_transcribed_text(
    sample_file: Path, transcriber: Transcriber, translator: Translator
) -> None:
    result = transcriber.transcribe(sample_file)
    texts = [str(seg.get("text", "")) for seg in result["segments"] if str(seg.get("text", "")).strip()]
    assert texts, "transcription produced no non-empty texts"

    translated = translator.translate(texts, hinted_language=result.get("language"))

    assert len(translated) == len(texts)
    assert any(t.strip() for t in translated)


@pytest.mark.integration
def test_save_srt(
    tmp_path: Path, sample_file: Path, transcriber: Transcriber, translator: Translator
) -> None:
    result = transcriber.transcribe(sample_file)
    segments = result["segments"]
    texts = [str(seg.get("text", "")) for seg in segments]
    translated = translator.translate(texts, hinted_language=result.get("language"))

    out = tmp_path / "integration_output.srt"
    App._save_segments_as_srt(out, segments, translated)

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "-->" in content
    assert len(content) > 100
