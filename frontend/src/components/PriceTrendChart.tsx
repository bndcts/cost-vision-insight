import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  useArticleIndicesValues,
  useArticlePriceHistory,
} from "@/lib/api";

interface PriceTrendChartProps {
  articleId: number | null;
}

interface ChartDataPoint {
  date: string;
  articlePrice?: number;
  rawMaterials?: number;
  laborCost?: number;
  electricityCost?: number;
}

const LABOR_INDEX_NAME = "Arbeitskosten Deutschland [€/h] (Eurostat)";
const ELECTRICITY_INDEX_NAME = "Strom [€/MWh] (Finanzen.net)";

export const PriceTrendChart = ({ articleId }: PriceTrendChartProps) => {
  const {
    data: priceHistory,
    isLoading: priceIsLoading,
    error: priceError,
  } = useArticlePriceHistory(articleId);
  const {
    data: indicesData,
    isLoading: indicesIsLoading,
    error: indicesError,
  } = useArticleIndicesValues(articleId);

  const chartData = useMemo<ChartDataPoint[]>(() => {
    if (!priceHistory && !indicesData) {
      return [];
    }

    const dateMap: Record<
      string,
      ChartDataPoint & { isoDate: string }
    > = {};

    const ensureEntry = (isoDate: string) => {
      if (!dateMap[isoDate]) {
        const label = new Date(isoDate).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        });
        dateMap[isoDate] = { isoDate, date: label };
      }
      return dateMap[isoDate];
    };

    priceHistory?.points.forEach((point) => {
      const isoDate = new Date(point.order_date).toISOString().split("T")[0];
      const entry = ensureEntry(isoDate);
      entry.articlePrice = Number(point.price);
    });

    indicesData?.indices.forEach((index) => {
      index.values.forEach((value) => {
        const isoDate = new Date(value.date).toISOString().split("T")[0];
        const entry = ensureEntry(isoDate);
        const valueNumber = Number(value.value);

        if (index.index_name === LABOR_INDEX_NAME) {
          entry.laborCost = (entry.laborCost || 0) + valueNumber;
        } else if (index.index_name === ELECTRICITY_INDEX_NAME) {
          entry.electricityCost =
            (entry.electricityCost || 0) + valueNumber;
        } else if (index.is_material) {
          entry.rawMaterials = (entry.rawMaterials || 0) + valueNumber;
        }
      });
    });

    const cutoffDate = new Date();
    cutoffDate.setFullYear(cutoffDate.getFullYear() - 3);

    const filteredEntries = Object.values(dateMap).filter(({ isoDate }) => {
      const entryDate = new Date(isoDate);
      return entryDate >= cutoffDate;
    });

    return filteredEntries
      .sort((a, b) => a.isoDate.localeCompare(b.isoDate))
      .map(({ isoDate: _iso, ...rest }) => rest);
  }, [priceHistory, indicesData]);

  const isLoading = priceIsLoading || indicesIsLoading;
  const error = priceError || indicesError;

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
          {error ? "Failed to load price data" : "No price data available"}
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-6">Price Trend Analysis</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Article price broken down against raw materials, labor, and electricity contributions
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
              yAxisId="price"
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
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="articlePrice"
              stroke="hsl(var(--chart-1))"
              strokeWidth={2}
              name="Article price"
              dot={{ r: 3 }}
            />
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="rawMaterials"
              stroke="hsl(var(--chart-2))"
              strokeWidth={2}
              name="Raw materials"
              dot={{ r: 3 }}
            />
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="laborCost"
              stroke="hsl(var(--chart-3))"
              strokeWidth={2}
              name="Labor cost"
              dot={{ r: 3 }}
            />
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="electricityCost"
              stroke="hsl(var(--chart-4))"
              strokeWidth={2}
              name="Electricity cost"
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
