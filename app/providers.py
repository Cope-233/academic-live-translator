from __future__ import annotations

import asyncio
import base64
import io
import os
import re
import sys
import threading

import httpx

from .config import MODELS_DIR, PROJECT_ROOT
from .models import AcademicConfig, ProviderConfig

_ASR_PREFIX_RE = re.compile(r"^\s*language\s+[^<\r\n]+<asr_text>\s*", re.IGNORECASE)
_ASR_TOKEN_RE = re.compile(r"</?asr_text>|<\|[^>]+\|>", re.IGNORECASE)
_HTTP_CLIENT: httpx.AsyncClient | None = None
_WHISPER_MODELS: dict[tuple[str, str, str], object] = {}
_WHISPER_LOCK = threading.Lock()
_WHISPER_INFER_LOCK = threading.Lock()
_CUDA_DLL_HANDLE = None


def _enable_project_cuda_runtime() -> None:
    global _CUDA_DLL_HANDLE
    if sys.platform != "win32":
        return
    runtime_dir = PROJECT_ROOT / "runtime" / "cuda12" / "bin"
    if not runtime_dir.is_dir():
        return
    runtime_path = str(runtime_dir)
    os.environ["PATH"] = runtime_path + os.pathsep + os.environ.get("PATH", "")
    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory:
        try:
            _CUDA_DLL_HANDLE = add_dll_directory(runtime_path)
        except OSError:
            _CUDA_DLL_HANDLE = None


_enable_project_cuda_runtime()

LANG_CODES = {"auto":"auto","english":"en","en":"en","chinese":"zh","中文":"zh","zh":"zh","malay":"ms","ms":"ms","japanese":"ja","ja":"ja","korean":"ko","ko":"ko","french":"fr","fr":"fr","german":"de","de":"de","spanish":"es","es":"es","italian":"it","it":"it","portuguese":"pt","pt":"pt","russian":"ru","ru":"ru","arabic":"ar","ar":"ar","thai":"th","th":"th","vietnamese":"vi","vi":"vi","indonesian":"id","id":"id","hindi":"hi","hi":"hi"}

def clean_asr_text(text: str) -> str:
    text = _ASR_PREFIX_RE.sub("", text or "")
    text = _ASR_TOKEN_RE.sub("", text)
    return text.strip()

def normalize_base_url(url: str) -> str:
    return url.rstrip("/")

