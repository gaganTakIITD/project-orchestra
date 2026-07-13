/**
 * JourneyStepper — horizontal progress rail shown across the client and worker
 * journeys. Purely presentational; the caller decides which stage is current.
 */
import type { JourneyStage } from "@/components/journey";

interface JourneyStepperProps {
  stages: JourneyStage[];
  currentStageId: string;
  className?: string;
}

export default function JourneyStepper({
  stages,
  currentStageId,
  className,
}: JourneyStepperProps) {
  const currentIndex = Math.max(
    0,
    stages.findIndex((s) => s.id === currentStageId)
  );

  return (
    <nav aria-label="Journey progress" className={className}>
      <ol className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-0">
        {stages.map((stage, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index === currentIndex;
          const state = isCurrent ? "current" : isComplete ? "complete" : "upcoming";

          return (
            <li
              key={stage.id}
              className="flex items-start gap-3 sm:flex-1 sm:flex-col sm:gap-0"
              aria-current={isCurrent ? "step" : undefined}
            >
              <div className="flex items-center gap-3 sm:w-full">
                <span
                  className={
                    "flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border text-xs font-semibold transition-colors " +
                    (state === "complete"
                      ? "border-primary bg-primary text-primary-foreground"
                      : state === "current"
                        ? "border-primary bg-background text-primary ring-2 ring-primary/30"
                        : "border-border bg-background text-muted-foreground")
                  }
                >
                  {isComplete ? (
                    <svg
                      viewBox="0 0 16 16"
                      className="h-3.5 w-3.5"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M3.5 8.5l3 3 6-7"
                        stroke="currentColor"
                        strokeWidth="1.75"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : (
                    index + 1
                  )}
                </span>

                {/* Connector line (between steps, horizontal layout only) */}
                {index < stages.length - 1 ? (
                  <span
                    aria-hidden="true"
                    className={
                      "hidden h-px flex-1 sm:block " +
                      (isComplete ? "bg-primary" : "bg-border")
                    }
                  />
                ) : null}
              </div>

              <div className="min-w-0 sm:mt-3 sm:pr-6">
                <p
                  className={
                    "text-sm font-semibold leading-tight " +
                    (state === "upcoming" ? "text-muted-foreground" : "text-foreground")
                  }
                >
                  {stage.label}
                </p>
                {stage.hint ? (
                  <p className="mt-0.5 text-xs text-muted-foreground">{stage.hint}</p>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
