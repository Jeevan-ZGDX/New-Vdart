const SPEECH_WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const VISION_WS_URL = process.env.NEXT_PUBLIC_VISION_WS_URL || "ws://localhost:8765";
const COACH_WS_URL = process.env.NEXT_PUBLIC_COACH_WS_URL || "ws://localhost:8004/ws/coach";

export function connectWebSocket(onMessage) {
  let speechWs = null;
  let visionWs = null;
  let coachWs = null;
  let speechReconnectTimer = null;
  let visionReconnectTimer = null;
  let coachReconnectTimer = null;

  function connectSpeech() {
    speechWs = new WebSocket(SPEECH_WS_URL);
    speechWs.onopen = () => console.log("Speech WebSocket connected");
    speechWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage({ source: "speech", ...data });
      } catch (e) {
        console.error("Speech WebSocket parse error", e);
      }
    };
    speechWs.onclose = () => {
      speechReconnectTimer = setTimeout(connectSpeech, 1000);
    };
    speechWs.onerror = () => speechWs.close();
  }

  function connectVision() {
    visionWs = new WebSocket(VISION_WS_URL);
    visionWs.onopen = () => console.log("Vision WebSocket connected");
    visionWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage({ source: "vision", ...data });
      } catch (e) {
        console.error("Vision WebSocket parse error", e);
      }
    };
    visionWs.onclose = () => {
      visionReconnectTimer = setTimeout(connectVision, 1000);
    };
    visionWs.onerror = () => visionWs.close();
  }

  function connectCoach() {
    coachWs = new WebSocket(COACH_WS_URL);
    coachWs.onopen = () => console.log("Coach WebSocket connected");
    coachWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage({ source: "coach", ...data });
      } catch (e) {
        console.error("Coach WebSocket parse error", e);
      }
    };
    coachWs.onclose = () => {
      coachReconnectTimer = setTimeout(connectCoach, 1000);
    };
    coachWs.onerror = () => coachWs.close();
  }

  connectSpeech();
  connectVision();
  connectCoach();

  return {
    close() {
      if (speechReconnectTimer) clearTimeout(speechReconnectTimer);
      if (visionReconnectTimer) clearTimeout(visionReconnectTimer);
      if (coachReconnectTimer) clearTimeout(coachReconnectTimer);
      if (speechWs) speechWs.close();
      if (visionWs) visionWs.close();
      if (coachWs) coachWs.close();
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
    sendCoach(data) {
      if (coachWs && coachWs.readyState === WebSocket.OPEN) {
        coachWs.send(JSON.stringify(data));
      }
    },
  };
}
