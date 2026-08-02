import { useEffect, useState } from "react";
import { PrimaryButton } from "../components/PrimaryButton";
import { TransactionTableRow } from "../components/TransactionTableRow";
import { fetchTransactions } from "../lib/api";
import type { TransactionRow } from "../lib/types";

export function History() {
  const [transactions, setTransactions] = useState<TransactionRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    fetchTransactions(false)
      .then(setTransactions)
      .catch(() => setError("Couldn't load transaction history. Check your connection and try again."));
  }

  useEffect(() => {
    load();
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-body font-sans text-rust">{error}</p>
        <PrimaryButton onClick={load}>Try again</PrimaryButton>
      </div>
    );
  }

  if (transactions === null) return null;

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-heading font-serif font-medium text-ink">Transaction history</h1>
        <p className="mt-1 text-body-sm font-sans text-slate">
          Every transaction Driftline has ingested, most recent first.
        </p>
      </div>

      <div className="rounded-card border border-hairline bg-surface p-6">
        {transactions.map((txn) => (
          <TransactionTableRow key={txn.id} transaction={txn} />
        ))}
      </div>
    </div>
  );
}
