import { CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TransactionRow } from "../lib/types";

const ACTUAL_COLOR = "#1e4fd8";
const EXPECTED_COLOR = "#9298a3";
const DRIFT_COLOR = "#e5484d";
const NORMAL_COLOR = "#0e9f6e";

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function ActualDot({ cx, cy, payload }: { cx?: number; cy?: number; payload?: TransactionRow }) {
  if (cx === undefined || cy === undefined || !payload) return null;
  return <circle cx={cx} cy={cy} r={payload.is_drift ? 5 : 3} fill={payload.is_drift ? DRIFT_COLOR : NORMAL_COLOR} />;
}

export function SubscriptionHistoryChart({ transactions }: { transactions: TransactionRow[] }) {
  return (
    <div className="rounded-card border border-hairline bg-surface p-6">
      <p className="text-body-sm font-sans text-slate">Charge history vs. forecast</p>
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={transactions} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#e7e7e4" />
            <XAxis
              dataKey="posted_date"
              tickFormatter={formatDate}
              tick={{ fontFamily: "IBM Plex Mono", fontSize: 12, fill: "#9298a3" }}
              axisLine={{ stroke: "#e7e7e4" }}
              tickLine={false}
              minTickGap={30}
            />
            <YAxis
              tickFormatter={(value) => `$${value}`}
              tick={{ fontFamily: "IBM Plex Mono", fontSize: 12, fill: "#9298a3" }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            <Tooltip
              formatter={(value, name) => [`$${Number(value).toFixed(2)}`, name === "amount" ? "Actual" : "Expected"]}
              labelFormatter={(label) => formatDate(label as string)}
              contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12, borderRadius: 10, borderColor: "#e7e7e4" }}
            />
            <Legend
              formatter={(value) => (value === "amount" ? "Actual charge" : "Forecast model's expected amount")}
              wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="expected_amount"
              stroke={EXPECTED_COLOR}
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              connectNulls
            />
            <Line type="monotone" dataKey="amount" stroke={ACTUAL_COLOR} strokeWidth={2} dot={<ActualDot />} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 flex items-center gap-4 text-caption font-mono text-slate">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: NORMAL_COLOR }} />
          On track
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: DRIFT_COLOR }} />
          Flagged as drift
        </span>
      </div>
    </div>
  );
}
