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
    let currentProgress = 0;

    // Update elapsed time every second
    const timeInterval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    // Simulate progress animation (this is just visual feedback)
    const progressInterval = setInterval(() => {
      // Progress slows down as it approaches 90% (we never reach 100% until backend confirms)
      if (currentProgress < 90) {
        const increment =
          currentProgress < 50 ? 2 : currentProgress < 70 ? 1 : 0.5;
        currentProgress = Math.min(90, currentProgress + increment);
        setProgress(currentProgress);
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
          // Alternate between different processing messages
          const messages = [
            "Extracting product weight from specification...",
            "Analyzing file content with AI...",
            "Finalizing analysis...",
          ];
          const messageIndex = Math.floor(elapsedTime / 3) % messages.length;
          setStage(messages[messageIndex]);
        }

        if (status.processing_status === "completed") {
          clearInterval(pollInterval);
          clearInterval(progressInterval);
          clearInterval(timeInterval);
          setProgress(100);
          setStage("Analysis complete!");
          setTimeout(() => onComplete(), 500);
        } else if (status.processing_status === "failed") {
          clearInterval(pollInterval);
          clearInterval(progressInterval);
          clearInterval(timeInterval);
          const errorMessage =
            status.processing_error || "Unknown error occurred";
          onError(errorMessage);
        }
      } catch (error) {
        console.error("Error polling status:", error);
        // Continue polling on network errors, but log them
      }
    };

    // Poll immediately, then every 2 seconds
    pollStatus();
    const pollInterval = setInterval(pollStatus, 2000);

    // Cleanup on unmount
    return () => {
      clearInterval(pollInterval);
      clearInterval(progressInterval);
      clearInterval(timeInterval);
    };
  }, [articleId, onComplete, onError, elapsedTime]);

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
            Calling OpenAI API to analyze your product specification...
          </p>
        </div>
      </Card>
    </div>
  );
};
