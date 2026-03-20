# WindowTranscibeShortcut

This repository is now a Python mono-repo/workspace with three independently installable applications under `apps/`:

- `apps/orchestrator/` — preset resolution, job coordination, subtitle writing, and the compatibility CLI/API.
- `apps/transcribe-service/` — WhisperX-backed ASR-only transcription service.
- `apps/translation-service/` — translation service wrapping DeepL and optional HTTP fallback translation backends.

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
DEEPL_API_KEY=your_deepl_key
DEEPL_BASE_URL=https://api-free.deepl.com/v2
LOCAL_TRANSLATION_ENABLED=false
LOCAL_TRANSLATION_URL=http://127.0.0.1:9988/translate
TRANSLATION_REQUEST_TIMEOUT_SECONDS=60
TRANSLATION_API_HOST=127.0.0.1
TRANSLATION_API_PORT=8876
```

## Recommended startup order

1. Start `transcribe-service-api --warmup` or `./apps/transcribe-service/entrypoint.sh --warmup`
2. Start `window-transcribe-translation-service-api`
3. Run either:
   - `window-transcribe-shortcut /path/to/video.mp4 --preset en2zh`
   - `window-transcribe-shortcut-api --reload`

## API boundaries

- The orchestrator never imports WhisperX, DeepL, or local translation backend implementations directly.
- The transcribe service owns WhisperX-specific code and exposes ASR output plus metadata over HTTP.
- The transcribe service never decides whether translation is needed and never writes subtitle files.
- The translation service owns translation backend selection and exposes line translation over HTTP.
