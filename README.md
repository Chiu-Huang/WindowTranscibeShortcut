Use pydantics-settings, env to store the API for deepl 
So basically build transcription service, and then if output is not Chinese, stack a deepl translate on top, and then output Chinese. 
and have some presets , by default eng to Chinese 
  英文 → 中文字幕
  日文 → 中文字幕
  中文 → 中文字幕

should be quite simple from now, a simple bat script opening, and then dragging the video to bat to trigger the main. 

Try modular approach and minimistic, loguru for logging, if error, prompt and show the error log as well as logging it. 




├─ pyproject.toml
├─ README.md
├─ .python-version
├─ src/
│  └─ subtool/
│     ├─ __init__.py
│     ├─ cli.py
│     ├─ config.py
│     ├─ pipeline.py
│     ├─ io_utils.py
│     ├─ naming.py
│     ├─ subtitle_formats.py
│     ├─ asr/
│     │  ├─ __init__.py
│     │  ├─ base.py
│     │  └─ whisperx_backend.py
│     ├─ translators/
│     │  ├─ __init__.py
│     │  ├─ base.py
│     │  ├─ deepl_backend.py
│     │  ├─ llm_backend.py
│     ├─ video/
│     │  ├─ __init__.py
│     │  ├─ mux.py
│     │  └─ burn.py
│     └─ presets/
│        ├─ __init__.py
│        └─ profiles.py
├─ scripts/
│  ├─ transcribe_zh.bat
│  ├─ en_to_zh.bat
│  ├─ ja_to_zh.bat
│  └─ mux_softsub.bat
└─ tests/
