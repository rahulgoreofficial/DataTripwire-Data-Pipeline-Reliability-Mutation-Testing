/**
 * Animated SVG score ring component.
 * Renders a circular progress arc that fills based on the mutation score.
 */

interface ScoreRingProps {
  score: number | null;
  size?: number;
}

function scoreToColor(score: number): string {
  if (score >= 80) return "var(--clr-success)";
  if (score >= 50) return "var(--clr-warning)";
  return "var(--clr-danger)";
}

export function ScoreRing({ score, size = 160 }: ScoreRingProps) {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = score ?? 0;
  const offset = circumference - (pct / 100) * circumference;
  const color = score !== null ? scoreToColor(pct) : "var(--clr-text-muted)";

  return (
    <div className="score-ring-wrapper">
      <div className="score-ring" style={{ width: size, height: size }}>
        <svg width={size} height={size} aria-hidden="true">
          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--clr-bg-overlay)"
            strokeWidth="10"
          />
          {/* Score arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition: "stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1), stroke 0.4s ease",
              filter: `drop-shadow(0 0 8px ${color})`,
            }}
          />
        </svg>
        <div className="score-ring-value">
          <span className="score-ring-number" style={{ color }}>
            {score !== null ? `${Math.round(score)}` : "N/A"}
          </span>
          {score !== null && (
            <span className="score-ring-unit">%</span>
          )}
        </div>
      </div>
      <span className="score-label">Mutation Score</span>
    </div>
  );
}
