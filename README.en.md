# Academic Live Translator

[简体中文](./README.md) | **English**

**beta01 · WebUI · portable by default**

Academic Live Translator is a local-first WebUI for real-time transcription, translation, and academic session capture. It is designed for lectures, seminars, conferences, meetings, interviews, and recorded media.

> This project is currently in beta. Pre-release builds use `betaXX` identifiers. Standard semantic version numbers will begin with the first stable release.

## Highlights

- Real-time bilingual transcript workspace
- Browser microphone, browser tab/screen audio, Windows WASAPI loopback, and media-file input
- Academic glossary profiles and custom terminology
- Important / Question / Idea / Reference / Follow-up / Note markers
- Screenshot capture for slides
- Searchable session Library with delete support
- TXT, Markdown, SRT, and JSON export
- Local Faster-Whisper default ASR
- Bing Free translation for zero-key first-run testing (experimental)
- Microsoft Translator and generic OpenAI-compatible providers
- llama.cpp, vLLM, LM Studio, LocalAI, and similar services can be connected through OpenAI-compatible endpoints

## Portable-by-default storage

The application does **not** use AppData for its own runtime data. By default everything created or downloaded by Academic Live Translator stays under the project directory:

```text
academic-live-translator/
├─ .venv/              # Python environment
├─ data/
│  ├─ config.json
│  ├─ sessions/
│  └─ assets/          # recordings and screenshots
├─ models/
│  └─ faster-whisper/  # automatically downloaded local ASR models
├─ cache/
│  ├─ huggingface/
│  ├─ pip/
│  └─ temp/
├─ logs/
├─ app/
├─ static/
└─ start_webui.ps1
```

These runtime folders are ignored by Git, so personal transcripts, recordings, screenshots, model files, and caches are not accidentally committed.

You can override storage locations with `ALT_DATA_DIR`, `ALT_MODELS_DIR`, `ALT_CACHE_DIR`, or `ALT_LOGS_DIR`.

## Requirements

- Python 3.11–3.13
- Windows 10/11 for native WASAPI loopback capture
- Chrome / Edge recommended for browser audio capture
- FFmpeg recommended for media conversion and FLAC recording
- GPU is optional. The default Faster-Whisper `base` model can run on CPU.

## Windows quick start

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_webui.ps1
```

The script will:

1. create `.venv/` inside the project;
2. install dependencies using the project-local pip cache;
3. download the default Faster-Whisper model into `models/faster-whisper/` on first run;
4. start the WebUI at `http://127.0.0.1:8765`.

The launcher works with both a normal Python installation and Conda as long as `python` is available in PowerShell.

## Linux / macOS quick start

```bash
chmod +x start_webui.sh
./start_webui.sh
```

Native Windows system-audio capture is unavailable on Linux/macOS, but browser microphone/tab/screen capture and media-file workflows remain available.

## Default providers

### ASR: Local Faster-Whisper

Default model: `base`. It is downloaded automatically on first run. You can switch to `tiny`, `small`, `medium`, or `large-v3-turbo` in Settings.

### Translation: Bing Free (experimental)

This option requires no API key and is intended to make first-run testing easy. It relies on an unofficial web interface and may break if Bing changes its frontend. For reliable long-term use, choose Microsoft Translator or an OpenAI-compatible service.

## OpenAI-compatible providers

Both ASR and translation can use compatible APIs. For example, a llama.cpp router hosting multiple models can use the same base URL for both providers:

```text
ASR
Base URL: http://127.0.0.1:8080/v1
Model: <ASR model id>
Mode: OpenAI /audio/transcriptions or Chat + input_audio

Translation
Base URL: http://127.0.0.1:8080/v1
Model: <translation model id>
Mode: OpenAI Chat Completions
```

No dedicated llama.cpp mode is required.

## Live input options

- Browser microphone
- Browser tab / screen audio
- Browser system audio + microphone mix
- Windows system audio via WASAPI loopback
- Windows native microphone
- Audio / video files

For online classes played by Chrome, Zoom, Teams, VLC, or similar applications on Windows, WASAPI loopback is usually the cleanest source because it captures the digital playback stream directly.

## Academic workflow

During a live session you can:

- see original text and translation side-by-side;
- add terminology profiles;
- mark content as Important, Question, Idea, Reference, Follow-up, or Note;
- capture the current screen as a slide snapshot;
- save session audio;
- export the session to Markdown, TXT, SRT, or JSON.

## Migration from older local builds

`beta01` intentionally **does not automatically reuse** v0.1/v0.2/v0.3 AppData folders. This prevents surprising cross-version records and hidden C-drive usage.

If you want to keep older sessions, copy the desired session JSON files and matching assets manually into the new portable `data/` directory after making a backup.

## Development

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements-dev.txt
# Linux/macOS: .venv/bin/python -m pip install -r requirements-dev.txt
pytest
```

## License

MIT. See [LICENSE](LICENSE).
