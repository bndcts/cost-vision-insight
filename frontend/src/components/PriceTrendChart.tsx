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

interface PriceTrendData {
  month: string;
  articlePrice: number;
  steelIndex: number;
  laborIndex: number;
  energyIndex: number;
}

interface PriceTrendChartProps {
  data: PriceTrendData[];
}

export const PriceTrendChart = ({ data }: PriceTrendChartProps) => {
  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-6">Price Trend Analysis</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Comparing article price movement with key material indices over the past 6 months
      </p>
      
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="month" 
              stroke="hsl(var(--foreground))"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="hsl(var(--foreground))"
              style={{ fontSize: '12px' }}
              label={{ value: 'Index (Base 100)', angle: -90, position: 'insideLeft' }}
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
              type="monotone"
              dataKey="articlePrice"
              stroke="hsl(var(--chart-1))"
              strokeWidth={3}
              name="Article Price"
              dot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="steelIndex"
              stroke="hsl(var(--chart-2))"
              strokeWidth={2}
              name="Steel Index"
              dot={{ r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="laborIndex"
              stroke="hsl(var(--chart-3))"
              strokeWidth={2}
              name="Labor Index"
              dot={{ r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="energyIndex"
              stroke="hsl(var(--chart-4))"
              strokeWidth={2}
              name="Energy Index"
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
