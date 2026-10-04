"""Portable first-run installer for Academic Live Translator beta 0.4.

Downloads the five supported Faster-Whisper models into project-local folders and,
on Windows with an NVIDIA GPU, prepares the CUDA 12 cuBLAS/cuDNN runtime under
runtime/cuda12/bin. No system CUDA Toolkit installation or global PATH change is
required when the supplied launcher is used.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from .config import CACHE_DIR, DATA_DIR, MODELS_DIR, PROJECT_ROOT

WHISPER_MODELS = ("tiny", "base", "small", "medium", "large-v3-turbo")
CUDA_RUNTIME_URL = (
    "https://github.com/Purfview/whisper-standalone-win/releases/download/libs/"
    "cuBLAS.and.cuDNN_CUDA12_win_v3.7z"
)
RUNTIME_DIR = PROJECT_ROOT / "runtime"
CUDA_BIN = RUNTIME_DIR / "cuda12" / "bin"
INSTALL_MARKER = DATA_DIR / ".installed-beta-0.4"
_DLL_HANDLES: list[object] = []


def _has_nvidia_gpu() -> bool:
    if sys.platform != "win32":
        return False
    exe = shutil.which("nvidia-smi")
    if not exe:
        return False
    try:
        result = subprocess.run([exe, "-L"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0 and "GPU" in result.stdout
    except Exception:
        return False


def _progress(blocks: int, block_size: int, total: int) -> None:
    if total <= 0:
        return
    current = min(total, blocks * block_size)
    percent = current * 100 / total
    print(f"\r[setup] CUDA runtime download: {percent:5.1f}%", end="", flush=True)
    if current >= total:
        print()


def _activate_cuda_runtime() -> None:
    if sys.platform != "win32" or not CUDA_BIN.exists():
        return
    os.environ["PATH"] = str(CUDA_BIN) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        _DLL_HANDLES.append(os.add_dll_directory(str(CUDA_BIN)))


def download_whisper_models() -> None:
    from faster_whisper.utils import download_model

    root = MODELS_DIR / "faster-whisper"
    root.mkdir(parents=True, exist_ok=True)
    hf_cache = CACHE_DIR / "huggingface"
    for name in WHISPER_MODELS:
        destination = root / name
        if (destination / "model.bin").exists():
            print(f"[setup] Whisper {name}: already installed")
            continue
        destination.mkdir(parents=True, exist_ok=True)
        print(f"[setup] Whisper {name}: downloading to {destination}")
        download_model(name, output_dir=str(destination), cache_dir=str(hf_cache))
        if not (destination / "model.bin").exists():
            raise RuntimeError(f"Whisper model download incomplete: {name}")
        print(f"[setup] Whisper {name}: ready")


def download_cuda_runtime() -> bool:
    if sys.platform != "win32":
        print("[setup] CUDA runtime: skipped (Windows-only portable package)")
        return False
    if not _has_nvidia_gpu():
        print("[setup] CUDA runtime: NVIDIA GPU not detected; CPU runtime is ready via CTranslate2")
        return False
    required = (CUDA_BIN / "cublas64_12.dll", CUDA_BIN / "cudnn64_9.dll")
    if all(path.exists() for path in required):
        print("[setup] CUDA 12 cuBLAS/cuDNN runtime: already installed")
        _activate_cuda_runtime()
        return True

    import py7zr

    downloads = CACHE_DIR / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / "cuBLAS.and.cuDNN_CUDA12_win_v3.7z"
    if not archive.exists():
        print("[setup] NVIDIA GPU detected; downloading portable CUDA 12 cuBLAS/cuDNN runtime...")
        urllib.request.urlretrieve(CUDA_RUNTIME_URL, archive, reporthook=_progress)

    CUDA_BIN.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="alt-cuda-", dir=str(CACHE_DIR / "temp")) as temp_dir:
        temp = Path(temp_dir)
        print("[setup] Extracting portable CUDA runtime...")
        with py7zr.SevenZipFile(archive, mode="r") as seven:
            seven.extractall(path=temp)
        dlls = list(temp.rglob("*.dll"))
        if not dlls:
            raise RuntimeError("CUDA runtime archive contained no DLL files")
        for source in dlls:
            shutil.copy2(source, CUDA_BIN / source.name)

    (CUDA_BIN.parent / "SOURCE.txt").write_text(
        "Faster-Whisper Windows CUDA runtime bundle\n"
        f"Source: {CUDA_RUNTIME_URL}\n",
        encoding="utf-8",
    )
    _activate_cuda_runtime()
    if not all(path.exists() for path in required):
        raise RuntimeError("Portable CUDA runtime extraction is incomplete")
    print(f"[setup] CUDA runtime: ready in {CUDA_BIN}")
    return True


def _consume(generator) -> None:
    list(generator)


def self_test(cuda_installed: bool) -> None:
    import numpy as np
    from faster_whisper import WhisperModel

    tiny = MODELS_DIR / "faster-whisper" / "tiny"
    silence = np.zeros(16000, dtype=np.float32)

    print("[setup] Self-test: Whisper CPU / int8 ...")
    cpu = WhisperModel(str(tiny), device="cpu", compute_type="int8")
    segments, _ = cpu.transcribe(silence, language="en", beam_size=1, best_of=1)
    _consume(segments)
    del cpu
    print("[setup] Self-test: Whisper CPU OK")

    if cuda_installed:
        print("[setup] Self-test: Whisper CUDA / float16 ...")
        try:
            gpu = WhisperModel(str(tiny), device="cuda", compute_type="float16")
            segments, _ = gpu.transcribe(silence, language="en", beam_size=1, best_of=1)
            _consume(segments)
            del gpu
            print("[setup] Self-test: Whisper CUDA OK")
        except Exception as exc:
            print(f"[setup] WARNING: CUDA self-test failed; CPU mode remains available: {exc}")


def main() -> None:
    (CACHE_DIR / "temp").mkdir(parents=True, exist_ok=True)
    print("[setup] Academic Live Translator beta 0.4 portable assets")
    print("[setup] CPU runtime is provided by the installed CTranslate2/faster-whisper package.")
    download_whisper_models()
    cuda_installed = download_cuda_runtime()
    self_test(cuda_installed)
    INSTALL_MARKER.write_text("beta 0.4\n", encoding="utf-8")
    print("[setup] Portable installation complete.")


if __name__ == "__main__":
    main()
