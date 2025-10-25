import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useArticleIndicesValues } from "@/lib/api";

interface PriceTrendChartProps {
  articleId: number | null;
}

interface ChartDataPoint {
  date: string;
  [key: string]: number | string;
}

const CHART_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

export const PriceTrendChart = ({ articleId }: PriceTrendChartProps) => {
  const { data, isLoading, error } = useArticleIndicesValues(articleId);

  const { chartData, indexNames } = useMemo(() => {
    if (!data || !data.indices || data.indices.length === 0) {
      return { chartData: [], indexNames: [] };
    }

    // Transform data for recharts
    const dateMap: Record<string, ChartDataPoint> = {};

    data.indices.forEach((index) => {
      index.values.forEach((point) => {
        if (!dateMap[point.date]) {
          dateMap[point.date] = { date: point.date };
        }
        dateMap[point.date][index.index_name] = point.value;
      });
    });

    // Convert to array and sort by date
    const transformedData = Object.values(dateMap).sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    // Format dates for display
    const formattedData = transformedData.map((item) => ({
      ...item,
      date: new Date(item.date).toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      }),
    }));

    return {
      chartData: formattedData,
      indexNames: data.indices.map((idx) => idx.index_name),
    };
  }, [data]);

  if (!articleId) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Price Trend Analysis</h3>
        <p className="text-sm text-muted-foreground">
          Select or create an article to view price trends
        </p>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Price Trend Analysis</h3>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </Card>
    );
  }

  if (error || chartData.length === 0) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Price Trend Analysis</h3>
        <p className="text-sm text-muted-foreground">
          {error ? "Failed to load price trend data" : "No data available"}
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-6">Price Trend Analysis</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Historical price trends for materials used in this article
      </p>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="date"
              stroke="hsl(var(--foreground))"
              style={{ fontSize: "12px" }}
            />
            <YAxis
              stroke="hsl(var(--foreground))"
              style={{ fontSize: "12px" }}
              label={{
                value: "Price (€)",
                angle: -90,
                position: "insideLeft",
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Legend />
            {indexNames.map((indexName, idx) => (
              <Line
                key={indexName}
                type="monotone"
                dataKey={indexName}
                stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                strokeWidth={2}
                name={indexName}
                dot={{ r: 3 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
