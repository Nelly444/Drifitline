import { useEffect, useState } from "react";
import { useAlertSocketContext } from "../contexts/AlertSocketContext";
import { fetchSubscriptions } from "../lib/api";

export function DriftRiskIndicator() {
  const [flagged, setFlagged] = useState<number | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const { subscribe } = useAlertSocketContext();

  async function refresh() {
    const subs = await fetchSubscriptions();
    setTotal(subs.length);
    setFlagged(subs.filter((s) => s.latest_transaction?.is_drift).length);
    return subs.length;
  }

  useEffect(() => {
    let cancelled = false;

    // The sidebar mounts as soon as the user is signed in, often before an
    // account is connected or before the scheduler's first pipeline pass has
    // populated subscriptions - poll a few times so the indicator appears as
    // soon as real data shows up instead of locking in at "no subscriptions".
    async function pollUntilPopulated(maxAttempts = 8, delayMs = 4000) {
      for (let attempt = 0; attempt < maxAttempts && !cancelled; attempt++) {
        const count = await refresh().catch(() => 0);
        if (count > 0) return;
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }

    pollUntilPopulated();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    // A live alert means real data now exists - refetch fully (not just
    // increment) so both counts stay accurate even if this fires before the
    // initial poll above has resolved.
    return subscribe(() => {
      refresh().catch(() => {});
    });
  }, [subscribe]);

  if (!total) return null;

  const pct = Math.min(100, Math.round(((flagged ?? 0) / total) * 100));

  return (
    <div className="flex flex-col gap-2">
      <p className="text-caption font-sans text-white/60">Drift risk</p>
      <div className="h-1.5 w-full rounded-pill bg-white/10">
        <div className="h-full rounded-pill bg-rust" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-caption font-sans text-white/80">
        {flagged} of {total} subscriptions flagged
      </p>
    </div>
  );
}
