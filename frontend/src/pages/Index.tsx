import { useState } from "react";
import { ArticleInput, ArticleData } from "@/components/ArticleInput";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { CostBreakdown } from "@/components/CostBreakdown";
import { PriceTrendChart } from "@/components/PriceTrendChart";
import { IndicesTable } from "@/components/IndicesTable";
import { ArticlesTable } from "@/components/ArticlesTable";
import { CostModelsTable } from "@/components/CostModelsTable";
import { SimilarArticles } from "@/components/SimilarArticles";
import { Model3DViewer } from "@/components/Model3DViewer";
import { Card } from "@/components/ui/card";
import { AlertCircle, BarChart3 } from "lucide-react";
import { useArticle } from "@/lib/api";

interface ArticleResponse {
  id: number;
  article_name: string;
  description?: string;
  unit_weight?: number;
  product_specification_filename?: string;
  drawing_filename?: string;
  comment?: string;
  processing_status: string;
  processing_error?: string | null;
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
  created_at: string;
}

const Index = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [articleData, setArticleData] = useState<ArticleData | null>(null);
  const [createdArticleId, setCreatedArticleId] = useState<number | null>(null);
  const [processingError, setProcessingError] = useState<string | null>(null);

  const { data: createdArticleResponse } = useArticle(
    showResults ? createdArticleId : null
  );

  const handleAnalyze = async (data: ArticleData) => {
    setArticleData(data);
    setIsAnalyzing(true);
    setShowResults(false);
    setProcessingError(null);

    try {
      // Create FormData object
      const formData = new FormData();
      formData.append("articleName", data.articleName);

      // Append files
      if (data.productSpecification) {
        formData.append("productSpecification", data.productSpecification);
      }

      if (data.drawing) {
        formData.append("drawing", data.drawing);
      }

      // Append description if provided
      if (data.description) {
        formData.append("description", data.description);
      }

      console.log("Sending form data with:", {
        articleName: data.articleName,
        hasSpec: !!data.productSpecification,
        hasDrawing: !!data.drawing,
        description: data.description,
      });

      // Send to backend
      const response = await fetch("http://localhost:8000/api/v1/analyze/", {
        method: "POST",
        body: formData,
        // Note: DO NOT set Content-Type header - browser sets it automatically with boundary
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Unknown error" }));
        console.error("API Error:", errorData);
        throw new Error(
          errorData.detail || `Analysis failed with status ${response.status}`
        );
      }

      const result = await response.json();
      console.log("Article created:", result);

      // Store the created article ID
      setCreatedArticleId(result.id);

      // LoadingOverlay will now poll for status and call onComplete/onError
    } catch (error) {
      console.error("Error analyzing article:", error);
      setProcessingError(
        error instanceof Error ? error.message : "Failed to analyze article"
      );
      setIsAnalyzing(false);
    }
  };

  const handleAnalysisComplete = () => {
    if (!createdArticleId) return;

    setIsAnalyzing(false);
    setShowResults(true);
    setProcessingError(null);
  };

  const handleAnalysisError = (error: string) => {
    setIsAnalyzing(false);
    setShowResults(false);
    setProcessingError(error);
  };

  // Mock data for demonstration
  const mockCostData = {
    materials: 245.5,
    labor: 125.75,
    overhead: 85.25,
    profit: 43.5,
  };

  const mockTotalCost = Object.values(mockCostData).reduce((a, b) => a + b, 0);

  const mockPriceTrend = [
    {
      month: "Jan",
      articlePrice: 100,
      steelIndex: 100,
      laborIndex: 100,
      energyIndex: 100,
    },
    {
      month: "Feb",
      articlePrice: 103,
      steelIndex: 105,
      laborIndex: 102,
      energyIndex: 98,
    },
    {
      month: "Mar",
      articlePrice: 108,
      steelIndex: 112,
      laborIndex: 103,
      energyIndex: 103,
    },
    {
      month: "Apr",
      articlePrice: 106,
      steelIndex: 110,
      laborIndex: 104,
      energyIndex: 107,
    },
    {
      month: "May",
      articlePrice: 112,
      steelIndex: 118,
      laborIndex: 105,
      energyIndex: 110,
    },
    {
      month: "Jun",
      articlePrice: 115,
      steelIndex: 120,
      laborIndex: 106,
      energyIndex: 108,
    },
  ];

  const mockSimilarArticles = [
    {
      id: "1",
      name: "Steel Bearing Housing Type A",
      category: "Mechanical Parts",
      similarity: 94,
      costEstimate: 485.2,
    },
    {
      id: "2",
      name: "Precision Machined Flange",
      category: "Industrial Components",
      similarity: 87,
      costEstimate: 512.5,
    },
    {
      id: "3",
      name: "Cast Steel Housing Unit",
      category: "Mechanical Parts",
      similarity: 82,
      costEstimate: 445.75,
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {isAnalyzing && createdArticleId && (
        <LoadingOverlay
          articleId={createdArticleId}
          onComplete={handleAnalysisComplete}
          onError={handleAnalysisError}
        />
      )}

      {/* Header */}
      <header className="border-b border-border/50 bg-card/30 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-4xl font-bold tracking-tight font-mono">
            SHOULD COST ANALYSIS
          </h1>
          <p className="text-muted-foreground mt-2 font-mono text-sm">
            AI-POWERED COST ESTIMATION AND MARKET INTELLIGENCE
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Input Section */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Article Analysis</h2>
            <p className="text-muted-foreground">
              Enter your article details to generate a comprehensive cost
              breakdown and market analysis
            </p>
          </div>
          <ArticleInput onAnalyze={handleAnalyze} />
        </section>

        {/* Error Display */}
        {processingError && (
          <section className="animate-in fade-in slide-in-from-top-4 duration-500">
            <Card className="p-6 border-destructive/50 bg-destructive/5">
              <div className="flex items-start gap-4">
                <AlertCircle className="h-6 w-6 text-destructive flex-shrink-0 mt-0.5" />
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-destructive">
                    Processing Failed
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {processingError}
                  </p>
                  <p className="text-xs text-muted-foreground mt-4">
                    Please check your product specification file and try again.
                    Common issues include:
                  </p>
                  <ul className="text-xs text-muted-foreground list-disc list-inside space-y-1">
                    <li>OpenAI API key not configured or invalid</li>
                    <li>File format not supported or corrupted</li>
                    <li>Network connection issues</li>
                  </ul>
                </div>
              </div>
            </Card>
          </section>
        )}

        {/* Results Section */}
        {showResults && (
          <>
            <section className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="space-y-4">
                <div>
                  <h2 className="text-2xl font-bold mb-2">Analysis Results</h2>
                  <p className="text-muted-foreground">
                    Comprehensive cost breakdown and market intelligence for{" "}
                    <span className="font-semibold text-foreground">
                      {articleData?.articleName}
                    </span>
                    {createdArticleId && (
                      <span className="ml-2 text-sm">
                        (Article ID:{" "}
                        <span className="font-mono font-semibold text-foreground">
                          {createdArticleId}
                        </span>
                        )
                      </span>
                    )}
                  </p>
                </div>

                {/* Extracted Product Information */}
                {createdArticleResponse && (
                  <Card className="p-6 bg-primary/5 border-primary/20">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-primary" />
                      Extracted Product Information
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                          Article Name
                        </p>
                        <p className="text-lg font-semibold">
                          {createdArticleResponse.article_name}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                          Product Weight
                        </p>
                        <p className="text-lg font-semibold">
                          {createdArticleResponse.unit_weight !== undefined &&
                          createdArticleResponse.unit_weight !== null ? (
                            (() => {
                              const weightNum = Number(
                                createdArticleResponse.unit_weight
                              );
                              if (Number.isNaN(weightNum)) {
                                return (
                                  <span className="text-muted-foreground">
                                    Not found
                                  </span>
                                );
                              }
                              return (
                                <>
                                  {weightNum.toFixed(2)} kg
                                  <span className="text-sm text-muted-foreground ml-2">
                                    ({(weightNum * 1000).toFixed(0)}g)
                                  </span>
                                </>
                              );
                            })()
                          ) : (
                            <span className="text-muted-foreground">
                              Not found
                            </span>
                          )}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                          Processing Time
                        </p>
                        <p className="text-lg font-semibold">
                          {createdArticleResponse.processing_started_at &&
                          createdArticleResponse.processing_completed_at ? (
                            <>
                              {Math.round(
                                (new Date(
                                  createdArticleResponse.processing_completed_at
                                ).getTime() -
                                  new Date(
                                    createdArticleResponse.processing_started_at
                                  ).getTime()) /
                                  1000
                              )}
                              s
                            </>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </p>
                      </div>
                    </div>
                    {createdArticleResponse.description && (
                      <div className="mt-4 pt-4 border-t">
                        <p className="text-sm text-muted-foreground mb-1">
                          Description
                        </p>
                        <p className="text-sm">
                          {createdArticleResponse.description}
                        </p>
                      </div>
                    )}
                  </Card>
                )}
              </div>

              {/* Cost Breakdown and 3D Model */}
              <div className="grid lg:grid-cols-2 gap-8">
                <CostBreakdown data={mockCostData} totalCost={mockTotalCost} />
                <Model3DViewer />
              </div>

              {/* Price Trend Chart */}
              <PriceTrendChart articleId={createdArticleResponse?.id || null} />

              {/* Database Tables */}
              <div className="space-y-6">
                <IndicesTable />
                <ArticlesTable />
                <CostModelsTable />
              </div>

              {/* Similar Articles */}
              <SimilarArticles articles={mockSimilarArticles} />
            </section>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t mt-16 py-6 bg-card">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>Should Cost Analysis Tool - Powered by AI & Market Intelligence</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
