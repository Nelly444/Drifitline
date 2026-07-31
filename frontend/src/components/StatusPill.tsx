export type StatusPillState = "on-track" | "drift";

const VARIANTS: Record<StatusPillState, { label: string; bg: string; text: string }> = {
  "on-track": { label: "On track", bg: "bg-moss-wash", text: "text-moss" },
  drift: { label: "Drift detected", bg: "bg-rust-wash", text: "text-rust" },
};

export function StatusPill({ state }: { state: StatusPillState }) {
  const variant = VARIANTS[state];

  return (
    <span
      className={`inline-flex items-center rounded-pill px-3 py-1 text-caption font-sans font-medium ${variant.bg} ${variant.text}`}
    >
      {variant.label}
    </span>
  );
}
