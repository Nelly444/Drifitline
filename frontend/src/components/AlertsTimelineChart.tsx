import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AlertsTimelinePoint } from "../lib/types";

function formatWeek(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function AlertsTimelineChart({ data }: { data: AlertsTimelinePoint[] }) {
  return (
    <div className="rounded-card border border-hairline bg-surface p-6">
      <p className="text-body-sm font-sans text-slate">Alerts over time</p>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#e7e7e4" />
            <XAxis
              dataKey="week_start"
              tickFormatter={formatWeek}
              tick={{ fontFamily: "IBM Plex Mono", fontSize: 12, fill: "#9298a3" }}
              axisLine={{ stroke: "#e7e7e4" }}
              tickLine={false}
              minTickGap={20}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fontFamily: "IBM Plex Mono", fontSize: 12, fill: "#9298a3" }}
              axisLine={false}
              tickLine={false}
              width={30}
            />
            <Tooltip
              formatter={(value) => [value, "Alerts"]}
              labelFormatter={(label) => `Week of ${formatWeek(label as string)}`}
              contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12, borderRadius: 10, borderColor: "#e7e7e4" }}
            />
            <Bar dataKey="count" fill="#e5484d" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
