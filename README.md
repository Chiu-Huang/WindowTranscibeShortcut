# WindowTranscibeShortcut

Simple modular tool for:
1. Transcribe a video
2. Translate subtitles to Chinese when needed
3. Export `.srt` Chinese subtitles

## Features
- `pydantic-settings` + `.env` configuration
- WhisperX transcription backend
- DeepL translation backend (for non-Chinese source)
- Presets:
  - `en2zh` (英文 → 中文字幕)
  - `ja2zh` (日文 → 中文字幕)
  - `zh2zh` (中文 → 中文字幕)
- Drag-and-drop `.bat` scripts on Windows
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
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
OUTPUT_DIR=outputs
```

## CLI usage
```bash
window-transcribe-shortcut /path/to/video.mp4 --preset en2zh
```

Optional output path:
```bash
window-transcribe-shortcut /path/to/video.mp4 --preset ja2zh --output ./my_subtitle.srt
```

## Windows drag & drop
Use files in `scripts/`:
- `transcribe_zh.bat` (default preset: `en2zh`)
- `en_to_zh.bat`
- `ja_to_zh.bat`
- `zh_to_zh.bat`

Drag a video file onto one of these `.bat` files.

## Output
- Subtitle: `outputs/<video_name>.zh.srt`
- Logs: `outputs/logs/window_transcribe_shortcut.log`
