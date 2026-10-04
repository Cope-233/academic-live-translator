# Changelog

## beta01 — 2026-10-04

First public beta.

- Portable-by-default storage: `data/`, `models/`, `cache/`, `logs/`, `.venv/` stay inside the project directory.
- Removed automatic AppData / legacy v0.2 data reuse.
- Local Faster-Whisper models download into `models/faster-whisper/`.
- Hugging Face, pip, and temporary caches are redirected into `cache/`.
- WebUI-only distribution.
- Unified Live workspace for lectures, meetings, interviews, seminars, and conferences.
- Library session deletion.
- GitHub-friendly default providers: Local Faster-Whisper + Bing Free (experimental).
- OpenAI-compatible provider remains the generic integration path for llama.cpp, vLLM, LM Studio, LocalAI, and compatible services.
- Lower endpointing latency and HTTP connection reuse.

Pre-release builds use `betaXX` identifiers. Semantic version numbers will begin with the first stable release.
