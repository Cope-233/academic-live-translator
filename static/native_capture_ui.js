(() => {
  const nativeStartTimeoutMs = 7000;
  const ASR_MODES = ['local_whisper', 'openai_chat'];
  const TRANSLATION_MODES = ['bing_web', 'azure_translator', 'openai_chat'];

  // ASR results are rendered immediately; translation updates the same segment
  // later instead of being required before original text appears.
  const baseHandleWs = handleWs;
  handleWs = function handleWsBeta07(event) {
    let message = null;
    try { message = JSON.parse(event.data); } catch {}

    if (message?.type === 'segment_update' && state.session) {
      const updated = message.segment;
      const index = state.session.segments.findIndex(seg => seg.id === updated?.id);
      if (index >= 0) state.session.segments[index] = updated;
      else if (updated) state.session.segments.push(updated);
      renderSession();
      return;
    }

    baseHandleWs(event);
  };

  const clone = value => structuredClone(value);

  function defaultAsrProfile(mode) {
    if (mode === 'openai_chat') {
      return {
        name: 'OpenAI-compatible ASR', mode: 'openai_chat',
        base_url: 'http://127.0.0.1:8080/v1', api_key: '', model: '', endpoint: null,
        timeout_seconds: 120, temperature: 0, max_tokens: 4096,
        device: 'auto', compute_type: 'auto', region: ''
      };
    }
    return {
      name: 'Local Whisper', mode: 'local_whisper', base_url: '', api_key: '',
      model: 'base', endpoint: null, timeout_seconds: 120, temperature: 0,
      max_tokens: 4096, device: 'auto', compute_type: 'auto', region: ''
    };
  }

  function defaultTranslationProfile(mode) {
    if (mode === 'azure_translator') {
      return {
        name: 'Microsoft Translator', mode, base_url: 'https://api.cognitive.microsofttranslator.com',
        api_key: '', model: 'translator-v3', endpoint: null, timeout_seconds: 120,
        temperature: 0, max_tokens: 4096, device: 'auto', compute_type: 'auto', region: ''
      };
    }
    if (mode === 'openai_chat') {
      return {
        name: 'OpenAI-compatible Translation', mode, base_url: '', api_key: '', model: '',
        endpoint: null, timeout_seconds: 120, temperature: 0, max_tokens: 4096,
        device: 'auto', compute_type: 'auto', region: ''
      };
    }
    return {
      name: 'Bing Translate (Free)', mode: 'bing_web', base_url: '', api_key: '',
      model: 'bing', endpoint: null, timeout_seconds: 120, temperature: 0,
      max_tokens: 4096, device: 'auto', compute_type: 'auto', region: ''
    };
  }

  function ensureProviderProfiles(config) {
    config.providers = config.providers || {};
    const p = config.providers;
    p.asr = p.asr || {};
    p.translation = p.translation || {};

    const currentAsrMode = ASR_MODES.includes(config.asr?.mode) ? config.asr.mode : 'local_whisper';
    const currentTranslationMode = TRANSLATION_MODES.includes(config.translation?.mode)
      ? config.translation.mode : 'bing_web';

    p.active_asr = ASR_MODES.includes(p.active_asr) ? p.active_asr : currentAsrMode;
    p.active_translation = TRANSLATION_MODES.includes(p.active_translation)
      ? p.active_translation : currentTranslationMode;

    for (const mode of ASR_MODES) {
      if (!p.asr[mode]) {
        p.asr[mode] = currentAsrMode === mode && config.asr
          ? clone(config.asr) : defaultAsrProfile(mode);
      }
      p.asr[mode].mode = mode;
    }

    for (const mode of TRANSLATION_MODES) {
      if (!p.translation[mode]) {
        p.translation[mode] = currentTranslationMode === mode && config.translation
          ? clone(config.translation) : defaultTranslationProfile(mode);
      }
      p.translation[mode].mode = mode;
    }
    return p;
  }

  function readAsrProfile(mode) {
    const p = ensureProviderProfiles(state.config);
    const profile = clone(p.asr[mode] || defaultAsrProfile(mode));
    profile.mode = mode;
    profile.name = $('asrName').value.trim() || profile.name || (mode === 'local_whisper' ? 'Local Whisper' : 'OpenAI-compatible ASR');

    if (mode === 'local_whisper') {
      profile.model = $('asrModel').value;
      profile.device = $('asrDevice').value;
      profile.compute_type = $('asrCompute').value || 'auto';
    } else {
      profile.model = $('asrModelRemote').value.trim();
      profile.base_url = $('asrBaseUrl').value.trim();
      profile.api_key = $('asrApiKey').value;
      profile.endpoint = $('asrEndpoint').value.trim() || null;
    }
    return profile;
  }

  function writeAsrProfile(mode) {
    const p = ensureProviderProfiles(state.config);
    const profile = p.asr[mode] || defaultAsrProfile(mode);
    $('asrMode').value = mode;
    $('asrName').value = profile.name || '';

    if (mode === 'local_whisper') {
      const localModels = ['tiny', 'base', 'small', 'medium', 'large-v3-turbo'];
      $('asrModel').value = localModels.includes(profile.model) ? profile.model : 'base';
      if ([...$('asrDevice').options].some(option => option.value === (profile.device || 'auto'))) {
        $('asrDevice').value = profile.device || 'auto';
      }
      $('asrCompute').value = profile.compute_type || 'auto';
    } else {
      $('asrModelRemote').value = profile.model || '';
      $('asrBaseUrl').value = profile.base_url || '';
      $('asrApiKey').value = profile.api_key || '';
      $('asrEndpoint').value = profile.endpoint || '';
    }

    state.config.asr = clone(profile);
  }

  function readTranslationProfile(mode) {
    const p = ensureProviderProfiles(state.config);
    const profile = clone(p.translation[mode] || defaultTranslationProfile(mode));
    profile.mode = mode;
    profile.name = $('mtName').value.trim() || profile.name || 'Translation';

    if (mode === 'openai_chat') {
      profile.base_url = $('mtBaseUrl').value.trim();
      profile.model = $('mtModel').value.trim();
      profile.api_key = $('mtApiKey').value;
    } else if (mode === 'azure_translator') {
      profile.base_url = 'https://api.cognitive.microsofttranslator.com';
      profile.model = 'translator-v3';
      profile.api_key = $('mtAzureKey').value;
      profile.region = $('mtRegion').value.trim();
    } else {
      profile.model = 'bing';
    }
    return profile;
  }

  function writeTranslationProfile(mode) {
    const p = ensureProviderProfiles(state.config);
    const profile = p.translation[mode] || defaultTranslationProfile(mode);
    $('mtMode').value = mode;
    $('mtName').value = profile.name || '';

    if (mode === 'openai_chat') {
      $('mtBaseUrl').value = profile.base_url || '';
      $('mtModel').value = profile.model || '';
      $('mtApiKey').value = profile.api_key || '';
    } else if (mode === 'azure_translator') {
      $('mtAzureKey').value = profile.api_key || '';
      $('mtRegion').value = profile.region || '';
    }

    state.config.translation = clone(profile);
  }

  function updateProviderBadges() {
    if (!state.config) return;
    $('asrMini').textContent = `${state.config.asr.name} · ${state.config.asr.model}`;
    $('mtMini').textContent = `${state.config.translation.name} · ${state.config.translation.model}`;
  }

  function restoreProviderUi(config) {
    const p = ensureProviderProfiles(config);
    state._activeAsrMode = p.active_asr;
    state._activeTranslationMode = p.active_translation;
    writeAsrProfile(p.active_asr);
    writeTranslationProfile(p.active_translation);
    providerUI();
    updateProviderBadges();
  }

  function switchAsrProfile() {
    if (!state.config) return providerUI();
    const p = ensureProviderProfiles(state.config);
    const next = $('asrMode').value;
    const previous = state._activeAsrMode || p.active_asr;

    if (ASR_MODES.includes(previous) && previous !== next) {
      p.asr[previous] = readAsrProfile(previous);
    }
    p.active_asr = next;
    state._activeAsrMode = next;
    writeAsrProfile(next);
    providerUI();
    updateProviderBadges();
  }

  function switchTranslationProfile() {
    if (!state.config) return providerUI();
    const p = ensureProviderProfiles(state.config);
    const next = $('mtMode').value;
    const previous = state._activeTranslationMode || p.active_translation;

    if (TRANSLATION_MODES.includes(previous) && previous !== next) {
      p.translation[previous] = readTranslationProfile(previous);
    }
    p.active_translation = next;
    state._activeTranslationMode = next;
    writeTranslationProfile(next);
    providerUI();
    updateProviderBadges();
  }

  function captureCurrentProviderProfiles() {
    const p = ensureProviderProfiles(state.config);
    const asrMode = ASR_MODES.includes($('asrMode').value) ? $('asrMode').value : p.active_asr;
    const translationMode = TRANSLATION_MODES.includes($('mtMode').value)
      ? $('mtMode').value : p.active_translation;

    p.active_asr = asrMode;
    p.asr[asrMode] = readAsrProfile(asrMode);
    p.active_translation = translationMode;
    p.translation[translationMode] = readTranslationProfile(translationMode);
    state._activeAsrMode = asrMode;
    state._activeTranslationMode = translationMode;
  }

  const baseLoadConfig = loadConfig;
  loadConfig = async function loadConfigBeta07() {
    const config = await baseLoadConfig();
    restoreProviderUi(config);
    return config;
  };

  const baseFormConfig = formConfig;
  formConfig = function formConfigBeta07() {
    captureCurrentProviderProfiles();
    const c = baseFormConfig();
    const p = ensureProviderProfiles(state.config);
    c.providers = clone(p);
    c.asr = clone(p.asr[p.active_asr]);
    c.translation = clone(p.translation[p.active_translation]);
    return c;
  };

  $('asrMode').onchange = switchAsrProfile;
  $('mtMode').onchange = switchTranslationProfile;

  startNative = async function startNativeBeta07() {
    const dev = $('nativeDevice').value;
    if (!dev) throw new Error(tr('noAudioDevice'));

    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(
      `${proto}://${location.host}/ws/native?session_id=${state.session.id}&source=${$('audioSource').value}&device=${dev}`
    );
    state.ws = ws;

    await new Promise((resolve, reject) => {
      let settled = false;
      const timeout = setTimeout(() => {
        fail(new Error(
          state.language === 'en'
            ? 'Windows audio device did not open in time. Try another WASAPI device or check Windows audio settings.'
            : 'Windows 原生音频设备未能及时打开。请尝试其他 WASAPI 设备，或检查 Windows 音频设置。'
        ));
      }, nativeStartTimeoutMs);

      function finish() {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        resolve();
      }

      function fail(error) {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        try { ws.close(); } catch {}
        if (state.ws === ws) state.ws = null;
        reject(error);
      }

      ws.onmessage = event => {
        let message = null;
        try { message = JSON.parse(event.data); } catch {}

        if (message?.type === 'error' && message?.stage !== 'translation') {
          fail(new Error(message.message || tr('failed')));
          return;
        }

        handleWs(event);
        if (message?.type === 'ready') finish();
      };

      ws.onerror = () => fail(new Error(
        state.language === 'en'
          ? 'Windows microphone WebSocket failed.'
          : 'Windows 原生麦克风连接失败。'
      ));

      ws.onclose = () => {
        if (!settled) {
          fail(new Error(
            state.language === 'en'
              ? 'Windows audio capture closed before the device became ready.'
              : 'Windows 原生音频设备就绪前，采集连接已关闭。'
          ));
        }
      };
    });

    ws.onmessage = event => {
      let message = null;
      try { message = JSON.parse(event.data); } catch {}
      handleWs(event);
      if (message?.type === 'error' && message?.stage !== 'translation' && state.ws === ws) {
        state.listening = false;
        state.ws = null;
        cleanup();
        $('micBtn').textContent = tr('startListening');
        try { ws.close(); } catch {}
      }
    };
    ws.onerror = null;
    ws.onclose = null;
  };

  // Keep the floating-window patch separate from the original function name to
  // avoid the beta 0.6 temporal-dead-zone collision.
  const baseToggleFloatingWindow = toggleFloatingWindow;
  const toggleFloatingWindowBeta07 = async () => {
    await baseToggleFloatingWindow();
    if (floatingWindowIsOpen()) {
      state.floatingWindow.document.title = 'Academic Live Translator beta 0.7';
    }
  };
  $('floatingWindowBtn').onclick = toggleFloatingWindowBeta07;
  $('floatingWindowSettingsBtn').onclick = toggleFloatingWindowBeta07;

  document.title = 'Academic Live Translator beta 0.7';
  const brandVersion = document.querySelector('.brand span');
  if (brandVersion) brandVersion.textContent = 'beta 0.7 · WebUI';

  // beta 0.7 restores the persisted active providers immediately on startup
  // instead of leaving the HTML's first-option Whisper/Bing placeholders visible.
  if (state.config) restoreProviderUi(state.config);
  else ensureConfigLoaded().catch(error => toast(`${tr('startupError')}: ${error.message}`));
})();
