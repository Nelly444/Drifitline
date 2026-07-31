import { LinkCTA } from "./LinkCTA";

export function SystemBanner({
  message,
  actionLabel,
  onAction,
}: {
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex items-center gap-3 rounded-input bg-amber-wash px-4 py-3">
      <span aria-hidden="true" className="text-amber">
        ⚠
      </span>
      <p className="flex-1 text-body-sm font-sans text-ink">{message}</p>
      {actionLabel && <LinkCTA onClick={onAction}>{actionLabel}</LinkCTA>}
    </div>
  );
}
