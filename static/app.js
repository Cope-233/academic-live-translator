const $ = id => document.getElementById(id);
const q = s => [...document.querySelectorAll(s)];

const state = {
  config: null,
  session: null,
  ws: null,
  ctx: null,
  streams: [],
  nodes: [],
  processor: null,
  listening: false,
  devices: {supported:false, system:[], microphones:[]},
  language: 'zh-CN'
};

const I18N = {
  'zh-CN': {
    navLive:'实时', navMedia:'媒体', navLibrary:'资料库', navSettings:'设置', translation:'翻译',
    newSession:'+ 新建会话', liveTitle:'实时工作区', liveSubtitle:'课程、会议、访谈与线上活动共用一个实时双语工作区。',
    mediaTitle:'媒体工作区', mediaSubtitle:'处理已有音频和视频。', libraryTitle:'学术资料库', librarySubtitle:'搜索、打开或删除历史会话。',
    settingsTitle:'设置', settingsSubtitle:'配置界面语言、本地模型或 OpenAI-compatible 服务。',
    audioSource:'音频来源', browserMicrophone:'浏览器麦克风', browserSystem:'浏览器标签页 / 屏幕音频', browserMix:'浏览器系统音频 + 麦克风', windowsSystem:'Windows 系统音频 (WASAPI)', windowsMic:'Windows 原生麦克风', device:'设备',
    source:'源语言', target:'目标语言', auto:'自动', startListening:'开始监听', stopListening:'停止监听', original:'原文', idle:'空闲', listening:'监听中', translating:'翻译中…', stopped:'已停止', waitingAudio:'等待音频输入…', translationHere:'译文将在这里出现…',
    academicNotes:'学术笔记', notePlaceholder:'研究想法、追问、待办…', note:'📝 笔记', important:'⭐ 重点', question:'❓ 问题', idea:'💡 想法', reference:'📚 文献', followUp:'⚠ 待跟进', saveNote:'保存笔记',
    mediaTranscription:'媒体转录', mediaDesc:'音频 / 视频 → ASR → 翻译 → 带时间戳会话。', sessionTitlePlaceholder:'会话标题', processMedia:'处理媒体', searchPlaceholder:'搜索转录、翻译或笔记', refresh:'刷新',
    interface:'界面', language:'语言', languageHint:'界面语言会立即切换并自动保存。', type:'类型', name:'名称',
    asrHint:'默认使用轻量 Local Faster-Whisper。远程服务统一使用 OpenAI Chat Completions。', testAsr:'测试 ASR', translationHint:'Bing Free 无需密钥但属于实验性方案；稳定部署可使用 Microsoft Translator 或 OpenAI-compatible 服务。', testTranslation:'测试翻译',
    academicCapture:'学术与采集', translationMode:'翻译模式', lowestLatency:'最低延迟', balanced:'平衡', highestContext:'最高上下文', saveAudio:'保存音频', yes:'是', no:'否', customGlossary:'自定义术语表', saveSettings:'保存设置',
    noSession:'尚未创建会话', saved:'已保存', settingsSaved:'设置已保存', ready:'可用', failed:'失败', noAudioDevice:'没有可用的 Windows 音频设备', websocketTimeout:'WebSocket 连接超时', screenshotSaved:'截图已保存', chooseFile:'请选择文件', processing:'处理中…', done:'完成', startupError:'启动错误',
    open:'打开', delete:'删除', deleteConfirm:'删除此会话及其录音和截图？', noSessions:'暂无会话。', segments:'段', notes:'条笔记'
  },
  en: {
    navLive:'Live', navMedia:'Media', navLibrary:'Library', navSettings:'Settings', translation:'Translation',
    newSession:'+ New Session', liveTitle:'Live Workspace', liveSubtitle:'A shared bilingual workspace for classes, meetings, interviews and online events.',
    mediaTitle:'Media Workspace', mediaSubtitle:'Process existing audio and video.', libraryTitle:'Academic Library', librarySubtitle:'Search, open or delete previous sessions.',
    settingsTitle:'Settings', settingsSubtitle:'Configure interface language, local models or OpenAI-compatible services.',
    audioSource:'Audio source', browserMicrophone:'Browser microphone', browserSystem:'Browser tab / screen audio', browserMix:'Browser system + microphone', windowsSystem:'Windows system audio (WASAPI)', windowsMic:'Windows native microphone', device:'Device',
    source:'Source', target:'Target', auto:'Auto', startListening:'Start listening', stopListening:'Stop listening', original:'Original', idle:'Idle', listening:'Listening', translating:'Translating…', stopped:'Stopped', waitingAudio:'Waiting for audio input…', translationHere:'Translation will appear here…',
    academicNotes:'Academic Notes', notePlaceholder:'Research ideas, questions, follow-ups…', note:'📝 Note', important:'⭐ Important', question:'❓ Question', idea:'💡 Idea', reference:'📚 Reference', followUp:'⚠ Follow up', saveNote:'Save note',
    mediaTranscription:'Media transcription', mediaDesc:'Audio / video → ASR → translation → timestamped session.', sessionTitlePlaceholder:'Session title', processMedia:'Process media', searchPlaceholder:'Search transcript, translation or notes', refresh:'Refresh',
    interface:'Interface', language:'Language', languageHint:'The interface language changes immediately and is saved automatically.', type:'Type', name:'Name',
    asrHint:'Default: lightweight Local Faster-Whisper. Remote ASR uses OpenAI Chat Completions.', testAsr:'Test ASR', translationHint:'Bing Free is zero-key but experimental. Use Microsoft Translator or an OpenAI-compatible service for reliable deployments.', testTranslation:'Test translation',
    academicCapture:'Academic & capture', translationMode:'Translation mode', lowestLatency:'Lowest latency', balanced:'Balanced', highestContext:'Highest context', saveAudio:'Save audio', yes:'Yes', no:'No', customGlossary:'Custom glossary', saveSettings:'Save settings',
    noSession:'No session yet', saved:'Saved', settingsSaved:'Settings saved', ready:'Ready', failed:'Failed', noAudioDevice:'No Windows audio device available', websocketTimeout:'WebSocket timeout', screenshotSaved:'Screenshot saved', chooseFile:'Choose a file', processing:'Processing…', done:'Done', startupError:'Startup error',
    open:'Open', delete:'Delete', deleteConfirm:'Delete this session, its recordings and screenshots?', noSessions:'No sessions yet.', segments:'segments', notes:'notes'
  }
};

