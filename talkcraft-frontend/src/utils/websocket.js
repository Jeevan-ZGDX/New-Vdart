const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export function connectWebSocket(onMessage) {
  let ws = null;
  let reconnectTimer = null;

  function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error("WebSocket parse error", e);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected, reconnecting in 1s...");
      reconnectTimer = setTimeout(connect, 1000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  connect();

  return {
    close() {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    },
  };
}
