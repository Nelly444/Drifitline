import type { SubscriptionSummary } from "../lib/types";

const UPCOMING_WINDOW_DAYS = 30;

function formatAmount(amount: number): string {
  return amount < 0 ? `-$${Math.abs(amount).toFixed(2)}` : `$${amount.toFixed(2)}`;
}

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function UpcomingChargesCard({ subscriptions }: { subscriptions: SubscriptionSummary[] }) {
  const today = new Date();
  const windowEnd = new Date(today.getTime() + UPCOMING_WINDOW_DAYS * 24 * 60 * 60 * 1000);

  const upcoming = subscriptions
    .filter((sub) => sub.forecast_date !== null && sub.forecast_amount !== null)
    .filter((sub) => {
      const date = new Date(sub.forecast_date as string);
      return date >= today && date <= windowEnd;
    })
    .sort((a, b) => (a.forecast_date as string).localeCompare(b.forecast_date as string));

  return (
    <div className="rounded-card border border-hairline bg-surface p-6">
      <p className="text-body-sm font-sans text-slate">Upcoming charges (next {UPCOMING_WINDOW_DAYS} days)</p>

      {upcoming.length === 0 ? (
        <p className="mt-4 text-body-sm font-sans text-slate">Nothing forecast in this window.</p>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          {upcoming.map((sub) => (
            <div key={sub.id} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="w-16 shrink-0 font-mono text-caption text-fog">
                  {formatDate(sub.forecast_date as string)}
                </span>
                <span className="text-body-sm font-sans text-ink">{sub.merchant_name ?? "Unknown merchant"}</span>
              </div>
              <span className="font-mono text-data-sm text-slate">{formatAmount(sub.forecast_amount as number)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