function tr(key){ return (I18N[state.language] && I18N[state.language][key]) || I18N['zh-CN'][key] || key; }

function applyLanguage(language){
  state.language = language === 'en' ? 'en' : 'zh-CN';
  document.documentElement.lang = state.language;
  q('[data-i18n]').forEach(el => { const key = el.dataset.i18n; if(tr(key)) el.textContent = tr(key); });
  q('[data-i18n-placeholder]').forEach(el => { const key = el.dataset.i18nPlaceholder; el.placeholder = tr(key); });
  if($('uiLanguage')) $('uiLanguage').value = state.language;
  const active = q('.nav').find(x => x.classList.contains('active'))?.dataset.view || 'live';
  updateViewHeading(active);
  if(!state.session && $('sessionTitle')) $('sessionTitle').value = tr('noSession');
  if($('micBtn')) $('micBtn').textContent = state.listening ? tr('stopListening') : tr('startListening');
  if($('asrStatus') && !state.listening) $('asrStatus').textContent = tr('idle');
}

function toast(t){
  const e=$('toast'); e.textContent=t; e.classList.add('show'); clearTimeout(e._t); e._t=setTimeout(()=>e.classList.remove('show'),2500);
}

async function api(path,opt={}){
  const r=await fetch(path,opt);
  if(!r.ok){ let d=`${r.status} ${r.statusText}`; try{d=(await r.json()).detail||d}catch{} throw new Error(d); }
  const ct=r.headers.get('content-type')||'';
  return ct.includes('json')?r.json():r.text();
}

function fmt(ms=0){ const s=Math.floor(ms/1000),m=Math.floor(s/60),x=s%60; return `${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`; }

