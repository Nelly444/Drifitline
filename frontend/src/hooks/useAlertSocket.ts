import { useEffect, useRef, useState } from "react";
import type { TransactionRow } from "../lib/types";

export type SocketStatus = "connecting" | "connected" | "disconnected";

const WS_URL = "ws://localhost:8000/ws/alerts";
const MAX_BACKOFF_MS = 10_000;

export function useAlertSocket(onAlert: (transaction: TransactionRow) => void): SocketStatus {
  const [status, setStatus] = useState<SocketStatus>("connecting");
  const onAlertRef = useRef(onAlert);
  onAlertRef.current = onAlert;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let backoffMs = 1000;
    let cancelled = false;

    function connect() {
      setStatus("connecting");
      socket = new WebSocket(WS_URL);

      socket.onopen = () => {
        backoffMs = 1000;
        setStatus("connected");
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "new_alert") {
          onAlertRef.current(message.transaction as TransactionRow);
        }
      };

      socket.onclose = () => {
        if (cancelled) return;
        setStatus("disconnected");
        reconnectTimer = setTimeout(connect, backoffMs);
        backoffMs = Math.min(backoffMs * 2, MAX_BACKOFF_MS);
      };

      socket.onerror = () => {
        socket?.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  return status;
}
