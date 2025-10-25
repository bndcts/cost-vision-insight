import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { useArticleIndicesValues } from "@/lib/api";

interface MaterialCompositionChartProps {
  articleId: number | null;
}

export const MaterialCompositionChart = ({
  articleId,
}: MaterialCompositionChartProps) => {
  const { data, isLoading, error } = useArticleIndicesValues(articleId);

  const chartData = useMemo(() => {
    if (!data || !data.indices || data.indices.length === 0) {
      return [];
    }

    // Calculate total weight
    const totalWeight = data.indices.reduce(
      (sum, index) => sum + index.quantity_grams,
      0
    );

    // Create radar chart data
    return data.indices.map((index) => {
      // Get just the material name (remove the unit and source info)
      const shortName = index.index_name.split("[")[0].trim();
      const percentage = (index.quantity_grams / totalWeight) * 100;

      return {
        material: shortName,
        percentage: Math.round(percentage * 10) / 10, // Round to 1 decimal
        grams: Math.round(index.quantity_grams * 10) / 10,
        fullName: index.index_name,
      };
    });
  }, [data]);

  if (!articleId) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Material Composition</h3>
        <p className="text-sm text-muted-foreground">
          Select or create an article to view material breakdown
        </p>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Material Composition</h3>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </Card>
    );
  }

  if (error || chartData.length === 0) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Material Composition</h3>
        <p className="text-sm text-muted-foreground">
          {error ? "Failed to load material data" : "No data available"}
        </p>
      </Card>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-sm mb-1">{data.fullName}</p>
          <p className="text-sm text-muted-foreground">
            {data.percentage}% ({data.grams}g)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-6">Material Composition</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Breakdown of materials by weight percentage
      </p>

      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={chartData}>
            <PolarGrid stroke="hsl(var(--border))" />
            <PolarAngleAxis
              dataKey="material"
              stroke="hsl(var(--foreground))"
              style={{ fontSize: "12px" }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              stroke="hsl(var(--foreground))"
              style={{ fontSize: "10px" }}
            />
            <Radar
              name="Weight %"
              dataKey="percentage"
              stroke="hsl(var(--chart-1))"
              fill="hsl(var(--chart-1))"
              fillOpacity={0.6}
              strokeWidth={2}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 pt-4 border-t">
        <h4 className="text-sm font-semibold mb-2">Material Breakdown:</h4>
        <div className="grid grid-cols-2 gap-2">
          {chartData.map((item, idx) => (
            <div
              key={idx}
              className="text-xs flex justify-between p-2 bg-secondary/20 rounded"
            >
              <span className="font-medium">{item.material}:</span>
              <span className="text-muted-foreground">
                {item.percentage}% ({item.grams}g)
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