function updateViewHeading(v){
  const map={live:['liveTitle','liveSubtitle'],media:['mediaTitle','mediaSubtitle'],library:['libraryTitle','librarySubtitle'],settings:['settingsTitle','settingsSubtitle']};
  const pair=map[v]||map.live;
  $('viewTitle').textContent=tr(pair[0]); $('viewSubtitle').textContent=tr(pair[1]);
}

function switchView(v){
  q('.nav').forEach(x=>x.classList.toggle('active',x.dataset.view===v));
  q('.view').forEach(x=>x.classList.toggle('active',x.id===v));
  updateViewHeading(v);
  $('newSessionBtn').style.display=v==='live'?'':'none';
  if(v==='library') loadSessions();
}
q('.nav').forEach(x=>x.onclick=()=>switchView(x.dataset.view));

function providerUI(){
  $('asrLocal').style.display=$('asrMode').value==='local_whisper'?'block':'none';
  $('asrRemote').style.display=$('asrMode').value==='local_whisper'?'none':'block';
  $('mtOpenAI').style.display=$('mtMode').value==='openai_chat'?'block':'none';
  $('mtAzure').style.display=$('mtMode').value==='azure_translator'?'block':'none';
}

const TARGET_LANGUAGES = new Set(['Chinese','English','Japanese','Korean','French','German','Spanish','Arabic']);

async function loadConfig(){
  state.config=await api('/api/config');
  const c=state.config;
  state.language=c.interface?.language||'zh-CN';
  applyLanguage(state.language);
  $('asrMini').textContent=`${c.asr.name} · ${c.asr.model}`;
  $('mtMini').textContent=`${c.translation.name} · ${c.translation.model}`;
  $('asrMode').value=c.asr.mode==='local_whisper'?'local_whisper':'openai_chat';
  $('asrName').value=c.asr.name;
  $('asrModel').value=['tiny','base','small','medium','large-v3-turbo'].includes(c.asr.model)?c.asr.model:'base';
  $('asrModelRemote').value=c.asr.model;
  $('asrDevice').value=c.asr.device||'auto';
  $('asrCompute').value=c.asr.compute_type||'auto';
  $('asrBaseUrl').value=c.asr.base_url||'';
  $('asrApiKey').value=c.asr.api_key||'';
  $('asrEndpoint').value=c.asr.endpoint||'';
  $('mtMode').value=c.translation.mode;
  $('mtName').value=c.translation.name;
  $('mtBaseUrl').value=c.translation.base_url||'';
  $('mtModel').value=c.translation.model||'';
  $('mtApiKey').value=c.translation.api_key||'';
  $('mtAzureKey').value=c.translation.mode==='azure_translator'?(c.translation.api_key||''):'';
  $('mtRegion').value=c.translation.region||'';
  const target=TARGET_LANGUAGES.has(c.academic.target_language)?c.academic.target_language:'Chinese';
  $('sourceLanguage').value=c.academic.source_language;
  $('targetLanguage').value=target;
  $('translationMode').value=c.academic.translation_mode;
  $('glossary').value=c.academic.glossary||'';
  $('silenceMs').value=c.live.silence_ms;
  $('minSpeechMs').value=c.live.min_speech_ms;
  $('maxSegmentMs').value=c.live.max_segment_ms;
  $('saveAudio').value=String(c.capture.save_audio);
  $('audioFormat').value=c.capture.audio_format;
  $('audioSource').value=c.capture.input_source;
  $('liveSourceLanguage').value=c.academic.source_language;
  $('liveTargetLanguage').value=target;
  $('uiLanguage').value=state.language;
  providerUI();
}

