from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .models import AppConfig


APP_NAME = "AcademicLiveTranslator"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Portable-by-default storage. Users can still override any location explicitly.
DATA_DIR = Path(os.environ.get("ALT_DATA_DIR", PROJECT_ROOT / "data")).expanduser().resolve()
MODELS_DIR = Path(os.environ.get("ALT_MODELS_DIR", PROJECT_ROOT / "models")).expanduser().resolve()
CACHE_DIR = Path(os.environ.get("ALT_CACHE_DIR", PROJECT_ROOT / "cache")).expanduser().resolve()
LOGS_DIR = Path(os.environ.get("ALT_LOGS_DIR", PROJECT_ROOT / "logs")).expanduser().resolve()
TEMP_DIR = CACHE_DIR / "temp"
HF_HOME = CACHE_DIR / "huggingface"
PIP_CACHE_DIR = CACHE_DIR / "pip"

for path in (DATA_DIR, MODELS_DIR, CACHE_DIR, LOGS_DIR, TEMP_DIR, HF_HOME, PIP_CACHE_DIR):
    path.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("HF_HUB_CACHE", str(HF_HOME / "hub"))
os.environ.setdefault("HF_XET_CACHE", str(HF_HOME / "xet"))
os.environ.setdefault("HF_ASSETS_CACHE", str(HF_HOME / "assets"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))
os.environ.setdefault("PIP_CACHE_DIR", str(PIP_CACHE_DIR))
os.environ.setdefault("TMPDIR", str(TEMP_DIR))
os.environ.setdefault("TEMP", str(TEMP_DIR))
os.environ.setdefault("TMP", str(TEMP_DIR))
try:
    sys.pycache_prefix = str(CACHE_DIR / "pycache")
except Exception:
    pass

SESSIONS_DIR = DATA_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR = DATA_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = DATA_DIR / "config.json"


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        cfg = AppConfig()
        save_config(cfg)
        return cfg
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return AppConfig.model_validate(raw)
    except Exception:
        broken = CONFIG_PATH.with_suffix(".broken.json")
        try:
            CONFIG_PATH.replace(broken)
        except Exception:
            pass
        cfg = AppConfig()
        save_config(cfg)
        return cfg


def save_config(config: AppConfig) -> None:
    CONFIG_PATH.write_text(json.dumps(config.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")


def session_assets_dir(session_id: str) -> Path:
    path = ASSETS_DIR / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path
