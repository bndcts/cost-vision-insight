import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Upload, Sparkles, FileText, X } from "lucide-react";

interface ArticleInputProps {
  onAnalyze: (data: ArticleData) => void;
}

export interface ArticleData {
  articleName: string;
  productSpecification: File | null;
  drawing: File | null;
  description: string;
}

export const ArticleInput = ({ onAnalyze }: ArticleInputProps) => {
  const [formData, setFormData] = useState<ArticleData>({
    articleName: "",
    productSpecification: null,
    drawing: null,
    description: "",
  });

  const handleFileUpload = (
    e: React.ChangeEvent<HTMLInputElement>,
    field: "productSpecification" | "drawing"
  ) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData({ ...formData, [field]: file });
    }
  };

  const handleRemoveFile = (field: "productSpecification" | "drawing") => {
    setFormData({ ...formData, [field]: null });
    // Reset the file input
    const input = document.getElementById(field) as HTMLInputElement;
    if (input) input.value = "";
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(formData);
  };

  return (
    <Card className="p-8 shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="articleName" className="text-base font-semibold">
            Article Name
          </Label>
          <Input
            id="articleName"
            placeholder="e.g., Precision Steel Bearing Housing"
            value={formData.articleName}
            onChange={(e) =>
              setFormData({ ...formData, articleName: e.target.value })
            }
            required
            className="text-base"
          />
        </div>

        <div className="space-y-2">
          <Label
            htmlFor="productSpecification"
            className="text-base font-semibold"
          >
            Product Specification <span className="text-destructive">*</span>
          </Label>
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  document.getElementById("productSpecification")?.click()
                }
                className="flex items-center gap-2"
              >
                <Upload className="h-4 w-4" />
                Upload Document
              </Button>
              <input
                id="productSpecification"
                type="file"
                accept=".pdf,.doc,.docx,.txt,.xls,.xlsx"
                onChange={(e) => handleFileUpload(e, "productSpecification")}
                className="hidden"
                required
              />
            </div>
            {formData.productSpecification && (
              <div className="flex items-center gap-2 p-3 border rounded-lg bg-muted/50">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm flex-1 truncate">
                  {formData.productSpecification.name}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveFile("productSpecification")}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="drawing" className="text-base font-semibold">
            Drawing{" "}
            <span className="text-sm text-muted-foreground">(Optional)</span>
          </Label>
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => document.getElementById("drawing")?.click()}
                className="flex items-center gap-2"
              >
                <Upload className="h-4 w-4" />
                Upload Drawing
              </Button>
              <input
                id="drawing"
                type="file"
                accept=".pdf,.dwg,.dxf,.png,.jpg,.jpeg,.svg"
                onChange={(e) => handleFileUpload(e, "drawing")}
                className="hidden"
              />
            </div>
            {formData.drawing && (
              <div className="flex items-center gap-2 p-3 border rounded-lg bg-muted/50">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm flex-1 truncate">
                  {formData.drawing.name}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveFile("drawing")}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description" className="text-base font-semibold">
            Description{" "}
            <span className="text-sm text-muted-foreground">(Optional)</span>
          </Label>
          <Textarea
            id="description"
            placeholder="Add any additional context or special requirements..."
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            className="min-h-24 text-base"
          />
        </div>

        <Button
          type="submit"
          size="lg"
          className="w-full text-base font-semibold flex items-center gap-2"
        >
          <Sparkles className="h-5 w-5" />
          Analyze Cost Structure
        </Button>
      </form>
    </Card>
  );
};
