import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS, CHART_GRID, CHART_TEXT } from "../../lib/chartColors";
import type { CategoryStat, PopularBook } from "./api";

const axisProps = { stroke: CHART_TEXT, fontSize: 12 };

function shorten(text: string, max = 22): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

export function PopularBooksChart({ data }: { data: PopularBook[] }) {
  const rows = data.map((b) => ({ name: shorten(b.title), full: b.title, count: b.loan_count }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(160, rows.length * 34)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid stroke={CHART_GRID} strokeOpacity={0.4} horizontal={false} />
        <XAxis type="number" allowDecimals={false} {...axisProps} />
        <YAxis type="category" dataKey="name" width={150} {...axisProps} />
        <Tooltip
          formatter={(value) => [value, "Ödünç"]}
          labelFormatter={(_, payload) => payload?.[0]?.payload.full ?? ""}
        />
        <Bar dataKey="count" name="Ödünç" fill={CHART_COLORS[0]} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CategoryChart({ data }: { data: CategoryStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ left: 0, right: 16 }}>
        <CartesianGrid stroke={CHART_GRID} strokeOpacity={0.4} vertical={false} />
        <XAxis
          dataKey="name"
          {...axisProps}
          interval={0}
          angle={-30}
          textAnchor="end"
          height={60}
        />
        <YAxis allowDecimals={false} {...axisProps} />
        <Tooltip />
        <Legend />
        <Bar dataKey="book_count" name="Kitap" fill={CHART_COLORS[0]} />
        <Bar dataKey="copy_count" name="Nüsha" fill={CHART_COLORS[1]} />
        <Bar dataKey="loan_count" name="Ödünç" fill={CHART_COLORS[2]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
