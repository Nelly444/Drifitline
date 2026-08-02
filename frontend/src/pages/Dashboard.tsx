import { useEffect, useState } from "react";
import { AlertFeedRow } from "../components/AlertFeedRow";
import { EmptyState } from "../components/EmptyState";
import { SpendBreakdownChart } from "../components/SpendBreakdownChart";
import { StatSummaryCard } from "../components/StatSummaryCard";
import { SubscriptionCard } from "../components/SubscriptionCard";
import { TrendChart } from "../components/TrendChart";
import { fetchStatsBreakdown, fetchStatsSummary, fetchSubscriptions, fetchTransactions } from "../lib/api";
import type { BreakdownEntry, StatsSummary, SubscriptionSummary, TransactionRow } from "../lib/types";

export function Dashboard() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionSummary[] | null>(null);
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [breakdown, setBreakdown] = useState<BreakdownEntry[] | null>(null);
  const [alerts, setAlerts] = useState<TransactionRow[] | null>(null);

  useEffect(() => {
    fetchSubscriptions().then(setSubscriptions);
    fetchStatsSummary().then(setStats);
    fetchStatsBreakdown().then(setBreakdown);
    fetchTransactions(true).then(setAlerts);
  }, []);

  if (subscriptions === null || stats === null || breakdown === null || alerts === null) {
    return null;
  }

  if (subscriptions.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-heading font-serif font-medium text-ink">Dashboard</h1>
        <p className="mt-1 text-body-sm font-sans text-slate">
          Your recurring subscriptions and recent activity.
        </p>
      </div>

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
        <TrendChart data={stats.sparkline} />
        <SpendBreakdownChart data={breakdown} />
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
