import { useState } from "react";
import { ArticleInput, ArticleData } from "@/components/ArticleInput";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { CostBreakdown } from "@/components/CostBreakdown";
import { PriceTrendChart } from "@/components/PriceTrendChart";
import { IndicesTable } from "@/components/IndicesTable";
import { SimilarArticles } from "@/components/SimilarArticles";
import { Model3DViewer } from "@/components/Model3DViewer";
import { BarChart3 } from "lucide-react";

const Index = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [articleData, setArticleData] = useState<ArticleData | null>(null);

  const handleAnalyze = (data: ArticleData) => {
    setArticleData(data);
    setIsAnalyzing(true);
  };

  const handleAnalysisComplete = () => {
    setIsAnalyzing(false);
    setShowResults(true);
  };

  // Mock data for demonstration
  const mockCostData = {
    materials: 245.50,
    labor: 125.75,
    overhead: 85.25,
    profit: 43.50,
  };

  const mockTotalCost = Object.values(mockCostData).reduce((a, b) => a + b, 0);

  const mockPriceTrend = [
    { month: "Jan", articlePrice: 100, steelIndex: 100, laborIndex: 100, energyIndex: 100 },
    { month: "Feb", articlePrice: 103, steelIndex: 105, laborIndex: 102, energyIndex: 98 },
    { month: "Mar", articlePrice: 108, steelIndex: 112, laborIndex: 103, energyIndex: 103 },
    { month: "Apr", articlePrice: 106, steelIndex: 110, laborIndex: 104, energyIndex: 107 },
    { month: "May", articlePrice: 112, steelIndex: 118, laborIndex: 105, energyIndex: 110 },
    { month: "Jun", articlePrice: 115, steelIndex: 120, laborIndex: 106, energyIndex: 108 },
  ];

  const mockIndices = [
    { name: "Steel Price Index", currentValue: 120.45, change: 2.15, changePercent: 1.82 },
    { name: "Aluminum Index", currentValue: 98.32, change: -1.23, changePercent: -1.24 },
    { name: "Labor Cost Index", currentValue: 106.78, change: 0.45, changePercent: 0.42 },
    { name: "Energy Price Index", currentValue: 108.90, change: -2.34, changePercent: -2.10 },
    { name: "Manufacturing PMI", currentValue: 52.15, change: 1.05, changePercent: 2.05 },
  ];

  const mockSimilarArticles = [
    {
      id: "1",
      name: "Steel Bearing Housing Type A",
      category: "Mechanical Parts",
      similarity: 94,
      costEstimate: 485.20,
    },
    {
      id: "2",
      name: "Precision Machined Flange",
      category: "Industrial Components",
      similarity: 87,
      costEstimate: 512.50,
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
      <header className="border-b bg-card shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <BarChart3 className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Should Cost Analysis Tool</h1>
              <p className="text-muted-foreground">
                AI-powered cost modeling and price intelligence platform
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Input Section */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Article Analysis</h2>
            <p className="text-muted-foreground">
              Enter your article details to generate a comprehensive cost breakdown and market analysis
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
                  <span className="font-semibold text-foreground">{articleData?.name}</span>
                </p>
              </div>

              {/* Cost Breakdown and 3D Model */}
              <div className="grid lg:grid-cols-2 gap-8">
                <CostBreakdown data={mockCostData} totalCost={mockTotalCost} />
                <Model3DViewer />
              </div>

              {/* Price Trend Chart */}
              <PriceTrendChart data={mockPriceTrend} />

              {/* Indices Table */}
              <IndicesTable indices={mockIndices} />

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
