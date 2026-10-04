import subprocess

import pytest

from app import install_assets
from app import __version__
from app.models import AppConfig
from app.config import CACHE_DIR, DATA_DIR, MODELS_DIR, PROJECT_ROOT, _migrate_config
from app.native_capture import NativeAudioCapture, NativeCaptureInfo, _capture_candidates
from app.providers import _bing_lang, _parse_bing_result


def test_version():
    assert __version__ == "beta 0.5"


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


def test_native_microphone_prefers_mono_wasapi_format():
    device = {"defaultSampleRate": 48000, "maxInputChannels": 2}
    assert _capture_candidates(device, False)[0] == (48000, 1)


def test_native_loopback_prefers_stereo_wasapi_format():
    device = {"defaultSampleRate": 48000, "maxInputChannels": 2}
    assert _capture_candidates(device, True)[0] == (48000, 2)


def test_native_capture_waits_for_device_open():
    capture = NativeAudioCapture(17, True, None, None)
    capture.info = NativeCaptureInfo(17, "Loopback", 48000, 2)
    capture._ready_event.set()
    assert capture.wait_until_ready(timeout=0.01) is capture.info


def test_native_capture_reports_device_open_error():
    capture = NativeAudioCapture(17, True, None, None)
    capture.error = "device busy"
    capture._ready_event.set()
    with pytest.raises(RuntimeError, match="device busy"):
        capture.wait_until_ready(timeout=0.01)


def test_bing_language_mapping():
    assert _bing_lang("auto", source=True) == "auto-detect"
    assert _bing_lang("Chinese") == "zh-Hans"
    assert _bing_lang("zh-tw") == "zh-Hant"


def test_bing_response_parser():
    payload = {"translations": [{"text": "你好，这是一个测试。", "to": "zh-Hans"}]}
    assert _parse_bing_result(payload) == "你好，这是一个测试。"


def test_cuda_archive_uses_windows_tar(monkeypatch, tmp_path):
    windows_dir = tmp_path / "Windows"
    tar = windows_dir / "System32" / "tar.exe"
    tar.parent.mkdir(parents=True)
    tar.touch()
    monkeypatch.setattr(install_assets.sys, "platform", "win32")
    monkeypatch.setenv("WINDIR", str(windows_dir))
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(install_assets.subprocess, "run", fake_run)
    archive = tmp_path / "runtime.7z"
    destination = tmp_path / "extracted"
    install_assets._extract_cuda_archive(archive, destination)

    assert calls[0][0] == [str(tar), "-xf", str(archive), "-C", str(destination)]


def test_cuda_archive_extraction_failure_is_reported(monkeypatch, tmp_path):
    windows_dir = tmp_path / "Windows"
    tar = windows_dir / "System32" / "tar.exe"
    tar.parent.mkdir(parents=True)
    tar.touch()
    monkeypatch.setattr(install_assets.sys, "platform", "win32")
    monkeypatch.setenv("WINDIR", str(windows_dir))
    monkeypatch.setattr(
        install_assets.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 2, "", "archive error"),
    )

    with pytest.raises(RuntimeError, match="archive error"):
        install_assets._extract_cuda_archive(tmp_path / "runtime.7z", tmp_path / "extracted")


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
