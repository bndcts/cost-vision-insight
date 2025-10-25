import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";

interface IndexData {
  name: string;
  currentValue: number;
  change: number;
  changePercent: number;
}

interface IndicesTableProps {
  indices: IndexData[];
}

export const IndicesTable = ({ indices }: IndicesTableProps) => {
  const getChangeIcon = (change: number) => {
    if (change > 0) return <ArrowUp className="h-4 w-4 text-success" />;
    if (change < 0) return <ArrowDown className="h-4 w-4 text-destructive" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return "text-success";
    if (change < 0) return "text-destructive";
    return "text-muted-foreground";
  };

  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-6">Current Market Indices</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Real-time pricing indices for key materials and commodities
      </p>
      
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="font-semibold">Index Name</TableHead>
            <TableHead className="text-right font-semibold">Current Value</TableHead>
            <TableHead className="text-right font-semibold">Change</TableHead>
            <TableHead className="text-right font-semibold">% Change</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {indices.map((index) => (
            <TableRow key={index.name}>
              <TableCell className="font-medium">{index.name}</TableCell>
              <TableCell className="text-right font-mono">
                {index.currentValue.toFixed(2)}
              </TableCell>
              <TableCell className={`text-right ${getChangeColor(index.change)}`}>
                <div className="flex items-center justify-end gap-1">
                  {getChangeIcon(index.change)}
                  <span className="font-mono">{Math.abs(index.change).toFixed(2)}</span>
                </div>
              </TableCell>
              <TableCell className={`text-right font-semibold ${getChangeColor(index.change)}`}>
                {index.changePercent > 0 ? "+" : ""}
                {index.changePercent.toFixed(2)}%
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
};
