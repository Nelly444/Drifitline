import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { getMerchantColor } from "../lib/merchantColors";
import type { BreakdownEntry } from "../lib/types";

function formatAmount(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

export function SpendBreakdownChart({ data }: { data: BreakdownEntry[] }) {
  const total = data.reduce((sum, entry) => sum + entry.amount, 0);

  return (
    <div className="rounded-card border border-hairline bg-surface p-6">
      <p className="text-body-sm font-sans text-slate">Spend by merchant</p>
      <div className="mt-4 flex items-center gap-6">
        <div className="h-48 w-48 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="amount" nameKey="merchant_name" innerRadius={55} outerRadius={80} paddingAngle={2}>
                {data.map((entry) => (
                  <Cell
                    key={entry.merchant_name}
                    fill={entry.merchant_name === "Other" ? "#9298a3" : getMerchantColor(entry.merchant_name)}
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="flex-1 space-y-3">
          {data.map((entry) => (
            <div key={entry.merchant_name} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: entry.merchant_name === "Other" ? "#9298a3" : getMerchantColor(entry.merchant_name) }}
                />
                <span className="text-body-sm font-sans text-ink">{entry.merchant_name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-data-sm text-slate">{formatAmount(entry.amount)}</span>
                <span className="w-10 text-right font-mono text-caption text-fog">
                  {total > 0 ? Math.round((entry.amount / total) * 100) : 0}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
