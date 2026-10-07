from __future__ import annotations

from copy import deepcopy
import json
import os
import sys
from pathlib import Path

from .models import AppConfig, ProviderProfiles


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

_ASR_PROFILE_MODES = ("local_whisper", "openai_chat")
_TRANSLATION_PROFILE_MODES = ("bing_web", "azure_translator", "openai_chat")


def _merged_profile(default: dict, candidate: object, mode: str) -> dict:
    profile = deepcopy(default)
    if isinstance(candidate, dict):
        profile.update(candidate)
    profile["mode"] = mode
    return profile


def _migrate_config(raw: dict) -> dict:
    """Normalize older beta config values and preserve provider-specific settings."""
    raw = deepcopy(raw)

    # Legacy ASR modes used before the Chat Completions path was unified.
    asr = raw.get("asr")
    if isinstance(asr, dict) and asr.get("mode") in {"openai_transcriptions", "openai_chat_audio"}:
        asr["mode"] = "openai_chat"
        endpoint = asr.get("endpoint")
        if not endpoint or str(endpoint).rstrip("/").endswith("audio/transcriptions"):
            asr["endpoint"] = None

    academic = raw.get("academic")
    if isinstance(academic, dict) and academic.get("target_language") == "Malay":
        academic["target_language"] = "Chinese"
    raw.setdefault("interface", {"language": "zh-CN"})

    # beta 0.7: provider profiles are canonical. Existing beta <=0.6 configs are
    # migrated by placing their current ASR/translation settings into the
    # corresponding profile. Once profiles exist, the active profile controls
    # the legacy `asr` / `translation` mirrors used by the runtime.
    defaults = ProviderProfiles().model_dump()
    existing = raw.get("providers")
    had_profiles = isinstance(existing, dict)
    providers = deepcopy(existing) if had_profiles else {}

    current_asr = raw.get("asr") if isinstance(raw.get("asr"), dict) else {}
    current_translation = raw.get("translation") if isinstance(raw.get("translation"), dict) else {}

    active_asr = providers.get("active_asr")
    if active_asr not in _ASR_PROFILE_MODES:
        active_asr = current_asr.get("mode") if current_asr.get("mode") in _ASR_PROFILE_MODES else "local_whisper"

    active_translation = providers.get("active_translation")
    if active_translation not in _TRANSLATION_PROFILE_MODES:
        active_translation = (
            current_translation.get("mode")
            if current_translation.get("mode") in _TRANSLATION_PROFILE_MODES
            else "bing_web"
        )

    raw_asr_profiles = providers.get("asr") if isinstance(providers.get("asr"), dict) else {}
    raw_translation_profiles = (
        providers.get("translation") if isinstance(providers.get("translation"), dict) else {}
    )

    asr_profiles: dict[str, dict] = {}
    for mode in _ASR_PROFILE_MODES:
        candidate = raw_asr_profiles.get(mode)
        if not had_profiles and current_asr.get("mode") == mode:
            candidate = current_asr
        asr_profiles[mode] = _merged_profile(defaults["asr"][mode], candidate, mode)

    translation_profiles: dict[str, dict] = {}
    for mode in _TRANSLATION_PROFILE_MODES:
        candidate = raw_translation_profiles.get(mode)
        if not had_profiles and current_translation.get("mode") == mode:
            candidate = current_translation
        translation_profiles[mode] = _merged_profile(defaults["translation"][mode], candidate, mode)

    raw["providers"] = {
        "active_asr": active_asr,
        "active_translation": active_translation,
        "asr": asr_profiles,
        "translation": translation_profiles,
    }
    raw["asr"] = deepcopy(asr_profiles[active_asr])
    raw["translation"] = deepcopy(translation_profiles[active_translation])
    return raw


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        cfg = AppConfig()
        save_config(cfg)
        return cfg
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cfg = AppConfig.model_validate(_migrate_config(raw))
        save_config(cfg)
        return cfg
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
    # Normalize before writing so `providers` remains the source of truth and
    # the runtime mirrors always point at the selected profiles.
    raw = _migrate_config(config.model_dump())
    CONFIG_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def session_assets_dir(session_id: str) -> Path:
    path = ASSETS_DIR / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path
