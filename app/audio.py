from __future__ import annotations

import io, math, shutil, struct, subprocess, tempfile, wave
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from .models import LiveConfig

def pcm16_rms(pcm: bytes) -> float:
    if not pcm: return 0.0
    count=len(pcm)//2
    if count<=0: return 0.0
    samples=struct.unpack("<"+"h"*count,pcm[:count*2])
    return math.sqrt(sum((s/32768.0)**2 for s in samples)/count)

def pcm16_to_wav_bytes(pcm: bytes, sample_rate: int=16000) -> bytes:
    out=io.BytesIO()
    with wave.open(out,"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate); wf.writeframes(pcm)
    return out.getvalue()

def wav_duration_ms(wav_bytes: bytes) -> int:
    with wave.open(io.BytesIO(wav_bytes),"rb") as wf:
        return int(wf.getnframes()/wf.getframerate()*1000) if wf.getframerate() else 0

def ensure_wav_16k_mono(raw: bytes, filename: str) -> bytes:
    suffix=Path(filename).suffix.lower()
    if suffix==".wav":
        try:
            with wave.open(io.BytesIO(raw),"rb") as wf:
                if wf.getnchannels()==1 and wf.getsampwidth()==2 and wf.getframerate()==16000: return raw
        except Exception: pass
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg: raise RuntimeError("FFmpeg is required for non-WAV media. Install FFmpeg and ensure it is on PATH.")
    with tempfile.TemporaryDirectory(prefix="alt-media-") as td:
        src=Path(td)/("input"+(suffix or ".bin")); dst=Path(td)/"output.wav"; src.write_bytes(raw)
        p=subprocess.run([ffmpeg,"-hide_banner","-loglevel","error","-y","-i",str(src),"-ac","1","-ar","16000","-c:a","pcm_s16le",str(dst)],capture_output=True,text=True)
        if p.returncode!=0: raise RuntimeError(f"FFmpeg conversion failed: {p.stderr.strip()}")
        return dst.read_bytes()

@dataclass
class EndpointResult:
    wav_bytes: bytes; duration_ms: int; start_ms: int; end_ms: int

@dataclass
class SpeechEndpointDetector:
    cfg: LiveConfig
    _pre_roll: deque[bytes]=field(default_factory=deque); _pre_roll_ms: float=0.0
    _speech_chunks: list[bytes]=field(default_factory=list); _speech_ms: float=0.0; _silence_ms: float=0.0
    _clock_ms: float=0.0; _segment_start_ms: float=0.0; in_speech: bool=False
    def feed(self, pcm: bytes):
        if not pcm: return 0.0,None
        chunk_ms=(len(pcm)//2)/self.cfg.sample_rate*1000.0; level=pcm16_rms(pcm); voice=level>=self.cfg.speech_threshold
        if not self.in_speech:
            self._pre_roll.append(pcm); self._pre_roll_ms+=chunk_ms
            while self._pre_roll and self._pre_roll_ms>self.cfg.pre_roll_ms+chunk_ms:
                old=self._pre_roll.popleft(); self._pre_roll_ms-=(len(old)//2)/self.cfg.sample_rate*1000.0
            if voice:
                self.in_speech=True; self._segment_start_ms=max(0.0,self._clock_ms-self._pre_roll_ms); self._speech_chunks.extend(self._pre_roll); self._speech_ms=self._pre_roll_ms; self._pre_roll.clear(); self._pre_roll_ms=0; self._silence_ms=0
        else:
            self._speech_chunks.append(pcm); self._speech_ms+=chunk_ms; self._silence_ms=0 if voice else self._silence_ms+chunk_ms
        self._clock_ms+=chunk_ms
        if self.in_speech and ((self._silence_ms>=self.cfg.silence_ms and self._speech_ms>=self.cfg.min_speech_ms) or self._speech_ms>=self.cfg.max_segment_ms): return level,self._finalize()
        return level,None
    def flush(self):
        if self.in_speech and self._speech_ms>=self.cfg.min_speech_ms: return self._finalize()
        self._reset(); return None
    def _finalize(self):
        pcm=b"".join(self._speech_chunks); duration=int(self._speech_ms); start=int(self._segment_start_ms); result=EndpointResult(pcm16_to_wav_bytes(pcm,self.cfg.sample_rate),duration,start,start+duration); self._reset(); return result
    def _reset(self): self.in_speech=False; self._speech_chunks.clear(); self._speech_ms=0; self._silence_ms=0

def segment_wav_bytes(wav_bytes: bytes, cfg: LiveConfig, frame_ms: int=100):
    results=[]
    with wave.open(io.BytesIO(wav_bytes),"rb") as wf:
        if wf.getnchannels()!=1 or wf.getsampwidth()!=2 or wf.getframerate()!=cfg.sample_rate: raise ValueError("Expected normalized mono 16-bit WAV")
        n=max(1,int(cfg.sample_rate*frame_ms/1000)); d=SpeechEndpointDetector(cfg)
        while True:
            pcm=wf.readframes(n)
            if not pcm: break
            _,r=d.feed(pcm)
            if r: results.append(r)
        r=d.flush()
        if r: results.append(r)
    if not results:
        duration=wav_duration_ms(wav_bytes)
        if duration: results.append(EndpointResult(wav_bytes,duration,0,duration))
    return results
