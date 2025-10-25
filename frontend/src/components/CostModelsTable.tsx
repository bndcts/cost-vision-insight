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

export const CostModelsTable = () => {
  const { data: costModels, isLoading } = useQuery({
    queryKey: ["cost-models"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("cost_models")
        .select(`
          *,
          articles (name),
          indices (name, unit)
        `)
        .order("created_at", { ascending: false });
      
      if (error) throw error;
      return data;
    },
  });

  return (
    <Card className="p-6 shadow-lg border-border/50 bg-card/50 backdrop-blur">
      <h3 className="text-xl font-bold mb-6 font-mono tracking-tight">Cost Model Configurations</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Index contribution factors for each article's cost calculation
      </p>
      
      <Table>
        <TableHeader>
          <TableRow className="border-border/50">
            <TableHead className="font-semibold text-muted-foreground">Article</TableHead>
            <TableHead className="font-semibold text-muted-foreground">Index</TableHead>
            <TableHead className="text-right font-semibold text-muted-foreground">Factor</TableHead>
            <TableHead className="text-right font-semibold text-muted-foreground">Contribution</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                Loading cost models...
              </TableCell>
            </TableRow>
          ) : costModels && costModels.length > 0 ? (
            costModels.map((model: any) => (
              <TableRow key={model.id} className="border-border/50">
                <TableCell className="font-medium font-mono">
                  {model.articles?.name || "Unknown"}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <span>{model.indices?.name || "Unknown"}</span>
                    {model.indices?.unit && (
                      <Badge variant="outline" className="text-xs font-mono">
                        {model.indices.unit}
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  {parseFloat(model.factor).toFixed(2)}
                </TableCell>
                <TableCell className="text-right font-semibold text-primary">
                  {(parseFloat(model.factor) * 100).toFixed(0)}%
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                No cost models found
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  );
};
