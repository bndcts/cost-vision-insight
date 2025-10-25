import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface LoadingOverlayProps {
  onComplete: () => void;
}

export const LoadingOverlay = ({ onComplete }: LoadingOverlayProps) => {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("Analyzing article specifications...");

  useEffect(() => {
    const stages = [
      { text: "Analyzing article specifications...", duration: 1000 },
      { text: "Identifying raw materials...", duration: 1200 },
      { text: "Calculating labor costs...", duration: 1000 },
      { text: "Fetching market indices...", duration: 800 },
      { text: "Generating cost model...", duration: 1000 },
      { text: "Finalizing analysis...", duration: 500 },
    ];

    let currentProgress = 0;
    let stageIndex = 0;

    const interval = setInterval(() => {
      if (currentProgress >= 100) {
        clearInterval(interval);
        setTimeout(onComplete, 500);
        return;
      }

      currentProgress += 2;
      setProgress(currentProgress);

      const targetProgress = ((stageIndex + 1) / stages.length) * 100;
      if (currentProgress >= targetProgress && stageIndex < stages.length - 1) {
        stageIndex++;
        setStage(stages[stageIndex].text);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <Card className="p-8 max-w-md w-full space-y-6 shadow-2xl">
        <div className="space-y-2 text-center">
          <h3 className="text-2xl font-bold">Processing Analysis</h3>
          <p className="text-muted-foreground">{stage}</p>
        </div>
        
        <div className="space-y-2">
          <Progress value={progress} className="h-3" />
          <p className="text-sm text-muted-foreground text-right">{Math.round(progress)}%</p>
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
      </Card>
    </div>
  );
};
