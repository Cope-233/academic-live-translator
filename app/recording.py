from __future__ import annotations
import shutil, subprocess, time, wave
from pathlib import Path
from .config import session_assets_dir

class SessionAudioRecorder:
    def __init__(self,session_id:str,sample_rate:int=16000,fmt:str='flac'):
        self.sample_rate=sample_rate; self.fmt=fmt; self.closed=False; self._dir=session_assets_dir(session_id); stamp=time.strftime('%Y%m%d-%H%M%S'); self._wav=self._dir/f'recording-{stamp}.wav'; self._wf=wave.open(str(self._wav),'wb'); self._wf.setnchannels(1); self._wf.setsampwidth(2); self._wf.setframerate(sample_rate)
    def write(self,pcm:bytes):
        if not self.closed and pcm: self._wf.writeframes(pcm)
    def close(self):
        if self.closed: return None
        self.closed=True; self._wf.close()
        if self.fmt!='flac': return self._wav.name
        ffmpeg=shutil.which('ffmpeg')
        if not ffmpeg: return self._wav.name
        dst=self._wav.with_suffix('.flac'); p=subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-i',str(self._wav),str(dst)],capture_output=True,text=True)
        if p.returncode==0: self._wav.unlink(missing_ok=True); return dst.name
        return self._wav.name
