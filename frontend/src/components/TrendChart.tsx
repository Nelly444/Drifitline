import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SparklinePoint } from "../lib/types";

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function TrendChart({ data }: { data: SparklinePoint[] }) {
  return (
    <div className="rounded-card border border-hairline bg-surface p-6">
      <p className="text-body-sm font-sans text-slate">Spend over time</p>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1e4fd8" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#1e4fd8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="#e7e7e4" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fontFamily: "IBM Plex Mono", fontSize: 12, fill: "#9298a3" }}
              axisLine={{ stroke: "#e7e7e4" }}
              tickLine={false}
              minTickGap={40}
            />
            <YAxis
              tickFormatter={(value) => `$${value}`}
              tick={{ fontFamily: "IBM Plex Mono", fontSize: 12, fill: "#9298a3" }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            <Tooltip
              formatter={(value) => [`$${Number(value).toFixed(2)}`, "Spend"]}
              labelFormatter={(label) => formatDate(label as string)}
              contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12, borderRadius: 10, borderColor: "#e7e7e4" }}
            />
            <Area type="monotone" dataKey="amount" stroke="#1e4fd8" strokeWidth={2} fill="url(#trendFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
