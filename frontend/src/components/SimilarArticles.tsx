import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface SimilarArticle {
  id: string;
  name: string;
  category: string;
  similarity: number;
  costEstimate: number;
  image?: string;
}

interface SimilarArticlesProps {
  articles: SimilarArticle[];
}

export const SimilarArticles = ({ articles }: SimilarArticlesProps) => {
  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-4">Similar Articles</h3>
      <p className="text-sm text-muted-foreground mb-6">
        Based on vector similarity analysis from our database
      </p>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {articles.map((article) => (
          <Card key={article.id} className="p-4 hover:shadow-md transition-shadow">
            <div className="aspect-video bg-muted rounded-lg mb-3 flex items-center justify-center overflow-hidden">
              {article.image ? (
                <img src={article.image} alt={article.name} className="object-cover w-full h-full" />
              ) : (
                <div className="text-muted-foreground text-sm">No Image</div>
              )}
            </div>
            
            <div className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <h4 className="font-semibold text-sm line-clamp-2">{article.name}</h4>
                <Badge variant="secondary" className="text-xs shrink-0">
                  {article.similarity}% match
                </Badge>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{article.category}</span>
                <span className="font-semibold text-primary">
                  ${article.costEstimate.toFixed(2)}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </Card>
  );
};
