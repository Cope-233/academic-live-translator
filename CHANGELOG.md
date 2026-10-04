# Changelog

## beta 0.1 — 2026-10-04

Current public beta.

- Portable-by-default storage: `data/`, `models/`, `cache/`, `logs/`, `.venv/` stay inside the project directory.
- Removed automatic AppData / legacy v0.2 data reuse.
- Local Faster-Whisper models download into `models/faster-whisper/`.
- Hugging Face, pip, and temporary caches are redirected into `cache/`.
- WebUI-only distribution.
- Unified Live workspace for lectures, meetings, interviews, seminars, and conferences.
- Library session deletion.
- Chinese / English interface switching.
- Unified OpenAI Chat Completions mode for remote ASR.
- Mainstream target-language list; Malay remains available as a source language.
- Synchronized scrolling between original and translation panels.
- Automatic follow-to-latest behavior with manual-scroll pause/resume.
- Compact interface-language settings UI.
- GitHub-friendly default providers: Local Faster-Whisper + Bing Free (experimental).
- OpenAI-compatible provider remains the generic integration path for llama.cpp, vLLM, LM Studio, LocalAI, and compatible services.
- Lower endpointing latency and HTTP connection reuse.

Beta builds use `beta x.y` identifiers. Semantic version numbers will begin with the first stable release.
