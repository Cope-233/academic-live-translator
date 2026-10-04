from __future__ import annotations

import asyncio
import platform
import threading
from dataclasses import dataclass

import numpy as np


def _require_windows_backend():
    if platform.system() != "Windows":
        raise RuntimeError("Native WASAPI capture is available on Windows only. Use browser audio on this platform.")
    try:
        import pyaudiowpatch as pyaudio
    except Exception as exc:
        raise RuntimeError("PyAudioWPatch is not installed. Re-run start_webui.ps1 or pip install PyAudioWPatch.") from exc
    return pyaudio


def _unique_ints(values):
    out = []
    for value in values:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number > 0 and number not in out:
            out.append(number)
    return out


def _capture_candidates(device: dict, loopback: bool) -> list[tuple[int, int]]:
    default_rate = int(round(float(device.get("defaultSampleRate", 48000))))
    max_channels = max(1, int(device.get("maxInputChannels", 1)))

    rates = _unique_ints([default_rate, 48000, 44100, 32000, 24000, 16000])
    if loopback:
        channels = _unique_ints([min(2, max_channels), max_channels, 1])
    else:
        # Speech recognition only needs mono. USB microphones often advertise
        # more channels than their shared-mode WASAPI endpoint will open with.
        channels = _unique_ints([1, min(2, max_channels), max_channels])

    return [(rate, channel_count) for rate in rates for channel_count in channels]


def list_native_devices() -> dict:
    if platform.system() != "Windows":
        return {"supported": False, "platform": platform.system(), "system": [], "microphones": []}

    try:
        pyaudio = _require_windows_backend()
        systems = []
        microphones = []

        with pyaudio.PyAudio() as p:
            wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            wasapi_index = int(wasapi.get("index", -1))
            default_input = int(wasapi.get("defaultInputDevice", -1))

            try:
                default_loop = p.get_default_wasapi_loopback()
            except Exception:
                default_loop = None

            for d in p.get_loopback_device_info_generator():
                if int(d.get("hostApi", wasapi_index)) != wasapi_index:
                    continue
                systems.append(
                    {
                        "index": int(d["index"]),
                        "name": str(d["name"]),
                        "sample_rate": int(round(float(d.get("defaultSampleRate", 48000)))),
                        "channels": int(d.get("maxInputChannels", 2)),
                        "default": bool(default_loop and int(d["index"]) == int(default_loop["index"])),
                        "host_api": "WASAPI",
                    }
                )

            for d in p.get_device_info_generator():
                if int(d.get("hostApi", -1)) != wasapi_index:
                    continue
                if bool(d.get("isLoopbackDevice")) or int(d.get("maxInputChannels", 0)) <= 0:
                    continue
                microphones.append(
                    {
                        "index": int(d["index"]),
                        "name": str(d["name"]),
                        "sample_rate": int(round(float(d.get("defaultSampleRate", 48000)))),
                        "channels": int(d.get("maxInputChannels", 1)),
                        "default": bool(int(d["index"]) == default_input),
                        "host_api": "WASAPI",
                    }
                )

        systems.sort(key=lambda item: (not item["default"], item["name"].lower()))
        microphones.sort(key=lambda item: (not item["default"], item["name"].lower()))
        return {"supported": True, "platform": "Windows", "system": systems, "microphones": microphones}
    except Exception as exc:
        return {
            "supported": False,
            "platform": "Windows",
            "system": [],
            "microphones": [],
            "error": str(exc),
        }


def pcm16_to_mono_16k(data: bytes, channels: int, source_rate: int, target_rate: int = 16000) -> bytes:
    if not data:
        return b""

    arr = np.frombuffer(data, dtype=np.int16)
    if channels > 1:
        usable = (arr.size // channels) * channels
        if usable == 0:
            return b""
        arr = arr[:usable].reshape(-1, channels).astype(np.float32).mean(axis=1)
    else:
        arr = arr.astype(np.float32)

    if arr.size == 0:
        return b""

    if source_rate != target_rate:
        out_len = max(1, int(round(arr.size * target_rate / source_rate)))
        old = np.linspace(0.0, 1.0, num=arr.size, endpoint=False)
        new = np.linspace(0.0, 1.0, num=out_len, endpoint=False)
        arr = np.interp(new, old, arr)

    return np.clip(arr, -32768, 32767).astype(np.int16).tobytes()


@dataclass
class NativeCaptureInfo:
    device_index: int
    name: str
    sample_rate: int
    channels: int


class NativeAudioCapture:
    def __init__(
        self,
        device_index: int,
        loopback: bool,
        loop: asyncio.AbstractEventLoop,
        queue: asyncio.Queue[bytes],
    ):
        self.device_index = int(device_index)
        self.loopback = loopback
        self.loop = loop
        self.queue = queue
        self._stop = threading.Event()
        self._ready_event = threading.Event()
        self._thread = None
        self.error = None
        self.info = None

    def wait_until_ready(self, timeout: float = 5.0):
        if not self._ready_event.wait(timeout):
            raise TimeoutError(f"Timed out opening WASAPI input device {self.device_index}.")
        if self.error:
            raise RuntimeError(self.error)
        return self.info

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="ALT-WASAPI", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _enqueue(self, pcm):
        if not pcm:
            return

        def put():
            try:
                self.queue.put_nowait(pcm)
            except asyncio.QueueFull:
                try:
                    self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    self.queue.put_nowait(pcm)
                except asyncio.QueueFull:
                    pass

        self.loop.call_soon_threadsafe(put)

    def _signal_error(self):
        def put_error():
            try:
                self.queue.put_nowait(b"")
            except asyncio.QueueFull:
                try:
                    self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    self.queue.put_nowait(b"")
                except asyncio.QueueFull:
                    pass

        self.loop.call_soon_threadsafe(put_error)

    def _open_stream(self, p, pyaudio, device):
        last_error = None
        attempted = []

        for rate, channels in _capture_candidates(device, self.loopback):
            attempted.append(f"{rate}Hz/{channels}ch")
            try:
                frames = max(256, int(rate * 0.08))
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    input_device_index=int(device["index"]),
                    frames_per_buffer=frames,
                )
                return stream, rate, channels, frames
            except Exception as exc:
                last_error = exc

        details = ", ".join(attempted)
        raise RuntimeError(
            f"Unable to open WASAPI input '{device.get('name', self.device_index)}'. "
            f"Tried {details}. Last error: {last_error}"
        )

    def _run(self):
        try:
            pyaudio = _require_windows_backend()

            with pyaudio.PyAudio() as p:
                d = p.get_device_info_by_index(self.device_index)
                if self.loopback and not bool(d.get("isLoopbackDevice")):
                    d = p.get_wasapi_loopback_analogue_by_index(self.device_index)

                stream, rate, channels, frames = self._open_stream(p, pyaudio, d)
                self.info = NativeCaptureInfo(
                    int(d["index"]),
                    str(d["name"]),
                    rate,
                    channels,
                )
                self._ready_event.set()

                try:
                    while not self._stop.is_set():
                        raw = stream.read(frames, exception_on_overflow=False)
                        self._enqueue(pcm16_to_mono_16k(raw, channels, rate, 16000))
                finally:
                    try:
                        stream.stop_stream()
                    except Exception:
                        pass
                    stream.close()
        except Exception as exc:
            self.error = str(exc)
            self._ready_event.set()
            self._signal_error()