def auth_headers(cfg: ProviderConfig) -> dict[str, str]:
    headers = {"Accept":"application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    return headers

def lang_code(value: str | None, fallback: str="auto") -> str:
    if not value:
        return fallback
    return LANG_CODES.get(value.strip().lower(), value.strip().lower())

async def http_client() -> httpx.AsyncClient:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None or _HTTP_CLIENT.is_closed:
        _HTTP_CLIENT = httpx.AsyncClient(limits=httpx.Limits(max_connections=20,max_keepalive_connections=10))
    return _HTTP_CLIENT

async def close_http_client() -> None:
    global _HTTP_CLIENT
    if _HTTP_CLIENT and not _HTTP_CLIENT.is_closed:
        await _HTTP_CLIENT.aclose()
    _HTTP_CLIENT = None

def _whisper_device(cfg: ProviderConfig) -> tuple[str,str]:
    device, compute = cfg.device, cfg.compute_type
    if device == "auto":
        try:
            import ctranslate2
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:
            device = "cpu"
    if compute == "auto":
        compute = "float16" if device == "cuda" else "int8"
    return device, compute

def _local_whisper_path(model_name: str):
    direct = MODELS_DIR / "faster-whisper" / model_name
    return direct if (direct / "model.bin").exists() else None

def get_local_whisper(cfg: ProviderConfig):
    from faster_whisper import WhisperModel
    device, compute = _whisper_device(cfg)
    key = (cfg.model, device, compute)
    with _WHISPER_LOCK:
        if key in _WHISPER_MODELS:
            return _WHISPER_MODELS[key]
        local_path = _local_whisper_path(cfg.model)
        model_ref = str(local_path) if local_path else cfg.model
        kwargs = {"device":device,"compute_type":compute}
        if local_path is None:
            kwargs["download_root"] = str(MODELS_DIR / "faster-whisper")
        try:
            model = WhisperModel(model_ref, **kwargs)
        except Exception:
            if device == "cpu":
                raise
            fallback = {"device":"cpu","compute_type":"int8"}
            if local_path is None:
                fallback["download_root"] = str(MODELS_DIR / "faster-whisper")
            model = WhisperModel(model_ref, **fallback)
        _WHISPER_MODELS[key] = model
        return model

def prepare_local_whisper(cfg: ProviderConfig) -> dict:
    model = get_local_whisper(cfg)
    device, compute = _whisper_device(cfg)
    return {"ok":True,"model":cfg.model,"detail":f"Local Whisper '{cfg.model}' ready","runtime":type(model).__name__,"device":device,"compute_type":compute}

def _wav_to_float32(wav_bytes: bytes):
    import numpy as np, wave
    with wave.open(io.BytesIO(wav_bytes),"rb") as wf:
        channels, sampwidth, rate = wf.getnchannels(), wf.getsampwidth(), wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if sampwidth != 2:
        raise ValueError("Local Whisper expects 16-bit PCM WAV")
    audio = np.frombuffer(frames,dtype=np.int16).astype(np.float32)/32768.0
    if channels > 1:
        audio = audio.reshape(-1,channels).mean(axis=1)
    if rate != 16000:
        raise ValueError(f"Expected 16 kHz WAV, got {rate} Hz")
    return audio

def _local_whisper_transcribe(wav_bytes: bytes, cfg: ProviderConfig, language: str, prompt: str) -> tuple[str,str|None]:
    model = get_local_whisper(cfg)
    audio = _wav_to_float32(wav_bytes)
    kwargs = {"beam_size":1,"best_of":1,"temperature":0.0,"condition_on_previous_text":False,"vad_filter":False}
    code = lang_code(language)
    if code != "auto": kwargs["language"] = code
    if prompt: kwargs["hotwords"] = prompt[:500]
    with _WHISPER_INFER_LOCK:
        segments, info = model.transcribe(audio, **kwargs)
        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()
    return clean_asr_text(text), getattr(info,"language",None)

def _active_glossary(academic: AcademicConfig) -> str:
    profile = academic.glossary_profiles.get(academic.active_glossary_profile,"").strip()
    custom = academic.glossary.strip()
    return "\n".join(x for x in [profile,custom] if x)

def _parse_glossary(academic: AcademicConfig) -> list[tuple[str,str]]:
    pairs=[]
    for line in _active_glossary(academic).splitlines():
        if "=" in line:
            src,dst = [x.strip() for x in line.split("=",1)]
            if src and dst: pairs.append((src,dst))
    pairs.sort(key=lambda x:len(x[0]),reverse=True)
    return pairs

def academic_hotwords(academic: AcademicConfig) -> str:
    return ", ".join(src for src,_ in _parse_glossary(academic))

def _protect_academic_terms(text: str, academic: AcademicConfig) -> str:
    if not academic.preserve_academic_terms: return text
    for src,dst in _parse_glossary(academic):
        text = re.sub(re.escape(src),dst,text,flags=re.IGNORECASE)
    return text

def _bing_lang(value: str | None, *, source: bool=False) -> str:
    code = lang_code(value, "auto" if source else "zh")
    if source and code == "auto":
        return "auto-detect"
    if code in {"zh","zh-cn","zh-hans"}:
        return "zh-Hans"
    if code in {"zh-tw","zh-hant"}:
        return "zh-Hant"
    return code

def _parse_bing_result(result) -> str:
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected Bing response: {result!r}")
    if result.get("statusCode"):
        raise RuntimeError(str(result.get("errorMessage") or f"Bing returned status {result['statusCode']}"))
    translations = result.get("translations") or []
    if not translations or not isinstance(translations[0], dict):
        raise RuntimeError(f"Bing returned no translation: {result!r}")
    text = translations[0].get("text")
    if not text:
        raise RuntimeError(f"Bing returned an empty translation: {result!r}")
    return str(text).strip()

async def _translate_bing(text: str, target_language: str, academic: AcademicConfig) -> str:
    from mintrans import BingTranslator
    result = await asyncio.to_thread(
        BingTranslator().translate,
        _protect_academic_terms(text,academic),
        _bing_lang(academic.source_language, source=True),
        _bing_lang(target_language),
    )
    return _parse_bing_result(result)

async def test_provider(cfg: ProviderConfig, academic: AcademicConfig|None=None) -> dict:
    academic = academic or AcademicConfig()
    if cfg.mode == "local_whisper":
        try:
            import numpy as np
            model = get_local_whisper(cfg)
            with _WHISPER_INFER_LOCK:
                segments, _ = model.transcribe(np.zeros(16000,dtype=np.float32),beam_size=1,best_of=1,temperature=0.0,condition_on_previous_text=False,vad_filter=False)
                list(segments)
            device, compute = _whisper_device(cfg)
            return {"ok":True,"model":cfg.model,"detail":f"Local Whisper inference ready on {device}/{compute}","runtime":type(model).__name__}
        except Exception as exc:
            return {"ok":False,"model":cfg.model,"error":str(exc)}
    if cfg.mode == "bing_web":
        try:
            translated = await _translate_bing("Hello", "Chinese", academic)
            return {"ok":True,"url":"Bing web","models":["bing"],"detail":translated}
        except Exception as exc:
            return {"ok":False,"url":"Bing web","error":str(exc)}
    if cfg.mode == "azure_translator":
        if not cfg.api_key: return {"ok":False,"url":"Azure Translator","error":"API key is required"}
        try:
            await _translate_azure("Hello",cfg,"Chinese"); return {"ok":True,"url":"Azure Translator","models":["translator-v3"]}
        except Exception as exc:
            return {"ok":False,"url":"Azure Translator","error":str(exc)}
    base = normalize_base_url(cfg.base_url); url = f"{base}/models"; client = await http_client()
    try:
        r = await client.get(url,headers=auth_headers(cfg),timeout=min(cfg.timeout_seconds,15.0)); r.raise_for_status(); payload=r.json()
        return {"ok":True,"url":url,"models":[m.get("id","") for m in payload.get("data",[]) if isinstance(m,dict)]}
    except Exception as exc:
        return {"ok":False,"url":url,"error":str(exc)}

async def transcribe_wav(wav_bytes: bytes, cfg: ProviderConfig, language: str="auto", prompt: str="") -> tuple[str,str|None]:
    if cfg.mode == "local_whisper": return await asyncio.to_thread(_local_whisper_transcribe,wav_bytes,cfg,language,prompt)
    if cfg.mode == "openai_chat": return await _transcribe_chat_audio(wav_bytes,cfg,language,prompt)
    raise ValueError(f"ASR provider mode '{cfg.mode}' cannot transcribe audio")

async def _transcribe_chat_audio(wav_bytes: bytes, cfg: ProviderConfig, language: str, prompt: str) -> tuple[str,str|None]:
    url = cfg.endpoint or f"{normalize_base_url(cfg.base_url)}/chat/completions"
    instruction = prompt or "Transcribe the audio accurately. Output only the transcription."
    if language and language.lower() != "auto": instruction += f" Spoken language: {language}."
    payload={"model":cfg.model,"messages":[{"role":"user","content":[{"type":"text","text":instruction},{"type":"input_audio","input_audio":{"data":base64.b64encode(wav_bytes).decode("ascii"),"format":"wav"}}]}],"temperature":cfg.temperature,"max_tokens":cfg.max_tokens,"stream":False}
    r = await (await http_client()).post(url,headers={**auth_headers(cfg),"Content-Type":"application/json"},json=payload,timeout=cfg.timeout_seconds); r.raise_for_status()
    return clean_asr_text(str(r.json()["choices"][0]["message"]["content"])), None

def build_translation_prompt(text: str, academic: AcademicConfig, target_language: str|None=None, context: list[str]|None=None) -> str:
    target = target_language or academic.target_language
    glossary = _active_glossary(academic)
    glossary_block = f"Terminology to follow:\n{glossary}\n\n" if glossary else ""
    context = [x.strip() for x in (context or []) if x and x.strip()]
    context_block = "Previous context (do not translate this block):\n"+"\n".join(context)+"\n\n" if context else ""
    return academic.translation_prompt.format(target_language=target,glossary_block=glossary_block,context_block=context_block,text=text)

async def _translate_azure(text: str, cfg: ProviderConfig, target_language: str) -> str:
    params={"api-version":"3.0","to":lang_code(target_language,"zh")}; headers={"Ocp-Apim-Subscription-Key":cfg.api_key,"Content-Type":"application/json"}
    if cfg.region: headers["Ocp-Apim-Subscription-Region"] = cfg.region
    url = cfg.endpoint or (normalize_base_url(cfg.base_url) if cfg.base_url else "https://api.cognitive.microsofttranslator.com") + "/translate"
    r = await (await http_client()).post(url,params=params,headers=headers,json=[{"text":text}],timeout=cfg.timeout_seconds); r.raise_for_status()
    return str(r.json()[0]["translations"][0]["text"]).strip()

async def translate_text(text: str, cfg: ProviderConfig, academic: AcademicConfig, target_language: str|None=None, context: list[str]|None=None) -> str:
    if not text.strip(): return ""
    target = target_language or academic.target_language
    if cfg.mode == "bing_web": return await _translate_bing(text,target,academic)
    if cfg.mode == "azure_translator": return await _translate_azure(_protect_academic_terms(text,academic),cfg,target)
    if cfg.mode != "openai_chat": raise ValueError(f"Translation provider mode '{cfg.mode}' is not supported")
    url = cfg.endpoint or f"{normalize_base_url(cfg.base_url)}/chat/completions"
    payload={"model":cfg.model,"messages":[{"role":"user","content":build_translation_prompt(text,academic,target,context)}],"temperature":cfg.temperature,"max_tokens":cfg.max_tokens,"stream":False}
    r = await (await http_client()).post(url,headers={**auth_headers(cfg),"Content-Type":"application/json"},json=payload,timeout=cfg.timeout_seconds); r.raise_for_status(); content=r.json()["choices"][0]["message"]["content"]
    if isinstance(content,list): content="".join(item.get("text","") for item in content if isinstance(item,dict) and item.get("type") in {"text","output_text"})
    return str(content).strip()
