# WindowTranscibeShortcut

This repository is now a Python mono-repo/workspace with three independently installable applications under `apps/`:

- `apps/orchestrator/` — preset resolution, job coordination, subtitle writing, and the compatibility CLI/API.
- `apps/transcribe-service/` — WhisperX-backed ASR-only transcription service.
- `apps/translation-service/` — translation service that owns the local Transformers/NLLB translation pipeline and translation HTTP APIs.

Each app has its own `pyproject.toml`, dependency set, and installable console scripts so the three runtimes can evolve together without sharing one Python environment.

## Layout

```text
apps/
  orchestrator/
  transcribe-service/
  translation-service/
```

## Install

Create a separate virtual environment for each application you want to run.

### Orchestrator
```bash
pip install -e ./apps/orchestrator
```

### Transcribe service
```bash
pip install -e ./apps/transcribe-service
```

### Translation service
```bash
pip install -e ./apps/translation-service
```

## Example environment variables

### Orchestrator
```env
OUTPUT_DIR=outputs
API_HOST=127.0.0.1
API_PORT=8765
TRANSCRIBE_SERVICE_URL=http://127.0.0.1:8766
TRANSLATION_SERVICE_URL=http://127.0.0.1:8876
```

### Transcribe service
```env
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
TRANSCRIBE_API_HOST=127.0.0.1
TRANSCRIBE_API_PORT=8766
```

### Translation service
```env
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M
TRANSLATION_DEVICE=auto
TRANSLATION_TORCH_DTYPE=auto
TRANSLATION_MAX_BATCH_SIZE=8
TRANSLATION_API_HOST=127.0.0.1
TRANSLATION_API_PORT=8876
```

## Windows launcher flow

1. Double-click `scripts/start_all_servers.bat`.
2. Wait for the launcher window to report that all three `/health` endpoints are ready:
   - `http://127.0.0.1:8766/health`
   - `http://127.0.0.1:8876/health`
   - `http://127.0.0.1:8765/health`
3. Drag/drop your media files onto one of the preset scripts in `scripts/` (for example `en_to_zh.bat`).
4. When you are finished, double-click `scripts/stop_all_servers.bat`.

The start launcher opens these console scripts in separate background windows/processes, warms up the transcribe and translation services, waits for the stack to become healthy, and stores the spawned PIDs so the stop launcher can shut everything down reliably later.

`./scripts/start_api_server.bat` is kept as a deprecated compatibility wrapper and now forwards to `start_all_servers.bat` so existing shortcuts still bring up the full stack.

## Manual startup order

If you prefer to launch each application yourself:

1. Start `transcribe-service-api --warmup` or `./apps/transcribe-service/entrypoint.sh --warmup`
2. Start `window-transcribe-translation-service-api --warmup`
3. Start `window-transcribe-shortcut-api`
4. Optionally run `window-transcribe-shortcut /path/to/video.mp4 --preset en2zh` for CLI usage

## API boundaries

- The orchestrator never imports WhisperX or local translation backend implementations directly.
- The transcribe service owns WhisperX-specific code and exposes ASR output plus metadata over HTTP.
- The transcribe service never decides whether translation is needed and never writes subtitle files.
- The translation service owns translation model loading and exposes line translation over HTTP.
