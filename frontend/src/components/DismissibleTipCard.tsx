import { useState } from "react";
import { LinkCTA } from "./LinkCTA";

interface DismissibleTipCardProps {
  title: string;
  body: string;
  ctaLabel?: string;
  onCtaClick?: () => void;
  onDismiss?: () => void;
}

export function DismissibleTipCard({ title, body, ctaLabel, onCtaClick, onDismiss }: DismissibleTipCardProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="relative rounded-card border border-hairline bg-surface p-6">
      <button
        aria-label="Dismiss"
        onClick={() => {
          setDismissed(true);
          onDismiss?.();
        }}
        className="absolute right-4 top-4 text-fog"
      >
        ×
      </button>

      <div className="h-8 w-8 rounded-avatar bg-signal-blue-wash flex items-center justify-center">
        <span className="h-2 w-2 rounded-full bg-signal-blue" />
      </div>

      <p className="mt-4 text-body font-sans font-semibold text-ink">{title}</p>
      <p className="mt-1 text-body-sm font-sans text-slate">{body}</p>

      {ctaLabel && (
        <div className="mt-4">
          <LinkCTA onClick={onCtaClick}>{ctaLabel}</LinkCTA>
        </div>
      )}
    </div>
  );
}
