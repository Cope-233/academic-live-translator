"""First-run preparation for the zero-config WebUI defaults."""
from __future__ import annotations

from .config import DATA_DIR, load_config
from .providers import prepare_local_whisper

MARKER = DATA_DIR / ".defaults-prepared-beta-0.1"

def main() -> None:
    cfg = load_config()
    if cfg.asr.mode != "local_whisper":
        print("[setup] External ASR configured; local Whisper download skipped.")
        return
    if MARKER.exists() and MARKER.read_text(encoding="utf-8").strip() == cfg.asr.model:
        print("[setup] Default local model already prepared.")
        return
    print(f"[setup] First run: downloading/preparing Faster-Whisper model '{cfg.asr.model}'.")
    print("[setup] This happens once; subsequent starts use the local cache.")
    prepare_local_whisper(cfg.asr)
    MARKER.write_text(cfg.asr.model, encoding="utf-8")
    print("[setup] Local Whisper is ready.")

if __name__ == "__main__": main()
