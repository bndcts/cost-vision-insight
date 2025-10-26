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

const SERIES_KEYS = [
  "articlePrice",
  "rawMaterials",
  "laborCost",
  "electricityCost",
] as const;
type SeriesKey = (typeof SERIES_KEYS)[number];

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

    const sortedEntries = filteredEntries
      .sort((a, b) => a.isoDate.localeCompare(b.isoDate))
      .map(({ isoDate: _iso, ...rest }) => rest);

    if (sortedEntries.length === 0) {
      return [];
    }

    const baseValues: Partial<Record<SeriesKey, number>> = {};

    sortedEntries.forEach((entry) => {
      SERIES_KEYS.forEach((key) => {
        if (
          baseValues[key] === undefined &&
          typeof entry[key] === "number"
        ) {
          baseValues[key] = entry[key];
        }
      });
    });

    const toPercentChange = (
      value?: number,
      base?: number
    ): number | undefined => {
      if (typeof value !== "number" || typeof base !== "number") {
        return undefined;
      }
      if (base === 0) {
        return undefined;
      }
      const percentage = ((value - base) / base) * 100;
      return Math.min(percentage, 100);
    };

    return sortedEntries.map((entry) => {
      const normalizedEntry: ChartDataPoint = { date: entry.date };

      SERIES_KEYS.forEach((key) => {
        const normalizedValue = toPercentChange(
          entry[key],
          baseValues[key]
        );
        if (typeof normalizedValue === "number") {
          normalizedEntry[key] = normalizedValue;
        }
      });

      return normalizedEntry;
    });
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
        Percentage change since the beginning of the time window for article price vs. index components (capped at 100%)
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
                value: "Change (%)",
                angle: -90,
                position: "insideLeft",
              }}
              domain={["auto", 100]}
              tickFormatter={(value) =>
                typeof value === "number" ? `${value.toFixed(0)}%` : value
              }
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              formatter={(
                value: number | string | Array<number | string>,
                name
              ) => {
                if (typeof value === "number") {
                  return [`${value.toFixed(2)}%`, name];
                }
                return [value, name];
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
