import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useArticleStatus } from "@/lib/api";

interface LoadingOverlayProps {
  articleId: number;
  onComplete: () => void;
  onError: (error: string) => void;
}

export const LoadingOverlay = ({
  articleId,
  onComplete,
  onError,
}: LoadingOverlayProps) => {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("Uploading file to OpenAI...");
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime] = useState(Date.now());

  const { data: status } = useArticleStatus(articleId);

  useEffect(() => {
    const EXPECTED_DURATION_MS = 60000; // 60 seconds expected

    const timeInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const elapsedSeconds = Math.floor(elapsed / 1000);
      setElapsedTime(elapsedSeconds);

      if (status?.processing_status !== "completed") {
        const timeBasedProgress = Math.min(
          95,
          (elapsed / EXPECTED_DURATION_MS) * 100
        );
        setProgress(timeBasedProgress);
      }
    }, 500);

    return () => clearInterval(timeInterval);
  }, [startTime, status]);

  useEffect(() => {
    if (!status) return;

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
      const messageIndex = Math.floor(currentSeconds / 10) % messages.length;
      setStage(messages[messageIndex]);
    }

    if (status.processing_status === "completed") {
      setProgress(100);
      setStage("Analysis complete!");
      setTimeout(() => onComplete(), 500);
    } else if (status.processing_status === "failed") {
      const errorMessage = status.processing_error || "Unknown error occurred";
      onError(errorMessage);
    }
  }, [status, startTime, onComplete, onError]);

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
