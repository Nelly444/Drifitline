import type { SocketStatus } from "../hooks/useAlertSocket";

const LABELS: Record<SocketStatus, string> = {
  connected: "Live",
  connecting: "Reconnecting…",
  disconnected: "Disconnected",
};

export function LiveStatusIndicator({ status }: { status: SocketStatus }) {
  const dotColor = status === "connected" ? "bg-white/60" : "bg-amber";

  return (
    <div className="flex items-center gap-2">
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotColor}`} />
      <span className="text-caption font-mono text-white/60">{LABELS[status]}</span>
    </div>
  );
}
