# WindowTranscibeShortcut: AI-Powered Transcription & Translation Pipeline

## 📌 Project Overview
WindowTranscibeShortcut is a modular, background-running Windows application designed to seamlessly transcribe and translate media files. By simply selecting a file in Windows Explorer and pressing a global hotkey, the application extracts the file path, processes the media using local AI models, and generates a bilingual `.srt` subtitle file.

The system is highly decoupled, utilizing a 10-minute Keep-Alive VRAM management strategy to balance processing speed and GPU memory usage.

## ✨ Core Features
- **Seamless OS Integration**: Runs in the system tray. Listens for `Ctrl + Shift + T` to grab the currently selected file in Windows Explorer via clipboard (`CF_HDROP`).
- **Smart Routing**: 
  - If a video/audio file is selected: Runs `whisperx` (Transcription) -> `transformers` (Translation) -> Outputs `.srt`.
  - If a `.srt` file is selected: Skips transcription, runs `transformers` directly -> Outputs `_translated.srt`.
- **Intelligent VRAM Management**: Models are lazy-loaded. After a task finishes, models stay in GPU memory for 10 minutes (Keep-Alive). If no new tasks arrive within 10 minutes, the memory is purged (`gc.collect()`, `torch.cuda.empty_cache()`).
- **Modern GUI**: A sleek, dark-mode settings interface built with `flet`.
- **Stateful Tray Icon**: The system tray icon dynamically changes to reflect the current state (Idle, Working, Error).

## 🛠️ Tech Stack & Dependencies
- **Package Manager**: `uv`
- **AI Models**: `whisperx` (Transcriber), `transformers` + `torch` (Translator: Helsinki-NLP/NLLB)
- **UI & System**: `flet` (Settings GUI), `pystray` + `Pillow` (Tray Icon), `plyer` (OS Notifications)
- **System Interactions**: `keyboard` (Hotkey listener), `pywin32` (Clipboard parsing)
- **Utilities**: `loguru` (Thread-safe logging), `pysrt` (Subtitle parsing/writing)

## 🏗️ Architecture & Module Breakdown

The application strictly follows a decoupled, modular architecture. **AI Assistant: Please generate these as separate Python files.**

### 1. `config_ui.py` (Config & UI Module)
- Manages a `config.json` file (Whisper model size, Translator model choice, "Require Confirmation" boolean).
- Provides a `SettingsUI` class using `flet` to display a modern settings window to modify these configurations.

### 2. `monitor.py` (Clipboard & Hotkey Module)
- Runs a background thread listening for `Ctrl + Shift + T`.
- Simulates `Ctrl + C`, waits 0.15s, and reads the Windows clipboard specifically for `CF_HDROP` to extract the absolute file path.
- Triggers a callback function with the extracted path.

### 3. `tray_manager.py` (Tray & Signaling Module)
- Manages the `pystray` system tray icon.
- Provides methods to dynamically update the icon image/color: `set_idle()`, `set_working()`, `set_error()`.
- Handles OS desktop notifications via `plyer`.
- Contains a right-click menu: "Settings" (opens Flet UI) and "Quit".

### 4. `transcriber.py` (Transcription Engine)
- Class `Transcriber` wrapping `whisperx`.
- **Lazy Loading**: Loads the model only when `transcribe()` is called.
- **Keep-Alive**: Uses `threading.Timer` for a 10-minute TTL. Resets on new tasks. On timeout, deletes the model and clears CUDA cache.
- Returns aligned text segments.

### 5. `translator.py` (Translation Engine)
- Class `Translator` wrapping `transformers` (default: `Helsinki-NLP/opus-mt-en-zh`).
- Implements the exact same Lazy Loading and 10-minute Keep-Alive VRAM management as the Transcriber.
- Accepts text segments, translates them efficiently, and returns the translated text.

### 6. `main.py` (The Orchestrator)
- The entry point. Initializes all modules.
- Connects the `monitor` callback to the processing pipeline.
- **Workflow**:
  1. File path received. Checks `config.json`.
  2. If "Require Confirmation" is true, shows a native Windows Yes/No dialog (`ctypes.windll.user32.MessageBoxW`).
  3. Spawns a background `threading.Thread` for processing (to prevent blocking the tray/monitor).
  4. Updates tray state to Working.
  5. Routes the file (Video -> Transcribe+Translate | SRT -> Translate only).
  6. Saves the final `.srt` file.
  7. Updates tray state to Idle and shows a success notification.
  8. Catches exceptions, logs via `loguru`, and sets tray state to Error.

## 🤖 Note to AI Coding Assistant
When implementing this project:
1. **Concurrency**: Ensure the GUI, Tray Icon, Hotkey Monitor, and AI Processing Pipeline all run on appropriate threads without blocking the main thread.
2. **Robustness**: Implement strict `try-except` blocks around CUDA memory allocations.
3. **Step-by-Step**: Please acknowledge this architecture, and ask the user which module you should generate first, or begin generating them sequentially.
