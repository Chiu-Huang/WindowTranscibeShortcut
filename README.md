# WindowTranscibeShortcut

Simple modular tool for:
1. Transcribe a video
2. Translate subtitles to Chinese when needed
3. Export `.srt` Chinese subtitles

## Why add a FastAPI backend?
The main bottleneck in the original drag-and-drop workflow was repeated Python startup plus repeated WhisperX model loading on every `.bat` invocation. The new API mode keeps one backend process alive, so the heavy model and imports stay warm between jobs.

## Features
- `pydantic-settings` + `.env` configuration
- WhisperX transcription backend with in-process model caching
- FastAPI server for persistent local inference
- DeepL translation backend with optional HTTP fallback to a separate local translation service
- Presets:
  - `en2zh` (英文 → 中文字幕)
  - `ja2zh` (日文 → 中文字幕)
  - `zh2zh` (中文 → 中文字幕)
- Windows drag-and-drop `.bat` scripts that call the local API
- Loguru logging + clear error prompt with log file path

## Install
```bash
pip install -e .
```

## Environment
Create `.env` in project root:

```env
DEEPL_API_KEY=your_deepl_key
# Optional
DEEPL_BASE_URL=https://api-free.deepl.com/v2
LOCAL_TRANSLATION_ENABLED=false
LOCAL_TRANSLATION_URL=http://127.0.0.1:8876/translate
TRANSLATION_REQUEST_TIMEOUT_SECONDS=60
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
OUTPUT_DIR=outputs
API_HOST=127.0.0.1
API_PORT=8765
```

## Direct CLI usage
You can still run the original one-shot CLI if you want:

```bash
window-transcribe-shortcut /path/to/video.mp4 --preset en2zh
```

Optional output path:
```bash
window-transcribe-shortcut /path/to/video.mp4 --preset ja2zh --output ./my_subtitle.srt
```

Inspect presets:
```bash
window-transcribe-shortcut --list-presets
```

Inspect effective configuration:
```bash
window-transcribe-shortcut --show-config
```

Verbose debugging:
```bash
window-transcribe-shortcut /path/to/video.mp4 --preset en2zh --debug
```

## Recommended architecture for optional offline translation
For your Hugging Face idea, the most practical next step is to **keep this app as the WhisperX/API orchestrator** and make the offline translator a **separate HTTP service** with its own environment. That gives you the same request/response workflow you already like, while keeping the heavy `transformers`/`torch` translation stack isolated from WhisperX.

A good incremental split is:

```
repo/
  apps/
    whisperx-api/           # current app / transcription entrypoint
    translation-service/    # optional Hugging Face or other translator
```

Recommended responsibility split:
- `whisperx-api`: FastAPI endpoints, job orchestration, WhisperX, subtitle writing, DeepL-first logic
- `translation-service`: only translation backends, such as MarianMT / NLLB / M2M100, exposed over HTTP

### Why this is a good fit
- Keeps the current API-call approach intact
- Lets WhisperX and Hugging Face use different virtual environments or Docker images
- Makes local/offline translation truly optional
- Avoids installing `transformers` into the main WhisperX runtime unless you really want that later

### Fallback order implemented now
1. Try DeepL when `DEEPL_API_KEY` is configured
2. If DeepL is unavailable or fails **and** `LOCAL_TRANSLATION_ENABLED=true`, call `LOCAL_TRANSLATION_URL`
3. If neither backend is available, keep the original transcript and log a warning

### Suggested local translation API contract
If you later build a Hugging Face service, this app now expects a simple JSON API like:

`POST /translate`

Request:
```json
{
  "lines": ["hello", "how are you"],
  "source_lang": "en",
  "target_lang": "zh"
}
```

Response:
```json
{
  "translations": ["你好", "你好吗"]
}
```

### Model choice note
If you want one multilingual Facebook model for an optional service, **NLLB** is usually the stronger architectural fit than older Marian-style per-pair models, because it is designed for many-language translation. Whether it is the right runtime choice depends on your hardware and latency tolerance, so keeping it behind a separate service boundary is the safest first move.

## FastAPI backend usage
Start the persistent API server:

```bash
window-transcribe-shortcut-api --warmup
```

Or with Uvicorn reload during development:

```bash
window-transcribe-shortcut-api --reload --debug
```

### API endpoints
- `GET /health` — backend status + whether the WhisperX model is already loaded
- `GET /presets` — list supported presets
- `POST /warmup` — load the WhisperX model before the first real request
- `POST /transcribe` — transcribe a local file path on the same machine as the server

Example request:

```bash
curl -X POST http://127.0.0.1:8765/transcribe \
  -H "Content-Type: application/json" \
  -d '{"video":"/absolute/path/to/video.mp4","preset":"en2zh"}'
```

## Windows drag & drop workflow
1. Start `scripts/start_api_server.bat` once.
2. Leave that console window open.
3. Drag a video file onto one of these scripts:
   - `scripts/transcribe_zh.bat` (default preset: `en2zh`)
   - `scripts/en_to_zh.bat`
   - `scripts/ja_to_zh.bat`
   - `scripts/zh_to_zh.bat`

Each script sends an HTTP request to `http://127.0.0.1:8765/transcribe` instead of starting a fresh Python transcription process every time.

## Output
- Subtitle: `outputs/<video_name>.zh.srt`
- Logs: `outputs/logs/window_transcribe_shortcut.log`
