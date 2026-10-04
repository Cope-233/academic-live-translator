from app import __version__
from app.models import AppConfig
from app.config import CACHE_DIR, DATA_DIR, MODELS_DIR, PROJECT_ROOT, _migrate_config


def test_version():
    assert __version__ == "beta 0.2"


def test_defaults():
    cfg = AppConfig()
    assert cfg.interface.language == "zh-CN"
    assert cfg.interface.floating_window_width == 960
    assert cfg.interface.floating_window_height == 420
    assert cfg.interface.floating_window_font_size == 18
    assert cfg.asr.mode == "local_whisper"
    assert cfg.asr.model == "base"
    assert cfg.translation.mode == "bing_web"
    assert cfg.academic.target_language == "Chinese"


def test_floating_window_bounds():
    cfg = AppConfig(interface={"language":"zh-CN","floating_window_width":420,"floating_window_height":220,"floating_window_font_size":12})
    assert cfg.interface.floating_window_width == 420
    assert cfg.interface.floating_window_height == 220
    assert cfg.interface.floating_window_font_size == 12


def test_portable_paths():
    assert DATA_DIR == PROJECT_ROOT / "data"
    assert MODELS_DIR == PROJECT_ROOT / "models"
    assert CACHE_DIR == PROJECT_ROOT / "cache"


def test_legacy_asr_migration():
    raw = {
        "asr": {"mode": "openai_transcriptions", "endpoint": "http://127.0.0.1:8080/v1/audio/transcriptions"},
        "academic": {"target_language": "Malay"},
    }
    migrated = _migrate_config(raw)
    assert migrated["asr"]["mode"] == "openai_chat"
    assert migrated["asr"]["endpoint"] is None
    assert migrated["academic"]["target_language"] == "Chinese"
    assert migrated["interface"]["language"] == "zh-CN"