function formConfig(){
  const c=structuredClone(state.config);
  c.interface=c.interface||{};
  c.interface.language=$('uiLanguage').value;
  c.asr.mode=$('asrMode').value;
  c.asr.name=$('asrName').value.trim()||'ASR';
  c.asr.model=c.asr.mode==='local_whisper'?$('asrModel').value:$('asrModelRemote').value.trim();
  c.asr.device=$('asrDevice').value;
  c.asr.compute_type=$('asrCompute').value;
  c.asr.base_url=$('asrBaseUrl').value.trim();
  c.asr.api_key=$('asrApiKey').value;
  c.asr.endpoint=$('asrEndpoint').value.trim()||null;
  c.translation.mode=$('mtMode').value;
  c.translation.name=$('mtName').value.trim()||'Translation';
  c.translation.model=c.translation.mode==='bing_web'?'bing':c.translation.mode==='azure_translator'?'translator-v3':$('mtModel').value.trim();
  c.translation.base_url=c.translation.mode==='azure_translator'?'https://api.cognitive.microsofttranslator.com':$('mtBaseUrl').value.trim();
  c.translation.api_key=c.translation.mode==='azure_translator'?$('mtAzureKey').value:$('mtApiKey').value;
  c.translation.region=$('mtRegion').value.trim();
  c.academic.source_language=$('sourceLanguage').value||'auto';
  c.academic.target_language=$('targetLanguage').value||'Chinese';
  c.academic.translation_mode=$('translationMode').value;
  c.academic.glossary=$('glossary').value;
  c.live.silence_ms=Number($('silenceMs').value);
  c.live.min_speech_ms=Number($('minSpeechMs').value);
  c.live.max_segment_ms=Number($('maxSegmentMs').value);
  c.capture.save_audio=$('saveAudio').value==='true';
  c.capture.audio_format=$('audioFormat').value;
  c.capture.input_source=$('audioSource').value;
  return c;
}

async function saveConfig(){
  state.config=formConfig();
  await api('/api/config',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.config)});
  $('asrMini').textContent=`${state.config.asr.name} · ${state.config.asr.model}`;
  $('mtMini').textContent=`${state.config.translation.name} · ${state.config.translation.model}`;
  $('saveStatus').textContent=tr('saved')+' '+new Date().toLocaleTimeString();
  applyLanguage(state.config.interface.language);
  toast(tr('settingsSaved'));
}

async function saveUILanguage(){
  if(!state.config) return;
  state.config.interface=state.config.interface||{};
  state.config.interface.language=$('uiLanguage').value;
  applyLanguage(state.config.interface.language);
  try{
    await api('/api/config',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.config)});
  }catch(e){ toast(e.message); }
}

async function testProvider(k){
  try{
    await saveConfig();
    const r=await api('/api/providers/test/'+k,{method:'POST'});
    $(k==='asr'?'asrTestResult':'mtTestResult').textContent=r.ok?'✓ '+tr('ready'):'✕ '+(r.error||tr('failed'));
  }catch(e){ $(k==='asr'?'asrTestResult':'mtTestResult').textContent='✕ '+e.message; }
}

$('asrMode').onchange=providerUI;
$('mtMode').onchange=providerUI;
$('uiLanguage').onchange=saveUILanguage;
$('saveSettingsBtn').onclick=()=>saveConfig().catch(e=>toast(e.message));
$('testAsrBtn').onclick=()=>testProvider('asr');
$('testMtBtn').onclick=()=>testProvider('translation');

async function loadDevices(){ try{state.devices=await api('/api/audio/devices')}catch{} updateDeviceUI(); }
function updateDeviceUI(){
  const src=$('audioSource').value,native=src.startsWith('native_');
  $('nativeDeviceWrap').hidden=!native;
  if(!native)return;
  const list=src==='native_system'?state.devices.system:state.devices.microphones;
  $('nativeDevice').innerHTML=(list||[]).map(d=>`<option value="${d.index}">${d.default?'★ ':''}${d.name}</option>`).join('');
}
$('audioSource').onchange=updateDeviceUI;

