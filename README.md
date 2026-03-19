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
- Configurable translation backends with DeepL, Google web translate, and LibreTranslate fallback support
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
# Optional translation backend settings
DEEPL_BASE_URL=https://api-free.deepl.com/v2
TRANSLATION_SERVICE=deepl
TRANSLATION_FALLBACK_SERVICES=google_web,libretranslate
GOOGLE_TRANSLATE_BASE_URL=https://translate.googleapis.com/translate_a/single
LIBRETRANSLATE_BASE_URL=
LIBRETRANSLATE_API_KEY=
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
OUTPUT_DIR=outputs
API_HOST=127.0.0.1
API_PORT=8765
```


### Translation backend behavior
- `TRANSLATION_SERVICE` chooses the primary translator. Supported values: `deepl`, `google_web`, `libretranslate`.
- `TRANSLATION_FALLBACK_SERVICES` is an ordered comma-separated fallback list. Duplicate services are ignored.
- If the primary translator is not configured or fails at runtime, the app automatically tries the next configured fallback.
- If every configured translation service is unavailable, the app skips translation and writes the original transcript instead of failing the whole job.

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
