import { createContext, useCallback, useContext, useRef, type ReactNode } from "react";
import { useAlertSocket, type SocketStatus } from "../hooks/useAlertSocket";
import type { TransactionRow } from "../lib/types";

type Listener = (transaction: TransactionRow) => void;

interface AlertSocketContextValue {
  status: SocketStatus;
  subscribe: (listener: Listener) => () => void;
}

const AlertSocketContext = createContext<AlertSocketContextValue | null>(null);

// Shell and Dashboard both need live alerts (status indicator, alert feed) but
// should share one WebSocket connection instead of each opening their own -
// this provider owns the single connection and fans messages out to subscribers.
export function AlertSocketProvider({ token, children }: { token: string | null; children: ReactNode }) {
  const listenersRef = useRef<Set<Listener>>(new Set());

  const status = useAlertSocket(token, (transaction) => {
    listenersRef.current.forEach((listener) => listener(transaction));
  });

  const subscribe = useCallback((listener: Listener) => {
    listenersRef.current.add(listener);
    return () => listenersRef.current.delete(listener);
  }, []);

  return <AlertSocketContext.Provider value={{ status, subscribe }}>{children}</AlertSocketContext.Provider>;
}

export function useAlertSocketContext(): AlertSocketContextValue {
  const ctx = useContext(AlertSocketContext);
  if (!ctx) throw new Error("useAlertSocketContext must be used within AlertSocketProvider");
  return ctx;
}
