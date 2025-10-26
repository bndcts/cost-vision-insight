import { Card } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

export interface CostData {
  materials: number;
  labor: number;
  electricity: number;
  overhead: number;
  profit: number;
}

interface CostBreakdownProps {
  data: CostData | null;
  totalCost: number | null;
  currency?: string;
  isLoading?: boolean;
}

const colorRamp = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

const currencyFormatter = (currency: string) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  });

export const CostBreakdown = ({
  data,
  totalCost,
  currency = "EUR",
  isLoading = false,
}: CostBreakdownProps) => {
  const formatter = currencyFormatter(currency);
  const pieLabel = ({
    percent,
  }: {
    percent: number;
  }) => `${(percent * 100).toFixed(0)}%`;

  if (isLoading) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Cost Breakdown</h3>
        <p className="text-muted-foreground text-sm">Loading cost data...</p>
      </Card>
    );
  }

  if (!data || totalCost === null) {
    return (
      <Card className="p-6 shadow-lg">
        <h3 className="text-xl font-bold mb-6">Cost Breakdown</h3>
        <p className="text-muted-foreground text-sm">
          Run an analysis to view cost contributions for this article.
        </p>
      </Card>
    );
  }

  const chartSegments = [
    { name: "Raw Materials", rawValue: data.materials, color: colorRamp[0] },
    { name: "Labor", rawValue: data.labor, color: colorRamp[1] },
    { name: "Electricity", rawValue: data.electricity, color: colorRamp[2] },
    { name: "Overhead (15%)", rawValue: data.overhead, color: colorRamp[3] },
    { name: "Profit Margin", rawValue: data.profit, color: colorRamp[4] },
  ];

  const chartData = chartSegments.map((segment) => ({
    ...segment,
    value: Math.max(segment.rawValue, 0),
  }));

  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-6">Cost Breakdown</h3>
      
      <div className="grid md:grid-cols-2 gap-8">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={pieLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, _name, props) =>
                  formatter.format(
                    typeof props?.payload?.rawValue === "number"
                      ? props.payload.rawValue
                      : value
                  )
                }
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-4">
          <div className="flex justify-between items-center p-4 bg-muted rounded-lg">
            <span className="font-semibold">Total Cost</span>
            <span className="text-2xl font-bold text-primary">
              {formatter.format(totalCost)}
            </span>
          </div>
          
          {chartSegments.map((item) => (
            <div key={item.name} className="flex justify-between items-center p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm font-medium">{item.name}</span>
              </div>
              <span className="font-semibold">
                {formatter.format(item.rawValue)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
