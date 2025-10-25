import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ExternalLink } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { mockArticles } from "@/lib/mockData";

export const ArticlesTable = () => {
  const { data: articles, isLoading } = useQuery({
    queryKey: ["articles"],
    queryFn: async () => {
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 300));
      return mockArticles;
    },
  });

  return (
    <Card className="p-6 shadow-lg border-border/50 bg-card/50 backdrop-blur">
      <h3 className="text-xl font-bold mb-6 font-mono tracking-tight">
        Articles Database
      </h3>
      <p className="text-sm text-muted-foreground mb-4">
        Registered articles with specifications and technical drawings
      </p>

      <Table>
        <TableHeader>
          <TableRow className="border-border/50">
            <TableHead className="font-semibold text-muted-foreground">
              Name
            </TableHead>
            <TableHead className="font-semibold text-muted-foreground">
              Description
            </TableHead>
            <TableHead className="text-right font-semibold text-muted-foreground">
              Drawing
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell
                colSpan={3}
                className="text-center text-muted-foreground"
              >
                Loading articles...
              </TableCell>
            </TableRow>
          ) : articles && articles.length > 0 ? (
            articles.map((article) => (
              <TableRow key={article.id} className="border-border/50">
                <TableCell className="font-medium font-mono">
                  {article.name}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-md">
                  {article.description}
                </TableCell>
                <TableCell className="text-right">
                  {article.drawing_url ? (
                    <a
                      href={article.drawing_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-primary hover:text-primary/80 transition-colors"
                    >
                      <span className="text-sm">View</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    <span className="text-xs text-muted-foreground">N/A</span>
                  )}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell
                colSpan={3}
                className="text-center text-muted-foreground"
              >
                No articles found
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  );
};
