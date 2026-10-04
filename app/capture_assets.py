from __future__ import annotations

import time
from pathlib import Path
from .config import session_assets_dir

def capture_screen_png(session_id: str, monitor: int=1) -> tuple[str,int]:
    try:
        import mss, mss.tools
    except Exception as exc:
        raise RuntimeError("Screen capture dependency 'mss' is not installed") from exc
    out_dir = session_assets_dir(session_id) / "slides"
    out_dir.mkdir(parents=True,exist_ok=True)
    stamp=int(time.time()*1000); filename=f"slide-{stamp}.png"; path=out_dir/filename
    with mss.mss() as sct:
        monitors=sct.monitors
        if len(monitors)<=1: raise RuntimeError("No display monitor is available")
        index=monitor if 1<=monitor<len(monitors) else 1
        shot=sct.grab(monitors[index]); mss.tools.to_png(shot.rgb,shot.size,output=str(path))
    return str(Path("slides")/filename),stamp
