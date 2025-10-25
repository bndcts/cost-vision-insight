import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { Badge } from "@/components/ui/badge";

export const IndicesTable = () => {
  const { data: indices, isLoading } = useQuery({
    queryKey: ["indices"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("indices")
        .select("*")
        .order("date", { ascending: false });
      
      if (error) throw error;
      return data;
    },
  });

  return (
    <Card className="p-6 shadow-lg border-border/50 bg-card/50 backdrop-blur">
      <h3 className="text-xl font-bold mb-6 font-mono tracking-tight">Market Indices</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Real-time pricing indices for key materials and commodities
      </p>
      
      <Table>
        <TableHeader>
          <TableRow className="border-border/50">
            <TableHead className="font-semibold text-muted-foreground">Index Name</TableHead>
            <TableHead className="text-right font-semibold text-muted-foreground">Value</TableHead>
            <TableHead className="text-right font-semibold text-muted-foreground">Unit</TableHead>
            <TableHead className="text-right font-semibold text-muted-foreground">Price Factor</TableHead>
            <TableHead className="text-right font-semibold text-muted-foreground">Date</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground">
                Loading indices...
              </TableCell>
            </TableRow>
          ) : indices && indices.length > 0 ? (
            indices.map((index) => (
              <TableRow key={index.id} className="border-border/50">
                <TableCell className="font-medium font-mono">{index.name}</TableCell>
                <TableCell className="text-right font-mono text-primary font-semibold">
                  {parseFloat(String(index.value)).toFixed(2)}
                </TableCell>
                <TableCell className="text-right">
                  <Badge variant="outline" className="font-mono text-xs">
                    {index.unit}
                  </Badge>
                </TableCell>
                <TableCell className="text-right font-mono text-sm text-muted-foreground">
                  {parseFloat(String(index.price_factor)).toFixed(2)}
                </TableCell>
                <TableCell className="text-right text-xs text-muted-foreground font-mono">
                  {new Date(index.date).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground">
                No indices found
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  );
};
