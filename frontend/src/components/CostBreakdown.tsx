import { Card } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

export interface CostData {
  materials: number;
  labor: number;
  overhead: number;
  profit: number;
}

interface CostBreakdownProps {
  data: CostData;
  totalCost: number;
}

export const CostBreakdown = ({ data, totalCost }: CostBreakdownProps) => {
  const chartData = [
    { name: "Raw Materials", value: data.materials, color: "hsl(var(--chart-1))" },
    { name: "Labor", value: data.labor, color: "hsl(var(--chart-2))" },
    { name: "Overhead", value: data.overhead, color: "hsl(var(--chart-3))" },
    { name: "Profit Margin", value: data.profit, color: "hsl(var(--chart-4))" },
  ];

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
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-4">
          <div className="flex justify-between items-center p-4 bg-muted rounded-lg">
            <span className="font-semibold">Total Cost</span>
            <span className="text-2xl font-bold text-primary">${totalCost.toFixed(2)}</span>
          </div>
          
          {chartData.map((item) => (
            <div key={item.name} className="flex justify-between items-center p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm font-medium">{item.name}</span>
              </div>
              <span className="font-semibold">${item.value.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