async function createSession(){
  state.session=await api('/api/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:'live',input_source:$('audioSource').value})});
  renderSession(); return state.session;
}
$('newSessionBtn').onclick=()=>createSession().catch(e=>toast(e.message));

function esc(x=''){ const d=document.createElement('div'); d.textContent=x; return d.innerHTML; }

function renderSession(){
  const s=state.session;if(!s)return;
  $('sessionTitle').value=s.title;$('sessionTitle').disabled=false;
  const o=$('originalList'),t=$('translationList');o.classList.remove('empty');t.classList.remove('empty');
  o.innerHTML=s.segments.length?'':tr('waitingAudio'); t.innerHTML=s.segments.length?'':tr('translationHere');
  for(const seg of s.segments){
    o.insertAdjacentHTML('beforeend',`<div class="segment"><small>${fmt(seg.start_ms)}</small>${esc(seg.source)}</div>`);
    t.insertAdjacentHTML('beforeend',`<div class="segment"><small>${fmt(seg.start_ms)}</small>${esc(seg.translation)}</div>`);
  }
  renderNotes();
}

function renderNotes(){
  $('annotationList').innerHTML=(state.session?.annotations||[]).map(a=>`<div class="annotation"><small>${fmt(a.timestamp_ms)} · ${a.kind}</small><div>${esc(a.text||'(marked)')}</div></div>`).join('');
}
async function refreshSession(){ if(state.session){ state.session=await api('/api/sessions/'+state.session.id); renderSession(); } }

async function syncLive(){
  const target=$('liveTargetLanguage').value||'Chinese';
  state.config.academic.source_language=$('liveSourceLanguage').value;
  state.config.academic.target_language=target;
  state.config.capture.input_source=$('audioSource').value;
  await api('/api/config',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(state.config)});
}

function handleWs(e){
  let x;try{x=JSON.parse(e.data)}catch{return}
  if(x.type==='transcript') $('asrStatus').textContent=tr('translating');
  if(x.type==='segment'){ state.session.segments.push(x.segment); renderSession(); $('asrStatus').textContent=tr('listening'); }
  if(x.type==='error') toast(x.message);
}

async function startNative(){
  const dev=$('nativeDevice').value;if(!dev)throw new Error(tr('noAudioDevice'));
  const proto=location.protocol==='https:'?'wss':'ws';
  state.ws=new WebSocket(`${proto}://${location.host}/ws/native?session_id=${state.session.id}&source=${$('audioSource').value}&device=${dev}`);
  state.ws.onmessage=handleWs;
  await new Promise((ok,no)=>{state.ws.onopen=ok;setTimeout(()=>no(new Error(tr('websocketTimeout'))),5000)});
}

function downsample(buf,rate){
  if(rate===16000)return new Int16Array(buf.map(x=>Math.max(-1,Math.min(1,x))*32767));
  const ratio=rate/16000,out=new Int16Array(Math.floor(buf.length/ratio));
  for(let i=0;i<out.length;i++){const a=Math.floor(i*ratio),b=Math.min(buf.length,Math.floor((i+1)*ratio));let s=0;for(let j=a;j<b;j++)s+=buf[j];out[i]=Math.max(-1,Math.min(1,s/(b-a||1)))*32767}
  return out;
}

async function startBrowser(){
  const src=$('audioSource').value;let streams=[];
  if(src==='microphone')streams=[await navigator.mediaDevices.getUserMedia({audio:true})];
  else if(src==='browser_system')streams=[await navigator.mediaDevices.getDisplayMedia({video:true,audio:true})];
  else streams=[await navigator.mediaDevices.getDisplayMedia({video:true,audio:true}),await navigator.mediaDevices.getUserMedia({audio:true})];
  state.streams=streams;state.ctx=new AudioContext();const dest=state.ctx.createMediaStreamDestination();
  for(const st of streams){const tracks=st.getAudioTracks();if(!tracks.length)continue;const node=state.ctx.createMediaStreamSource(new MediaStream(tracks));node.connect(dest);state.nodes.push(node)}
  const mix=state.ctx.createMediaStreamSource(dest.stream),proc=state.ctx.createScriptProcessor(2048,1,1);mix.connect(proc);const mute=state.ctx.createGain();mute.gain.value=0;proc.connect(mute);mute.connect(state.ctx.destination);state.processor=proc;
  const proto=location.protocol==='https:'?'wss':'ws';state.ws=new WebSocket(`${proto}://${location.host}/ws/live?session_id=${state.session.id}`);state.ws.onmessage=handleWs;
  await new Promise((ok,no)=>{state.ws.onopen=ok;setTimeout(()=>no(new Error(tr('websocketTimeout'))),5000)});
  proc.onaudioprocess=e=>{if(state.ws?.readyState===1)state.ws.send(downsample(e.inputBuffer.getChannelData(0),state.ctx.sampleRate).buffer)};
}

