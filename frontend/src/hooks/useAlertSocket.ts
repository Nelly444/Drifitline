import { useEffect, useRef, useState } from "react";
import { triggerUnauthorized } from "../lib/api";
import { WS_URL } from "../lib/config";
import type { TransactionRow } from "../lib/types";

export type SocketStatus = "connecting" | "connected" | "disconnected";

const MAX_BACKOFF_MS = 10_000;
const AUTH_FAILURE_CLOSE_CODE = 1008;

export function useAlertSocket(token: string | null, onAlert: (transaction: TransactionRow) => void): SocketStatus {
  const [status, setStatus] = useState<SocketStatus>("connecting");
  const onAlertRef = useRef(onAlert);
  onAlertRef.current = onAlert;

  useEffect(() => {
    if (!token) {
      setStatus("disconnected");
      return;
    }

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let backoffMs = 1000;
    let cancelled = false;

    function connect() {
      setStatus("connecting");
      socket = new WebSocket(`${WS_URL}/ws/alerts`);

      socket.onopen = () => {
        backoffMs = 1000;
        socket?.send(JSON.stringify({ token }));
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "connected") {
          setStatus("connected");
        } else if (message.type === "new_alert") {
          onAlertRef.current(message.transaction as TransactionRow);
        }
      };

      socket.onclose = (event) => {
        if (cancelled) return;
        setStatus("disconnected");
        if (event.code === AUTH_FAILURE_CLOSE_CODE) {
          triggerUnauthorized();
          return;
        }
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
  }, [token]);

  return status;
}
