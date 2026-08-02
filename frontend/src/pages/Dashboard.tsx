import { useEffect, useState } from "react";
import { AlertFeedRow } from "../components/AlertFeedRow";
import { EmptyState } from "../components/EmptyState";
import { PrimaryButton } from "../components/PrimaryButton";
import { SpendBreakdownChart } from "../components/SpendBreakdownChart";
import { StatSummaryCard } from "../components/StatSummaryCard";
import { TrendChart } from "../components/TrendChart";
import { UpcomingChargesCard } from "../components/UpcomingChargesCard";
import { useAlertSocketContext } from "../contexts/AlertSocketContext";
import { connectSandboxAccount, fetchStatsBreakdown, fetchStatsSummary, fetchSubscriptions, fetchTransactions } from "../lib/api";
import type { BreakdownEntry, StatsSummary, SubscriptionSummary, TransactionRow } from "../lib/types";

export function Dashboard() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionSummary[] | null>(null);
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [breakdown, setBreakdown] = useState<BreakdownEntry[] | null>(null);
  const [alerts, setAlerts] = useState<TransactionRow[] | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const { subscribe } = useAlertSocketContext();

  function refetchAll() {
    setLoadError(null);
    Promise.all([
      fetchSubscriptions().then(setSubscriptions),
      fetchStatsSummary().then(setStats),
      fetchStatsBreakdown().then(setBreakdown),
      fetchTransactions(true).then(setAlerts),
    ]).catch(() => {
      setLoadError("Couldn't load your dashboard. Check your connection and try again.");
    });
  }

  useEffect(() => {
    refetchAll();
  }, []);

  async function handleConnect() {
    setConnecting(true);
    setConnectError(null);
    try {
      await connectSandboxAccount();
      // Plaid's sandbox data isn't always ready the instant an item is linked,
      // so the very first sync/cluster/forecast pass right after connecting can
      // legitimately come back empty - the background scheduler retries this
      // tenant automatically, so poll until subscriptions actually show up
      // instead of leaving the user stuck on "Connecting..." forever.
      await waitForSubscriptions();
    } catch {
      setConnectError("Couldn't connect your account. Please try again.");
    } finally {
      setConnecting(false);
    }
  }

  async function waitForSubscriptions(maxAttempts = 15, delayMs = 3000) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const subs = await fetchSubscriptions();
      if (subs.length > 0) {
        refetchAll();
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    // Didn't show up within the poll window - the scheduler will still pick it
    // up in the background, and a manual refresh will pick up the result.
    refetchAll();
  }

  useEffect(() => {
    return subscribe((txn) => {
      setAlerts((prev) => (prev?.some((a) => a.id === txn.id) ? prev : [txn, ...(prev ?? [])]));
      setStats((prev) => (prev ? { ...prev, flagged_this_month_count: prev.flagged_this_month_count + 1 } : prev));
    });
  }, [subscribe]);

  if (loadError) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-body font-sans text-rust">{loadError}</p>
        <PrimaryButton onClick={refetchAll}>Try again</PrimaryButton>
      </div>
    );
  }

  if (subscriptions === null || stats === null || breakdown === null || alerts === null) {
    return null;
  }

  if (subscriptions.length === 0) {
    return <EmptyState onConnect={handleConnect} connecting={connecting} error={connectError} />;
  }

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-heading font-serif font-medium text-ink">Dashboard</h1>
        <p className="mt-1 text-body-sm font-sans text-slate">
          An overview of your spend, upcoming charges, and recent activity.
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

      <UpcomingChargesCard subscriptions={subscriptions} />

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
