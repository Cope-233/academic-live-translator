from __future__ import annotations

import asyncio, platform, threading
from dataclasses import dataclass
import numpy as np

def _require_windows_backend():
    if platform.system() != "Windows": raise RuntimeError("Native WASAPI capture is available on Windows only. Use browser audio on this platform.")
    try: import pyaudiowpatch as pyaudio
    except Exception as exc: raise RuntimeError("PyAudioWPatch is not installed. Re-run start_webui.ps1 or pip install PyAudioWPatch.") from exc
    return pyaudio

def list_native_devices() -> dict:
    if platform.system() != "Windows": return {"supported":False,"platform":platform.system(),"system":[],"microphones":[]}
    try:
        pyaudio=_require_windows_backend(); systems=[]; microphones=[]
        with pyaudio.PyAudio() as p:
            try: default_loop=p.get_default_wasapi_loopback()
            except Exception: default_loop=None
            try: default_input=int(p.get_host_api_info_by_type(pyaudio.paWASAPI).get("defaultInputDevice",-1))
            except Exception: default_input=None
            for d in p.get_loopback_device_info_generator():
                systems.append({"index":int(d["index"]),"name":str(d["name"]),"sample_rate":int(float(d.get("defaultSampleRate",48000))),"channels":int(d.get("maxInputChannels",2)),"default":bool(default_loop and int(d["index"])==int(default_loop["index"]))})
            for d in p.get_device_info_generator():
                if bool(d.get("isLoopbackDevice")) or int(d.get("maxInputChannels",0))<=0: continue
                microphones.append({"index":int(d["index"]),"name":str(d["name"]),"sample_rate":int(float(d.get("defaultSampleRate",48000))),"channels":int(d.get("maxInputChannels",1)),"default":bool(default_input is not None and int(d["index"])==default_input)})
        return {"supported":True,"platform":"Windows","system":systems,"microphones":microphones}
    except Exception as exc:
        return {"supported":False,"platform":"Windows","system":[],"microphones":[],"error":str(exc)}

def pcm16_to_mono_16k(data:bytes,channels:int,source_rate:int,target_rate:int=16000)->bytes:
    if not data: return b""
    arr=np.frombuffer(data,dtype=np.int16)
    if channels>1:
        usable=(arr.size//channels)*channels
        if usable==0:return b""
        arr=arr[:usable].reshape(-1,channels).astype(np.float32).mean(axis=1)
    else: arr=arr.astype(np.float32)
    if arr.size==0:return b""
    if source_rate!=target_rate:
        out_len=max(1,int(round(arr.size*target_rate/source_rate))); old=np.linspace(0.0,1.0,num=arr.size,endpoint=False); new=np.linspace(0.0,1.0,num=out_len,endpoint=False); arr=np.interp(new,old,arr)
    return np.clip(arr,-32768,32767).astype(np.int16).tobytes()

@dataclass
class NativeCaptureInfo:
    device_index:int; name:str; sample_rate:int; channels:int

class NativeAudioCapture:
    def __init__(self,device_index:int,loopback:bool,loop:asyncio.AbstractEventLoop,queue:asyncio.Queue[bytes]):
        self.device_index=int(device_index); self.loopback=loopback; self.loop=loop; self.queue=queue; self._stop=threading.Event(); self._thread=None; self.error=None; self.info=None
    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._thread=threading.Thread(target=self._run,name="ALT-WASAPI",daemon=True); self._thread.start()
    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive(): self._thread.join(timeout=2.0)
    def _enqueue(self,pcm):
        if not pcm:return
        def put():
            try:self.queue.put_nowait(pcm)
            except asyncio.QueueFull:
                try:self.queue.get_nowait()
                except asyncio.QueueEmpty:pass
                try:self.queue.put_nowait(pcm)
                except asyncio.QueueFull:pass
        self.loop.call_soon_threadsafe(put)
    def _run(self):
        try:
            pyaudio=_require_windows_backend()
            with pyaudio.PyAudio() as p:
                d=p.get_device_info_by_index(self.device_index)
                if self.loopback and not bool(d.get("isLoopbackDevice")):
                    d=p.get_wasapi_loopback_analogue_by_index(self.device_index)
                rate=int(float(d.get("defaultSampleRate",48000))); channels=max(1,int(d.get("maxInputChannels",1))); self.info=NativeCaptureInfo(int(d["index"]),str(d["name"]),rate,channels); frames=max(256,int(rate*0.08))
                stream=p.open(format=pyaudio.paInt16,channels=channels,rate=rate,input=True,input_device_index=int(d["index"]),frames_per_buffer=frames)
                try:
                    while not self._stop.is_set(): self._enqueue(pcm16_to_mono_16k(stream.read(frames,exception_on_overflow=False),channels,rate,16000))
                finally:
                    try:stream.stop_stream()
                    except Exception:pass
                    stream.close()
        except Exception as exc:
            self.error=str(exc); self.loop.call_soon_threadsafe(lambda:self.queue.put_nowait(b""))
