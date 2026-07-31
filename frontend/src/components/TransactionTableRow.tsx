import type { TransactionRow } from "../lib/types";

function formatAmount(amount: number): string {
  return amount < 0 ? `-$${Math.abs(amount).toFixed(2)}` : `$${amount.toFixed(2)}`;
}

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export function TransactionTableRow({ transaction }: { transaction: TransactionRow }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-hairline py-3 last:border-b-0">
      <span className="flex-1 text-body-sm font-sans text-ink">{transaction.merchant_name}</span>
      <span className="w-28 shrink-0 text-right font-mono text-data-sm text-slate">
        {formatDate(transaction.posted_date)}
      </span>
      <span className="w-24 shrink-0 text-right font-mono text-data-sm text-ink">
        {formatAmount(transaction.amount)}
      </span>
    </div>
  );
}
