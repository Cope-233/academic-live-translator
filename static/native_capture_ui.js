(() => {
  const nativeStartTimeoutMs = 7000;

  startNative = async function startNativeBeta03() {
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
            ? 'Windows microphone returned no audio stream. Try another WASAPI device or check Windows exclusive-mode settings.'
            : 'Windows 原生麦克风未返回音频流。请尝试其他 WASAPI 设备，或检查 Windows 麦克风独占模式设置。'
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
        handleWs(event);

        if (message?.type === 'level') finish();
        if (message?.type === 'error') fail(new Error(message.message || tr('failed')));
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
              ? 'Windows microphone capture closed before audio was received.'
              : 'Windows 原生麦克风在收到音频前已关闭。'
          ));
        }
      };
    });

    ws.onmessage = handleWs;
    ws.onerror = null;
    ws.onclose = null;
  };

  const originalToggleFloatingWindow = toggleFloatingWindow;
  const toggleFloatingWindowBeta03 = async () => {
    await originalToggleFloatingWindow();
    if (floatingWindowIsOpen()) {
      state.floatingWindow.document.title = 'Academic Live Translator beta 0.3';
    }
  };
  $('floatingWindowBtn').onclick = toggleFloatingWindowBeta03;
  $('floatingWindowSettingsBtn').onclick = toggleFloatingWindowBeta03;
})();
