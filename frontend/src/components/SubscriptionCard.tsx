import { DriftMeter } from "./DriftMeter";
import { MerchantIcon } from "./MerchantIcon";
import { StatusPill } from "./StatusPill";
import type { SubscriptionSummary } from "../lib/types";

function formatAmount(amount: number): string {
  return amount < 0 ? `-$${Math.abs(amount).toFixed(2)}` : `$${amount.toFixed(2)}`;
}

export function SubscriptionCard({ subscription }: { subscription: SubscriptionSummary }) {
  const merchantName = subscription.merchant_name ?? "Unknown merchant";
  const { latest_transaction: latest } = subscription;

  return (
    <div className="rounded-card border border-hairline bg-surface p-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <MerchantIcon merchantName={merchantName} />
          <span className="text-body-sm font-sans text-slate">{merchantName}</span>
        </div>
        {latest && <StatusPill state={latest.is_drift ? "drift" : "on-track"} />}
      </div>

      <p className="mt-4 font-mono text-data-lg text-ink">
        {subscription.forecast_amount !== null ? formatAmount(subscription.forecast_amount) : "—"}
      </p>

      {latest && subscription.forecast_amount !== null && (
        <div className="mt-4">
          <DriftMeter
            expectedAmount={subscription.forecast_amount}
            actualAmount={latest.amount}
            deviationPct={latest.deviation_pct}
            isDrift={latest.is_drift}
          />
        </div>
      )}
    </div>
  );
}
