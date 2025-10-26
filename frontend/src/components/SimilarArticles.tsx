import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSimilarArticles } from "@/lib/api";
import { Package, TrendingUp, Weight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface SimilarArticlesProps {
  articleId: number | null;
}

export const SimilarArticles = ({ articleId }: SimilarArticlesProps) => {
  const { data: similarArticlesData, isLoading } =
    useSimilarArticles(articleId);

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5 text-muted-foreground" />
            <h3 className="text-xl font-semibold">Similar Articles</h3>
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 border rounded-lg">
                <Skeleton className="h-5 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2 mb-2" />
                <Skeleton className="h-4 w-1/4" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (
    !similarArticlesData ||
    similarArticlesData.similar_articles.length === 0
  ) {
    return (
      <Card className="p-6 bg-muted/20">
        <div className="flex items-start gap-4">
          <Package className="h-6 w-6 text-muted-foreground flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-xl font-semibold mb-2">Similar Articles</h3>
            <p className="text-sm text-muted-foreground">
              No similar articles found in the database yet. As more articles
              are analyzed, the system will identify products with similar
              specifications and materials.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Package className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-semibold">Similar Articles</h3>
          <Badge variant="secondary" className="ml-auto">
            {similarArticlesData.similar_articles.length} found
          </Badge>
        </div>

        <p className="text-sm text-muted-foreground">
          These articles have similar specifications and material compositions
          based on vector similarity search
        </p>

        <div className="space-y-3">
          {similarArticlesData.similar_articles.map((article) => (
            <Card
              key={article.id}
              className="p-4 hover:shadow-md transition-shadow bg-card/50 border-border/50"
            >
              <div className="space-y-3">
                {/* Article Name and ID */}
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-foreground truncate">
                      {article.article_name}
                    </h4>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Article ID: {article.id}
                    </p>
                  </div>
                  {article.cost_estimate !== null && (
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm text-muted-foreground">Est. Cost</p>
                      <p className="text-lg font-bold text-primary">
                        €{article.cost_estimate.toFixed(2)}
                      </p>
                    </div>
                  )}
                </div>

                {/* Weight */}
                {article.unit_weight !== null && (
                  <div className="flex items-center gap-2 text-sm">
                    <Weight className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Weight:</span>
                    <span className="font-medium">
                      {article.unit_weight.toFixed(2)} kg
                      <span className="text-muted-foreground ml-1">
                        ({(article.unit_weight * 1000).toFixed(0)}g)
                      </span>
                    </span>
                  </div>
                )}

                {/* Cost Components */}
                {article.cost_components.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground font-medium">
                        Material Composition:
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 ml-6">
                      {article.cost_components
                        .filter((comp) => comp.is_material)
                        .map((comp, idx) => (
                          <div
                            key={idx}
                            className="text-sm flex items-center justify-between bg-muted/30 px-2 py-1 rounded"
                          >
                            <span className="text-muted-foreground truncate mr-2">
                              {comp.index_name}
                            </span>
                            <span className="font-mono font-medium text-xs whitespace-nowrap">
                              {comp.quantity_grams.toFixed(1)}g
                            </span>
                          </div>
                        ))}
                    </div>
                    {article.cost_components.filter((comp) => !comp.is_material)
                      .length > 0 && (
                      <>
                        <p className="text-xs text-muted-foreground mt-2 ml-6">
                          Other costs:
                        </p>
                        <div className="grid grid-cols-1 gap-1 ml-6">
                          {article.cost_components
                            .filter((comp) => !comp.is_material)
                            .map((comp, idx) => (
                              <div
                                key={idx}
                                className="text-xs flex items-center justify-between bg-muted/20 px-2 py-0.5 rounded"
                              >
                                <span className="text-muted-foreground truncate">
                                  {comp.index_name}
                                </span>
                              </div>
                            ))}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </Card>
  );
};
