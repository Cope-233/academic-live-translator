# Academic Live Translator

[简体中文](./README.md) | **English**

**beta 0.4 · WebUI · portable by default**

Academic Live Translator is a local-first WebUI for real-time transcription, translation, and academic session capture. It is designed for lectures, seminars, conferences, meetings, interviews, and recorded media.

> Beta builds use `beta x.y` identifiers. Standard semantic versioning will begin with the first stable release.

## beta 0.4: Whisper/Bing fixes and one-click installation

beta 0.4 focuses on Local Faster-Whisper reliability, Bing Free translation, and a beginner-friendly Windows installation flow.

### Live pipeline fix

Live processing now follows:

```text
Audio → ASR → show and save original text immediately → translate → update the same segment
```

This means:

- Whisper text appears as soon as ASR finishes; it no longer waits for translation.
- A Bing, Microsoft Translator, or OpenAI-compatible translation failure no longer hides or discards recognized source text.
- The translated text updates the existing segment instead of creating a duplicate.
- ASR and translation failures are logged separately so the failing stage is clear.

### Bing Free fix

- Correctly extracts `translations[0].text` from the `mintrans` response.
- Uses `auto-detect` for automatic source-language detection.
- Maps Simplified Chinese to `zh-Hans` and Traditional Chinese to `zh-Hant`.
- The translation test now verifies an actual translated string.

### Better Faster-Whisper testing

The ASR test now performs a real inference pass instead of only constructing `WhisperModel`. Missing GPU runtime libraries such as `cublas64_12.dll` are therefore detected before a live session.

## Windows one-click install

### Easiest option

Double-click:

```text
install.bat
```

Or simply double-click:

```text
start_webui.bat
```

If beta 0.4 has not been initialized yet, `start_webui.bat` automatically runs the full installer first and then starts the WebUI.

The installer automatically:

1. creates `.venv/` inside the project;
2. installs Python dependencies;
3. downloads all five supported Faster-Whisper models: `tiny`, `base`, `small`, `medium`, and `large-v3-turbo`;
4. stores them under `models/faster-whisper/<model>/`;
5. detects an NVIDIA GPU on Windows and, when present, downloads a project-local CUDA 12 cuBLAS/cuDNN runtime;
6. extracts the GPU runtime into `runtime/cuda12/bin/` without changing the system-wide CUDA installation;
7. runs a real Whisper CPU/int8 inference self-test;
8. when the NVIDIA runtime is present, runs a real CUDA/float16 inference self-test.

> A full install contains five Whisper models plus the optional CUDA runtime. Expect several gigabytes of downloads and disk use. The five models alone are roughly 4 GB; reserving at least 6 GB is recommended.

The Windows CUDA runtime follows the local-library approach documented by Faster-Whisper and uses the [Purfview/whisper-standalone-win cuBLAS/cuDNN bundle](https://github.com/Purfview/whisper-standalone-win/releases/tag/libs).

## Starting the app

After installation, the recommended launcher is:

```text
start_webui.bat
```

PowerShell is also supported:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_webui.ps1
```

Default WebUI address:

```text
http://127.0.0.1:8765
```

## Portable directory layout

Application-created data and downloaded assets stay under the project directory rather than AppData:

```text
academic-live-translator/
├─ .venv/                     # project Python environment
├─ data/
│  ├─ config.json
│  ├─ sessions/
│  └─ assets/                 # recordings and screenshots
├─ models/
│  └─ faster-whisper/
│     ├─ tiny/
│     ├─ base/
│     ├─ small/
│     ├─ medium/
│     └─ large-v3-turbo/
├─ runtime/
│  └─ cuda12/
│     └─ bin/                 # project-local CUDA/cuDNN DLLs on Windows/NVIDIA
├─ cache/
│  ├─ huggingface/
│  ├─ pip/
│  ├─ downloads/
│  └─ temp/
├─ logs/
├─ app/
├─ static/
├─ install.bat
├─ install.ps1
├─ start_webui.bat
└─ start_webui.ps1
```

`.venv/`, `data/`, `models/`, `runtime/`, `cache/`, and `logs/` are ignored by Git.

## Highlights

- Real-time bilingual transcript workspace
- Local Faster-Whisper: tiny / base / small / medium / large-v3-turbo
- Bing Free, Microsoft Translator, and OpenAI-compatible translation providers
- OpenAI-compatible llama.cpp, vLLM, LM Studio, LocalAI, and similar services
- Browser microphone, tab/screen audio, and system-audio + microphone mix
- Windows WASAPI loopback and native microphone capture
- Audio/video file transcription
- Synchronized original/translation scrolling with automatic follow-to-latest
- Experimental always-on-top Document Picture-in-Picture bilingual subtitle window
- Academic glossary profiles and custom terminology
- Important / Question / Idea / Reference / Follow-up / Note markers
- Screenshot capture for slides
- Searchable Session Library with delete support
- TXT, Markdown, SRT, and JSON export

## Default providers

### ASR: Local Faster-Whisper

The default model is `base`. A beta 0.4 full install prepares all five models in advance, so switching models later does not require another model download.

CPU mode requires no CUDA. On Windows with an NVIDIA GPU, the one-click installer prepares the required runtime inside the project. Use the supplied launcher so `runtime/cuda12/bin` is added only to the application process PATH.

### Translation: Bing Free (Experimental)

Bing Free requires no API key and is useful for first-run and lightweight use. It relies on an unofficial web interface, so it remains Experimental. For long-term stable deployments, use Microsoft Translator or an OpenAI-compatible translation service.

## OpenAI-compatible providers

Example with a llama.cpp router:

```text
ASR
Mode: OpenAI Chat Completions
Base URL: http://127.0.0.1:8080/v1
Model: <ASR model id>

Translation
Mode: OpenAI Chat Completions
Base URL: http://127.0.0.1:8080/v1
Model: <translation model id>
```

Remote ASR sends WAV audio through Chat Completions `input_audio`, so the selected service must support the corresponding multimodal audio input.

## Floating Window (Experimental)

On recent desktop Chrome/Edge builds, Document Picture-in-Picture can display the live original text and translation above Zoom, WebEx, slide decks, or browser classes. The floating view is resizable, follows the newest segment automatically, and shares the same live Session as the main WebUI.

> The floating window is only a display layer. Keep the main WebUI tab open.

## Linux / macOS

You can continue to use:

```bash
chmod +x start_webui.sh
./start_webui.sh
```

Linux/macOS support browser microphone, tab/screen capture, and media-file workflows. Windows WASAPI capture and the beta 0.4 Windows CUDA bundle do not apply; GPU runtime libraries must be prepared according to the selected platform.

## Upgrading from older betas

beta 0.4 keeps portable-by-default storage. Existing `data/config.json` and Sessions remain usable.

On the first beta 0.4 start, the launcher checks for `data/.installed-beta-0.4`. If it is missing, the new full installation flow runs automatically. Older Hugging Face caches are not deleted; beta 0.4 creates explicit project-local folders for all five supported Whisper models.

## Development

```bash
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -r requirements-dev.txt
pytest
```

CI checks both Python tests and WebUI JavaScript syntax.

## License

MIT. See [LICENSE](LICENSE).
