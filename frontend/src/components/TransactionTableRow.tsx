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
      <div className="flex flex-1 items-center gap-2">
        {transaction.is_drift && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-rust" />}
        <span className="text-body-sm font-sans text-ink">{transaction.merchant_name}</span>
      </div>
      <span className="w-28 shrink-0 text-right font-mono text-data-sm text-slate">
        {formatDate(transaction.posted_date)}
      </span>
      <span className={`w-24 shrink-0 text-right font-mono text-data-sm ${transaction.is_drift ? "text-rust" : "text-ink"}`}>
        {formatAmount(transaction.amount)}
      </span>
    </div>
  );
}
