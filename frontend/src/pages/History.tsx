import { useEffect, useState } from "react";
import { TransactionTableRow } from "../components/TransactionTableRow";
import { fetchTransactions } from "../lib/api";
import type { TransactionRow } from "../lib/types";

export function History() {
  const [transactions, setTransactions] = useState<TransactionRow[] | null>(null);

  useEffect(() => {
    fetchTransactions(false).then(setTransactions);
  }, []);

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
