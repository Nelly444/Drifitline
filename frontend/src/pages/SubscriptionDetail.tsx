import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DriftMeter } from "../components/DriftMeter";
import { PrimaryButton } from "../components/PrimaryButton";
import { SubscriptionHistoryChart } from "../components/SubscriptionHistoryChart";
import { TransactionTableRow } from "../components/TransactionTableRow";
import { fetchSubscriptionDetail } from "../lib/api";
import type { SubscriptionDetail as SubscriptionDetailData } from "../lib/types";

function formatAmount(amount: number): string {
  return amount < 0 ? `-$${Math.abs(amount).toFixed(2)}` : `$${amount.toFixed(2)}`;
}

export function SubscriptionDetail() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<SubscriptionDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!id) return;
    setError(null);
    fetchSubscriptionDetail(id)
      .then(setDetail)
      .catch(() => setError("Couldn't load this subscription. Check your connection and try again."));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-body font-sans text-rust">{error}</p>
        <PrimaryButton onClick={load}>Try again</PrimaryButton>
      </div>
    );
  }

  if (detail === null) {
    return null;
  }

  const latest = detail.transactions[detail.transactions.length - 1];

  return (
    <div className="flex flex-col gap-10">
      <div>
        <Link to="/subscriptions" className="text-body-sm font-sans text-signal-blue">
          &larr; Back to subscriptions
        </Link>
        <h1 className="mt-3 text-heading font-serif font-medium text-ink">
          {detail.merchant_name ?? "Unknown merchant"}
        </h1>
        <p className="mt-1 text-body-sm font-sans text-slate">
          {detail.forecast_amount !== null
            ? `Forecast: ${formatAmount(detail.forecast_amount)}${
                detail.forecast_date ? ` on ${new Date(detail.forecast_date).toLocaleDateString()}` : ""
              }`
            : "Not enough history yet to forecast."}
        </p>
      </div>

      {latest && (
        <div className="rounded-card border border-hairline bg-surface p-6">
          <p className="text-body-sm font-sans text-slate">Latest charge</p>
          <div className="mt-4">
            <DriftMeter
              expectedAmount={latest.expected_amount ?? latest.amount}
              actualAmount={latest.amount}
              deviationPct={latest.deviation_pct}
              isDrift={latest.is_drift}
            />
          </div>
        </div>
      )}

      <SubscriptionHistoryChart transactions={detail.transactions} />

      <div className="rounded-card border border-hairline bg-surface p-6">
        <h2 className="text-heading-sm font-serif font-medium text-ink">Transaction history</h2>
        <div className="mt-4">
          {detail.transactions
            .slice()
            .reverse()
            .map((txn) => (
              <TransactionTableRow key={txn.id} transaction={txn} />
            ))}
        </div>
      </div>
    </div>
  );
}
