# Orchestrator

Coordinates subtitle jobs by calling the transcribe and translation services over HTTP, deciding whether translation is needed from the selected preset plus the detected language, and then writing the final `.srt` output.

## Minimal runtime dependencies

The orchestrator only depends on:

- `fastapi`
- `uvicorn`
- `requests`
- `pydantic-settings`
- `loguru`
- `srt`

It never imports WhisperX, Hugging Face, or the translation backends directly, so it can start even when those packages are not installed locally.
