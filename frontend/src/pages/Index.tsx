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
import { BarChart3 } from "lucide-react";

interface ArticleResponse {
  id: number;
  article_name: string;
  description?: string;
  product_specification_filename?: string;
  drawing_filename?: string;
  comment?: string;
  created_at: string;
}

const Index = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [articleData, setArticleData] = useState<ArticleData | null>(null);
  const [createdArticleId, setCreatedArticleId] = useState<number | null>(null);
  const [createdArticleResponse, setCreatedArticleResponse] =
    useState<ArticleResponse | null>(null);

  const handleAnalyze = async (data: ArticleData) => {
    setArticleData(data);
    setIsAnalyzing(true);

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
      console.log("Analysis result:", result);

      // Store the created article ID and response
      setCreatedArticleId(result.id);
      setCreatedArticleResponse(result);

      // Show success message with article ID
      alert(
        `✅ Article created successfully!\n\nArticle ID: ${result.id}\nName: ${
          result.article_name
        }\nCreated at: ${new Date(result.created_at).toLocaleString()}`
      );

      // Handle the response...
      handleAnalysisComplete();
    } catch (error) {
      console.error("Error analyzing article:", error);
      alert(
        `Error: ${
          error instanceof Error ? error.message : "Failed to analyze article"
        }`
      );
      setIsAnalyzing(false);
    }
  };

  const handleAnalysisComplete = () => {
    setIsAnalyzing(false);
    setShowResults(true);
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
      {isAnalyzing && <LoadingOverlay onComplete={handleAnalysisComplete} />}

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

        {/* Results Section */}
        {showResults && (
          <>
            <section className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
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

              {/* Cost Breakdown and 3D Model */}
              <div className="grid lg:grid-cols-2 gap-8">
                <CostBreakdown data={mockCostData} totalCost={mockTotalCost} />
                <Model3DViewer />
              </div>

              {/* Price Trend Chart */}
              <PriceTrendChart data={mockPriceTrend} />

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
