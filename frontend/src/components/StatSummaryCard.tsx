import { Line, LineChart, ResponsiveContainer } from "recharts";
import type { SparklinePoint } from "../lib/types";

interface StatSummaryCardProps {
  label: string;
  value: string;
  sparkline?: SparklinePoint[];
}

export function StatSummaryCard({ label, value, sparkline }: StatSummaryCardProps) {
  return (
    <div className="rounded-card border border-hairline bg-surface p-6">
      <p className="text-body-sm font-sans text-slate">{label}</p>
      <div className="mt-2 flex items-end justify-between gap-4">
        <p className="font-mono text-data-lg text-ink">{value}</p>
        {sparkline && sparkline.length > 1 && (
          <div className="h-10 w-24">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sparkline}>
                <Line type="monotone" dataKey="amount" stroke="#1e4fd8" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
