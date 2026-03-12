# WindowTranscibeShortcut

> Windows 全局快捷键语音转录/翻译工具（系统托盘常驻）
>
> A Windows tray app that lets you press a hotkey to transcribe media and generate Chinese subtitles.

## ✨ What this project does

`WindowTranscibeShortcut` runs in the background and listens for a global hotkey:

- Press **`Ctrl + Shift + T`** in Windows Explorer after selecting a file.
- The app captures that file path from clipboard (`CF_HDROP`).
- It automatically routes the task:
  - **Media file** (`.mp4`, `.mkv`, `.mp3`, `.wav`, etc.): Transcribe with WhisperX, then translate to Chinese, output `.srt`.
  - **Subtitle file** (`.srt`): Translate directly, output `_translated.srt`.

## 🖼️ Showcase

- Demo video: [`sample/Codex with MCP servers.mp4`](sample/Codex%20with%20MCP%20servers.mp4)
- Add your own tray screenshot / GIF here for best sharing effect.

> 推荐：发布前录制一个 10~20 秒 GIF，展示“选中文件 → 按快捷键 → 自动生成字幕”。

## ✅ Requirements

### For users

- **OS:** Windows 10 / 11 (primary target)
- **Python:** 3.10+
- **GPU:** Optional (CUDA GPU recommended for speed; CPU can work but slower)
- **Disk:** enough free space for model downloads (first run is heavier)

### For developers

- [uv](https://docs.astral.sh/uv/) package manager

## 🚀 Quick start (non-technical users)

1. Download this project ZIP from **GitHub Releases** (recommended), then extract.
2. Double-click `install.bat` and wait until dependency installation completes.
3. Double-click `start.vbs` to launch without showing a console window.
4. You should see a tray icon. Select a media file in Explorer and press `Ctrl + Shift + T`.

## 🧑‍💻 Developer setup

```bash
git clone <your-repo-url>
cd WindowTranscibeShortcut
uv sync
uv run window-transcribe-shortcut
```

## 🛠️ User scripts included

- `install.bat`:
  - Checks whether `uv` is installed.
  - If not installed, prints a clear installation hint.
  - Runs `uv sync`.
- `start.vbs`:
  - Starts app with hidden console using `uv run window-transcribe-shortcut`.
- `create_shortcut.bat`:
  - Creates a Desktop shortcut to `start.vbs`.

## 🎮 Usage notes

- **Default hotkey:** `Ctrl + Shift + T`
- **First run:** model download can take time (depends on network and model size).
- **Settings UI:** right-click tray icon → open settings.
- **Config path:** `%APPDATA%\WindowTranscibeShortcut\config.json`

## 📁 Recommended repository contents

Keep your repository clean for internet sharing:

**Should include**

- `src/` (core code)
- `pyproject.toml`
- `README.md`
- `LICENSE`
- user helper scripts (`install.bat`, `start.vbs`, optional `create_shortcut.bat`)

**Should NOT include**

- `.venv/`
- `__pycache__/`
- large model weights (`*.pt`, `*.bin`, `*.safetensors`, etc.)
- personal/local secret configs

## 📦 Releases best practice

When sharing with users, prefer **GitHub Releases** over `Code -> Download ZIP` of the latest branch:

1. Create a release tag, e.g. `v0.1.0`.
2. Add release notes.
3. Upload a clean ZIP asset (`WindowTranscribeShortcut-v0.1.0.zip`) with scripts included.
4. Tell users to download from Releases.

This gives users a stable version instead of in-progress source code.

## 🧪 Basic checks

```bash
uv run pytest -q
```

Optional integration tests (heavy model initialization):

```bash
uv run pytest -q --run-integration
```

## 📄 License

MIT License. See [LICENSE](LICENSE).
