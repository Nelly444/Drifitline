import { useEffect, useState } from "react";
import { AlertFeedRow } from "../components/AlertFeedRow";
import { PrimaryButton } from "../components/PrimaryButton";
import { useAlertSocketContext } from "../contexts/AlertSocketContext";
import { fetchTransactions } from "../lib/api";
import type { TransactionRow } from "../lib/types";

export function Alerts() {
  const [alerts, setAlerts] = useState<TransactionRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { subscribe } = useAlertSocketContext();

  function load() {
    setError(null);
    fetchTransactions(true)
      .then(setAlerts)
      .catch(() => setError("Couldn't load alerts. Check your connection and try again."));
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    return subscribe((txn) => {
      setAlerts((prev) => (prev?.some((a) => a.id === txn.id) ? prev : [txn, ...(prev ?? [])]));
    });
  }, [subscribe]);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-body font-sans text-rust">{error}</p>
        <PrimaryButton onClick={load}>Try again</PrimaryButton>
      </div>
    );
  }

  if (alerts === null) return null;

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-heading font-serif font-medium text-ink">Alerts</h1>
        <p className="mt-1 text-body-sm font-sans text-slate">
          Every transaction Driftline has flagged as drift, most recent first.
        </p>
      </div>

      {alerts.length === 0 ? (
        <div className="rounded-card border border-hairline bg-surface p-6 text-center">
          <p className="text-body-sm font-sans text-slate">No drift detected yet.</p>
        </div>
      ) : (
        <div className="rounded-card border border-hairline bg-surface p-6">
          {alerts.map((txn) => (
            <AlertFeedRow key={txn.id} transaction={txn} />
          ))}
        </div>
      )}
    </div>
  );
}
