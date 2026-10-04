from app.audio import SpeechEndpointDetector, pcm16_to_wav_bytes, wav_duration_ms
from app.exporters import export_markdown, export_srt
from app.models import LiveConfig, Segment, SessionData
from app.providers import clean_asr_text

def test_clean_qwen_prefix(): assert clean_asr_text("language English<asr_text>Hello world") == "Hello world"
def test_wav_duration():
    wav=pcm16_to_wav_bytes(b"\x00\x00"*16000,16000); assert 995 <= wav_duration_ms(wav) <= 1005
def test_endpoint_detector():
    cfg=LiveConfig(speech_threshold=0.01,silence_ms=200,min_speech_ms=100,pre_roll_ms=0); d=SpeechEndpointDetector(cfg); loud=int(0.1*32767).to_bytes(2,"little",signed=True)*1600; silence=b"\x00\x00"*1600
    d.feed(loud); d.feed(loud); d.feed(silence); result=d.feed(silence)[1]; assert result is not None
def test_exporters():
    s=SessionData(id="x",title="Test",created_at="now",updated_at="now",segments=[Segment(id="1",start_ms=0,end_ms=1000,source="Hello",translation="你好")]); assert "Hello" in export_markdown(s); assert "00:00:00,000 --> 00:00:01,000" in export_srt(s)
