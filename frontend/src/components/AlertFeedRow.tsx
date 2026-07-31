import { DriftMeter } from "./DriftMeter";
import { MerchantIcon } from "./MerchantIcon";
import type { TransactionRow } from "../lib/types";

function formatAmount(amount: number): string {
  return amount < 0 ? `-$${Math.abs(amount).toFixed(2)}` : `$${amount.toFixed(2)}`;
}

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function AlertFeedRow({ transaction }: { transaction: TransactionRow }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-hairline py-3 last:border-b-0">
      <div className="flex items-center gap-3">
        <span className="w-12 shrink-0 font-mono text-caption text-fog">{formatDate(transaction.posted_date)}</span>
        <MerchantIcon merchantName={transaction.merchant_name} />
        <div>
          <p className="text-body-sm font-sans text-ink">{transaction.merchant_name}</p>
          <p className="text-caption font-sans text-slate">Charged {formatAmount(transaction.amount)}</p>
        </div>
      </div>

      <div className="w-32 shrink-0">
        <DriftMeter
          expectedAmount={transaction.expected_amount ?? transaction.amount}
          actualAmount={transaction.amount}
          deviationPct={transaction.deviation_pct}
          isDrift={transaction.is_drift}
          variant="compact"
        />
      </div>
    </div>
  );
}
