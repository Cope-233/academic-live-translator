from app import __version__
from app.models import AppConfig
from app.config import CACHE_DIR, DATA_DIR, MODELS_DIR, PROJECT_ROOT

def test_version(): assert __version__ == "beta01"
def test_defaults():
    cfg=AppConfig(); assert cfg.asr.mode=="local_whisper"; assert cfg.asr.model=="base"; assert cfg.translation.mode=="bing_web"
def test_portable_paths():
    assert DATA_DIR==PROJECT_ROOT/"data"; assert MODELS_DIR==PROJECT_ROOT/"models"; assert CACHE_DIR==PROJECT_ROOT/"cache"