async function startListening(){
  try{
    if(!state.session)await createSession();await syncLive();const src=$('audioSource').value;
    if(src.startsWith('native_'))await startNative();else await startBrowser();
    state.listening=true;$('micBtn').textContent=tr('stopListening');$('asrStatus').textContent=tr('listening');
  }catch(e){toast(e.message);cleanup()}
}

function cleanup(){
  try{state.processor&&(state.processor.onaudioprocess=null)}catch{}
  for(const s of state.streams)for(const t of s.getTracks())t.stop();
  try{state.ctx?.close()}catch{}
  state.streams=[];state.nodes=[];state.ctx=null;state.processor=null;
}

async function stopListening(){
  state.listening=false;try{state.ws?.send(JSON.stringify({type:'stop'}))}catch{}cleanup();
  $('micBtn').textContent=tr('startListening');$('asrStatus').textContent=tr('stopped');setTimeout(refreshSession,700);
}
$('micBtn').onclick=()=>state.listening?stopListening():startListening();

async function mark(kind,text=''){
  if(!state.session)await createSession();
  state.session=await api(`/api/sessions/${state.session.id}/annotations`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,text})});
  renderNotes();toast(tr('saved'));
}
$('quickImportant').onclick=()=>mark('important');$('quickQuestion').onclick=()=>mark('question');$('quickIdea').onclick=()=>mark('idea');
$('saveNoteBtn').onclick=()=>{const t=$('noteText').value.trim();if(t){mark($('noteKind').value,t);$('noteText').value=''}};
$('captureSlideBtn').onclick=async()=>{if(!state.session)await createSession();try{state.session=await api(`/api/sessions/${state.session.id}/screenshot`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});toast(tr('screenshotSaved'))}catch(e){toast(e.message)}};

async function loadSessions(){
  const items=await api('/api/sessions?q='+encodeURIComponent($('sessionSearch').value.trim()));
  $('sessionList').innerHTML=items.length?items.map(s=>`<div class="session" data-id="${s.id}"><div><strong>${esc(s.title)}</strong><p>${s.segments} ${tr('segments')} · ${s.annotations} ${tr('notes')} · ${s.source_language} → ${s.target_language}</p></div><div><button class="open">${tr('open')}</button> <button class="danger delete">${tr('delete')}</button></div></div>`).join(''):`<div class="pad muted">${tr('noSessions')}</div>`;
  q('.session').forEach(el=>{
    el.querySelector('.open').onclick=async()=>{state.session=await api('/api/sessions/'+el.dataset.id);renderSession();switchView('live')};
    el.querySelector('.delete').onclick=async()=>{if(confirm(tr('deleteConfirm'))){await api('/api/sessions/'+el.dataset.id,{method:'DELETE'});loadSessions()}};
  });
}
$('refreshSessionsBtn').onclick=loadSessions;
$('sessionSearch').oninput=()=>setTimeout(loadSessions,200);

$('processFileBtn').onclick=async()=>{
  const f=$('mediaFile').files[0];if(!f)return toast(tr('chooseFile'));
  $('mediaStatus').textContent=tr('processing');const fd=new FormData();fd.append('file',f);
  try{
    state.session=await api('/api/process-file?title='+encodeURIComponent($('mediaTitle').value.trim()),{method:'POST',body:fd});
    $('mediaStatus').textContent=`${tr('done')}: ${state.session.segments.length} ${tr('segments')}`;renderSession();switchView('live');
  }catch(e){$('mediaStatus').textContent=e.message}
};

$('sessionTitle').onchange=async()=>{if(state.session)state.session=await api('/api/sessions/'+state.session.id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:$('sessionTitle').value})})};

(async()=>{try{await loadConfig();await loadDevices();await loadSessions()}catch(e){toast(tr('startupError')+': '+e.message)}})();
