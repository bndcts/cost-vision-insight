import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { AlertCircle } from "lucide-react";

interface LoadingOverlayProps {
  articleId: number;
  onComplete: () => void;
  onError: (error: string) => void;
}

interface ArticleStatus {
  id: number;
  processing_status: "pending" | "processing" | "completed" | "failed";
  processing_error: string | null;
  processing_started_at: string | null;
  processing_completed_at: string | null;
}

export const LoadingOverlay = ({
  articleId,
  onComplete,
  onError,
}: LoadingOverlayProps) => {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState(
    "Extracting product weight from specification..."
  );
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const EXPECTED_DURATION_MS = 60000; // 60 seconds expected
    let completed = false;

    // Update elapsed time and progress based on expected duration
    const timeInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const elapsedSeconds = Math.floor(elapsed / 1000);
      setElapsedTime(elapsedSeconds);

      if (!completed) {
        // Progress fills up smoothly over 60 seconds, caps at 95% until completion
        const timeBasedProgress = Math.min(
          95,
          (elapsed / EXPECTED_DURATION_MS) * 100
        );
        setProgress(timeBasedProgress);
      }
    }, 500);

    // Poll backend for actual status
    const pollStatus = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/articles/${articleId}/status`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch status: ${response.status}`);
        }

        const status: ArticleStatus = await response.json();
        console.log("Article status:", status);

        // Update stage based on status
        if (status.processing_status === "processing") {
          const elapsed = Date.now() - startTime;
          const currentSeconds = Math.floor(elapsed / 1000);
          const messages = [
            "Uploading file to OpenAI...",
            "Analyzing material composition...",
            "Extracting product weight...",
            "Identifying cost indices...",
            "Finalizing analysis...",
          ];
          const messageIndex =
            Math.floor(currentSeconds / 10) % messages.length;
          setStage(messages[messageIndex]);
        }

        if (status.processing_status === "completed") {
          completed = true;
          clearInterval(pollInterval);
          clearInterval(timeInterval);
          setProgress(100);
          setStage("Analysis complete!");
          setTimeout(() => onComplete(), 500);
        } else if (status.processing_status === "failed") {
          clearInterval(pollInterval);
          clearInterval(timeInterval);
          const errorMessage =
            status.processing_error || "Unknown error occurred";
          onError(errorMessage);
        }
      } catch (error) {
        console.error("Error polling status:", error);
      }
    };

    pollStatus();
    const pollInterval = setInterval(pollStatus, 2000);

    return () => {
      clearInterval(pollInterval);
      clearInterval(timeInterval);
    };
  }, [articleId, onComplete, onError]);

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <Card className="p-8 max-w-md w-full space-y-6 shadow-2xl">
        <div className="space-y-2 text-center">
          <h3 className="text-2xl font-bold">Processing Analysis</h3>
          <p className="text-muted-foreground">{stage}</p>
        </div>

        <div className="space-y-2">
          <Progress value={progress} className="h-3" />
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>{Math.round(progress)}%</span>
            <span>{elapsedTime}s elapsed</span>
          </div>
        </div>

        <div className="flex justify-center">
          <div className="flex gap-2">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="w-3 h-3 rounded-full bg-primary animate-pulse"
                style={{
                  animationDelay: `${i * 0.15}s`,
                }}
              />
            ))}
          </div>
        </div>

        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            Analyzing your product specification with AI...
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            This typically takes about 1 minute
          </p>
        </div>
      </Card>
    </div>
  );
};
