const SPEECH_WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const VISION_WS_URL = process.env.NEXT_PUBLIC_VISION_WS_URL || "ws://localhost:8765";

export function connectWebSocket(onMessage) {
  let speechWs = null;
  let visionWs = null;
  let speechReconnectTimer = null;
  let visionReconnectTimer = null;

  function connectSpeech() {
    speechWs = new WebSocket(SPEECH_WS_URL);

    speechWs.onopen = () => {
      console.log("Speech WebSocket connected");
    };

    speechWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error("Speech WebSocket parse error", e);
      }
    };

    speechWs.onclose = () => {
      console.log("Speech WebSocket disconnected, reconnecting in 1s...");
      speechReconnectTimer = setTimeout(connectSpeech, 1000);
    };

    speechWs.onerror = () => {
      speechWs.close();
    };
  }

  function connectVision() {
    visionWs = new WebSocket(VISION_WS_URL);

    visionWs.onopen = () => {
      console.log("Vision WebSocket connected");
    };

    visionWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error("Vision WebSocket parse error", e);
      }
    };

    visionWs.onclose = () => {
      console.log("Vision WebSocket disconnected, reconnecting in 1s...");
      visionReconnectTimer = setTimeout(connectVision, 1000);
    };

    visionWs.onerror = () => {
      visionWs.close();
    };
  }

  connectSpeech();
  connectVision();

  return {
    close() {
      if (speechReconnectTimer) clearTimeout(speechReconnectTimer);
      if (visionReconnectTimer) clearTimeout(visionReconnectTimer);
      if (speechWs) speechWs.close();
      if (visionWs) visionWs.close();
    },
    send(data) {
      if (speechWs && speechWs.readyState === WebSocket.OPEN) {
        speechWs.send(JSON.stringify(data));
      }
    },
    sendVision(data) {
      if (visionWs && visionWs.readyState === WebSocket.OPEN) {
        visionWs.send(JSON.stringify(data));
      }
    },
  };
}
