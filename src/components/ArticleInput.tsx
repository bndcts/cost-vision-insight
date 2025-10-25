import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Upload, Sparkles } from "lucide-react";

interface ArticleInputProps {
  onAnalyze: (data: ArticleData) => void;
}

export interface ArticleData {
  name: string;
  specification: string;
  description: string;
  image: string | null;
}

export const ArticleInput = ({ onAnalyze }: ArticleInputProps) => {
  const [formData, setFormData] = useState<ArticleData>({
    name: "",
    specification: "",
    description: "",
    image: null,
  });
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        setImagePreview(result);
        setFormData({ ...formData, image: result });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(formData);
  };

  return (
    <Card className="p-8 shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="name" className="text-base font-semibold">
            Article Name
          </Label>
          <Input
            id="name"
            placeholder="e.g., Precision Steel Bearing Housing"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            className="text-base"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="specification" className="text-base font-semibold">
            Specification
          </Label>
          <Input
            id="specification"
            placeholder="e.g., ISO 9001 Certified, 316L Stainless Steel"
            value={formData.specification}
            onChange={(e) => setFormData({ ...formData, specification: e.target.value })}
            required
            className="text-base"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description" className="text-base font-semibold">
            Description
          </Label>
          <Textarea
            id="description"
            placeholder="Detailed description of the article, including dimensions, materials, and manufacturing requirements..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            required
            className="min-h-32 text-base"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="image" className="text-base font-semibold">
            Technical Drawing / Image
          </Label>
          <div className="flex items-center gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => document.getElementById("image")?.click()}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload Image
            </Button>
            <input
              id="image"
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
            {imagePreview && (
              <span className="text-sm text-muted-foreground">Image uploaded</span>
            )}
          </div>
          {imagePreview && (
            <div className="mt-4 border rounded-lg overflow-hidden">
              <img
                src={imagePreview}
                alt="Preview"
                className="w-full h-48 object-contain bg-muted"
              />
            </div>
          )}
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
