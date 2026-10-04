# Changelog

## beta 0.2 — 2026-10-04

Floating-window beta focused on single-screen academic use.

- Added an **Experimental Floating Window** based on Document Picture-in-Picture for supported desktop Chromium browsers.
- Floating window can remain above Zoom, WebEx, browser classes, slide decks, and other desktop applications.
- Two-column layout keeps original text and translation aligned by segment with one shared scrollbar.
- Floating subtitles auto-follow the newest segment and pause follow mode when the user scrolls upward.
- Added `Back to WebUI` and close controls inside the floating window.
- Added configurable floating-window default width, height, and subtitle font size.
- Manual floating-window resizing automatically persists the new width and height to the portable config.
- Standard WebUI remains unchanged as the main capture, ASR, translation, notes, and session-management workspace.
- Updated Chinese / English documentation for browser support and usage limitations.

## beta 0.1 — 2026-10-04

First public beta.

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
