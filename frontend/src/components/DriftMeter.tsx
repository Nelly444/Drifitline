interface DriftMeterProps {
  expectedAmount: number;
  actualAmount: number;
  deviationPct: number | null;
  isDrift: boolean;
  variant?: "full" | "compact";
}

const MOSS_ZONE_START = 40;
const MOSS_ZONE_END = 60;

function clampPosition(deviationPct: number): number {
  const clamped = Math.max(-50, Math.min(50, deviationPct));
  return 50 + clamped;
}

function formatAmount(amount: number): string {
  return amount < 0 ? `-$${Math.abs(amount).toFixed(2)}` : `$${amount.toFixed(2)}`;
}

export function DriftMeter({ expectedAmount, actualAmount, deviationPct, isDrift, variant = "full" }: DriftMeterProps) {
  const hasScore = deviationPct !== null;
  const position = hasScore ? clampPosition(deviationPct) : 50;
  const markerColor = !hasScore ? "bg-slate" : isDrift ? "bg-rust" : "bg-moss";
  const textColor = !hasScore ? "text-slate" : isDrift ? "text-rust" : "text-moss";

  let rustZone: { left: number; width: number } | null = null;
  if (hasScore && isDrift) {
    if (position > MOSS_ZONE_END) {
      rustZone = { left: MOSS_ZONE_END, width: position - MOSS_ZONE_END };
    } else if (position < MOSS_ZONE_START) {
      rustZone = { left: position, width: MOSS_ZONE_START - position };
    }
  }

  return (
    <div className="w-full">
      <div className="relative h-1 w-full rounded-pill bg-hairline">
        <div
          className="absolute inset-y-0 rounded-pill bg-moss-wash"
          style={{ left: `${MOSS_ZONE_START}%`, width: `${MOSS_ZONE_END - MOSS_ZONE_START}%` }}
        />
        {rustZone && (
          <div
            className="absolute inset-y-0 rounded-pill bg-rust-wash"
            style={{ left: `${rustZone.left}%`, width: `${rustZone.width}%` }}
          />
        )}
        <div
          className={`absolute top-1/2 h-3 w-3 -translate-y-1/2 -translate-x-1/2 rounded-full ${markerColor}`}
          style={{ left: `${position}%` }}
        />
      </div>

      {variant === "full" ? (
        <p className={`mt-2 font-mono text-data-sm ${textColor}`}>
          {hasScore
            ? `Expected ${formatAmount(expectedAmount)} · Actual ${formatAmount(actualAmount)} · ${deviationPct! > 0 ? "+" : ""}${deviationPct!.toFixed(0)}% over baseline`
            : "Not enough history yet"}
        </p>
      ) : (
        hasScore && (
          <p className={`mt-1 font-mono text-caption ${textColor}`}>
            {deviationPct! > 0 ? "+" : ""}
            {deviationPct!.toFixed(0)}%
          </p>
        )
      )}
    </div>
  );
}
