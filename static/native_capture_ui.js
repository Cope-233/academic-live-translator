(() => {
  const nativeStartTimeoutMs = 7000;

  // beta 0.5: ASR results are rendered immediately; translation updates the
  // same segment later instead of being required before original text appears.
  const baseHandleWs = handleWs;
  handleWs = function handleWsBeta05(event) {
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

  // Provider-specific modes should not retain stale llama.cpp/OpenAI fields.
  const baseFormConfig = formConfig;
  formConfig = function formConfigBeta05() {
    const c = baseFormConfig();
    if (c.asr.mode === 'local_whisper') {
      c.asr.name = 'Local Whisper';
      c.asr.base_url = '';
      c.asr.api_key = '';
      c.asr.endpoint = null;
    }
    if (c.translation.mode === 'bing_web') {
      c.translation.name = 'Bing Translate (Free)';
      c.translation.base_url = '';
      c.translation.api_key = '';
      c.translation.endpoint = null;
    }
    return c;
  };

  startNative = async function startNativeBeta05() {
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

  const originalToggleFloatingWindow = toggleFloatingWindow;
  const toggleFloatingWindowBeta05 = async () => {
    await originalToggleFloatingWindow();
    if (floatingWindowIsOpen()) {
      state.floatingWindow.document.title = 'Academic Live Translator beta 0.5';
    }
  };
  $('floatingWindowBtn').onclick = toggleFloatingWindowBeta05;
  $('floatingWindowSettingsBtn').onclick = toggleFloatingWindowBeta05;
})();
