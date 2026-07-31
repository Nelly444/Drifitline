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
    <div className="rounded-card border border-hairline bg-surface p-6">
      <h2 className="text-heading-sm font-serif font-medium text-ink">Transaction history</h2>
      <div className="mt-4">
        {transactions.map((txn) => (
          <TransactionTableRow key={txn.id} transaction={txn} />
        ))}
      </div>
    </div>
  );
}
