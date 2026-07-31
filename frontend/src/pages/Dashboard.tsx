import { useEffect, useState } from "react";
import { AlertFeedRow } from "../components/AlertFeedRow";
import { EmptyState } from "../components/EmptyState";
import { StatSummaryCard } from "../components/StatSummaryCard";
import { SubscriptionCard } from "../components/SubscriptionCard";
import { fetchStatsSummary, fetchSubscriptions, fetchTransactions } from "../lib/api";
import type { StatsSummary, SubscriptionSummary, TransactionRow } from "../lib/types";

export function Dashboard() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionSummary[] | null>(null);
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [alerts, setAlerts] = useState<TransactionRow[] | null>(null);

  useEffect(() => {
    fetchSubscriptions().then(setSubscriptions);
    fetchStatsSummary().then(setStats);
    fetchTransactions(true).then(setAlerts);
  }, []);

  if (subscriptions === null || stats === null || alerts === null) {
    return null;
  }

  if (subscriptions.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="flex flex-col gap-10">
      <div className="grid grid-cols-3 gap-6">
        <StatSummaryCard
          label="Total monthly spend"
          value={`$${stats.total_monthly_spend.toFixed(2)}`}
          sparkline={stats.sparkline}
        />
        <StatSummaryCard label="Active subscriptions" value={String(stats.active_subscriptions_count)} />
        <StatSummaryCard label="Flagged this month" value={String(stats.flagged_this_month_count)} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {subscriptions.map((sub) => (
          <SubscriptionCard key={sub.id} subscription={sub} />
        ))}
      </div>

      {alerts.length > 0 && (
        <div className="rounded-card border border-hairline bg-surface p-6">
          <h2 className="text-heading-sm font-serif font-medium text-ink">Alerts</h2>
          <div className="mt-4">
            {alerts.map((txn) => (
              <AlertFeedRow key={txn.id} transaction={txn} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
