# Window Transcribe Shortcut

Minimal modular tool to convert video/audio to **Chinese subtitles (SRT)**.

- Transcribe with WhisperX
- Auto-translate non-Chinese transcripts via DeepL
- Presets:
  - `en2zh` 英文 → 中文字幕 (default)
  - `ja2zh` 日文 → 中文字幕
  - `zh2zh` 中文 → 中文字幕 (no translation)
- Logging with `loguru`
- Errors are both logged and shown to user

## Setup

```bash
pip install -e .
cp .env.example .env
```

Set your DeepL key in `.env`:

```env
WTS_DEEPL_API_KEY=...
```

Optional WhisperX settings:

```env
WTS_WHISPER_MODEL=small
WTS_WHISPER_MODEL_PATH=C:/models/whisperx
WTS_WHISPER_DEVICE=cpu
```

`WTS_WHISPER_MODEL_PATH` is optional and is passed to WhisperX as the model download/cache directory.

## Usage

```bash
window-transcribe-shortcut path/to/video.mp4 --preset en2zh
```

Optional:

```bash
window-transcribe-shortcut path/to/video.mp4 --preset ja2zh
window-transcribe-shortcut path/to/video.mp4 --preset zh2zh
window-transcribe-shortcut path/to/video.mp4 --source-lang en
```

Output is written to `output/<input_name>.zh.srt` by default.

## Windows drag-and-drop

Use scripts in `scripts/`:

- `transcribe_zh.bat`
- `en_to_zh.bat`
- `ja_to_zh.bat`
- `zh_to_zh.bat`

Drag a video file onto a `.bat` file to run.
