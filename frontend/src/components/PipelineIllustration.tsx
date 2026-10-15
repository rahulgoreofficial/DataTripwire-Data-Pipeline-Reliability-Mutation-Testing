/**
 * PipelineIllustration component.
 *
 * An original, precision SVG visualization depicting data records traversing
 * a pipeline, showing a controlled mutation injection (signal orange branch),
 * an active or bypassed validation checkpoint, and downstream metric impact.
 *
 * Theme-aware: Dynamically adapts to Daylight and After Hours themes via CSS custom properties.
 */

interface PipelineIllustrationProps {
  mode?: "hero" | "live";
  status?: "neutral" | "survived" | "detected";
  mutationType?: string;
  hasUniquenessRule?: boolean;
}

export function PipelineIllustration({
  mode = "hero",
  status = "neutral",
  mutationType = "duplicate_row",
  hasUniquenessRule = false,
}: PipelineIllustrationProps) {
  const isDetected = status === "detected" || (mode === "hero" && hasUniquenessRule);
  const isSurvived = status === "survived" || (mode === "hero" && !hasUniquenessRule && status === "neutral");

  return (
    <div className="pipeline-illustration-wrapper" aria-label="Pipeline mutation and validation diagram">
      <div className="pipeline-illustration-header">
        <div className="pipeline-tag">
          <span className="pipeline-tag-dot" />
          <span>INSTRUMENTATION TELEMETRY // PIPELINE FLOW</span>
        </div>
        <div className="pipeline-status-badge">
          {mode === "hero" ? (
            <span className="mono-subtle">DIAGRAM // CONTROLLED FAULT INJECTION</span>
          ) : isDetected ? (
            <span className="mono-success">✓ TRIPWIRE TRIPPED // SAFEGUARD ACTIVE</span>
          ) : (
            <span className="mono-danger">⚠ SILENT ESCAPE // METRIC COMPROMISED</span>
          )}
        </div>
      </div>

      <svg
        viewBox="0 0 840 280"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="pipeline-svg"
        role="img"
        aria-label="Data flow visualization showing records flowing into a mutation fork and reaching validation boundary"
      >
        <defs>
          {/* Subtle background grid pattern */}
          <pattern id="grid-pattern" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="var(--clr-svg-grid)" strokeWidth="0.5" strokeOpacity="0.6" />
          </pattern>

          {/* Marker arrows */}
          <marker id="arrow-navy" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="var(--clr-svg-arrow)" />
          </marker>
          <marker id="arrow-orange" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="var(--clr-signal-orange)" />
          </marker>
          <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="var(--clr-success)" />
          </marker>
        </defs>

        {/* Blueprint background grid */}
        <rect width="840" height="280" fill="url(#grid-pattern)" rx="4" />
        <rect width="840" height="280" fill="none" stroke="var(--clr-svg-grid)" strokeWidth="1" rx="4" />

        {/* Coordinate / Technical crosshairs */}
        <path d="M 20 15 L 30 15 M 25 10 L 25 20" stroke="var(--clr-text-muted)" strokeWidth="0.8" />
        <text x="35" y="18" fill="var(--clr-text-muted)" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="0.05em">
          LAB-NODE // DT-0984-X
        </text>

        <path d="M 810 15 L 820 15 M 815 10 L 815 20" stroke="var(--clr-text-muted)" strokeWidth="0.8" />
        <text x="735" y="18" fill="var(--clr-text-muted)" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="0.05em">
          SYS_CLK: 100HZ
        </text>

        {/* ── STAGE 1: INGESTION STREAM (x: 40 to 180, y: 120) ──────────────── */}
        <g className="pipeline-stage" transform="translate(40, 70)">
          <rect x="0" y="0" width="130" height="100" fill="var(--clr-svg-node-bg)" stroke="var(--clr-svg-node-border)" strokeWidth="1.2" rx="2" />
          <rect x="0" y="0" width="130" height="20" fill="var(--clr-svg-header-bg)" />
          <text x="10" y="14" fill="var(--clr-svg-header-text)" fontSize="9" fontWeight="700" fontFamily="var(--font-mono)">
            01 // INGESTION
          </text>
          <text x="10" y="42" fill="var(--clr-text-primary)" fontSize="11" fontWeight="600" fontFamily="var(--font-sans)">
            Raw Pipeline
          </text>
          <text x="10" y="58" fill="var(--clr-text-secondary)" fontSize="9" fontFamily="var(--font-mono)">
            15 Transactions
          </text>
          <text x="10" y="72" fill="var(--clr-text-secondary)" fontSize="9" fontFamily="var(--font-mono)">
            ORD-101 .. ORD-115
          </text>
          <circle cx="118" cy="10" r="3" fill="var(--clr-success)" />
        </g>

        {/* Stream connector 1 to 2 */}
        <path d="M 170 120 L 230 120" stroke="var(--clr-svg-arrow)" strokeWidth="1.5" markerEnd="url(#arrow-navy)" />
        <circle cx="200" cy="120" r="3" fill="var(--clr-svg-arrow)" />
        <text x="180" y="112" fill="var(--clr-text-muted)" fontSize="8" fontFamily="var(--font-mono)">
          VALID FLOW
        </text>

        {/* ── STAGE 2: MUTATION INJECTION (x: 235 to 375, y: 70) ───────────── */}
        <g className="pipeline-stage" transform="translate(235, 70)">
          <rect x="0" y="0" width="145" height="100" fill="var(--clr-svg-node-bg)" stroke="var(--clr-signal-orange)" strokeWidth="1.5" rx="2" />
          <rect x="0" y="0" width="145" height="20" fill="var(--clr-signal-orange)" />
          <text x="8" y="14" fill="#FFFFFF" fontSize="9" fontWeight="700" fontFamily="var(--font-mono)">
            02 // MUTATION INJECTION
          </text>
          <text x="10" y="40" fill="var(--clr-text-primary)" fontSize="11" fontWeight="600" fontFamily="var(--font-sans)">
            Synthesized Fault
          </text>
          <text x="10" y="56" fill="var(--clr-signal-orange)" fontSize="9.5" fontWeight="700" fontFamily="var(--font-mono)">
            {mutationType === "duplicate_row" ? "FORK: DUPLICATE ROW" : mutationType.toUpperCase()}
          </text>
          <text x="10" y="72" fill="var(--clr-text-secondary)" fontSize="8.5" fontFamily="var(--font-mono)">
            Target: ORD-101 (₹800)
          </text>
          <text x="10" y="86" fill="var(--clr-text-muted)" fontSize="8" fontFamily="var(--font-mono)">
            Seed: Deterministic
          </text>
        </g>

        {/* Clean path continuing straight forward (y: 100) */}
        <path d="M 380 100 L 470 100" stroke="var(--clr-svg-arrow)" strokeWidth="1.5" strokeDasharray="3 3" markerEnd="url(#arrow-navy)" />
        <text x="390" y="93" fill="var(--clr-text-muted)" fontSize="8" fontFamily="var(--font-mono)">
          CLEAN TRACE (14 tx)
        </text>

        {/* Fault branch diverging downward (y: 140 to 180) */}
        <path
          d="M 380 145 C 410 145, 420 185, 470 185"
          stroke="var(--clr-signal-orange)"
          strokeWidth="2"
          markerEnd="url(#arrow-orange)"
        />
        {/* Animated pulse dot along the fault branch */}
        <circle cx="430" cy="168" r="4" fill="var(--clr-signal-orange)">
          <animate
            attributeName="opacity"
            values="0.4;1;0.4"
            dur="2s"
            repeatCount="indefinite"
          />
        </circle>
        <text x="395" y="198" fill="var(--clr-signal-orange)" fontSize="8.5" fontWeight="700" fontFamily="var(--font-mono)">
          +1 INJECTED CLONE
        </text>

        {/* ── STAGE 3: VALIDATION CHECKPOINT BOUNDARY (x: 475, y: 40 to 220) ─ */}
        <g className="pipeline-checkpoint" transform="translate(475, 45)">
          {/* Checkpoint boundary gate */}
          <rect
            x="0"
            y="0"
            width="145"
            height="150"
            fill="var(--clr-svg-gate-bg)"
            stroke={isDetected ? "var(--clr-success)" : isSurvived ? "var(--clr-signal-orange)" : "var(--clr-svg-node-border)"}
            strokeWidth={isDetected || isSurvived ? 2 : 1.2}
            rx="2"
          />
          <rect
            x="0"
            y="0"
            width="145"
            height="22"
            fill={isDetected ? "var(--clr-success)" : isSurvived ? "var(--clr-svg-header-bg)" : "var(--clr-svg-header-bg)"}
          />
          <text x="8" y="15" fill="#FFFFFF" fontSize="9" fontWeight="700" fontFamily="var(--font-mono)">
            03 // VALIDATION GATE
          </text>

          {/* Clean path checkpoint */}
          <circle cx="20" cy="55" r="4" fill="var(--clr-success)" />
          <text x="30" y="58" fill="var(--clr-text-primary)" fontSize="9.5" fontWeight="600" fontFamily="var(--font-sans)">
            Required Columns ✓
          </text>

          <circle cx="20" cy="80" r="4" fill="var(--clr-success)" />
          <text x="30" y="83" fill="var(--clr-text-primary)" fontSize="9.5" fontWeight="600" fontFamily="var(--font-sans)">
            Positive Qty ✓
          </text>

          {/* The Uniqueness Checkpoint Line */}
          <line x1="8" y1="105" x2="137" y2="105" stroke="var(--clr-border)" strokeWidth="1" />

          {isDetected ? (
            <>
              <rect x="8" y="112" width="129" height="28" fill="var(--clr-svg-active-gate)" stroke="var(--clr-success)" strokeWidth="1" rx="2" />
              <text x="14" y="125" fill="var(--clr-success)" fontSize="9" fontWeight="700" fontFamily="var(--font-mono)">
                UNIQUENESS: ACTIVE
              </text>
              <text x="14" y="136" fill="var(--clr-success)" fontSize="8" fontFamily="var(--font-mono)">
                FAULT DETECTED & BLOCKED
              </text>
            </>
          ) : (
            <>
              <rect x="8" y="112" width="129" height="28" fill="var(--clr-svg-escape-gate)" stroke="var(--clr-signal-orange)" strokeWidth="1" rx="2" />
              <text x="14" y="125" fill="var(--clr-signal-orange)" fontSize="9" fontWeight="700" fontFamily="var(--font-mono)">
                UNIQUENESS: DISABLED
              </text>
              <text x="14" y="136" fill="var(--clr-signal-orange)" fontSize="8" fontFamily="var(--font-mono)">
                SILENT ESCAPE ROUTE ⚠
              </text>
            </>
          )}
        </g>

        {/* Clean stream out of checkpoint */}
        <path d="M 620 100 L 690 100" stroke="var(--clr-svg-arrow)" strokeWidth="1.5" markerEnd="url(#arrow-navy)" />

        {/* Fault path out of checkpoint */}
        {isDetected ? (
          // Trapped! Red/green barrier stop sign
          <g transform="translate(620, 175)">
            <line x1="0" y1="0" x2="30" y2="0" stroke="var(--clr-success)" strokeWidth="2" strokeDasharray="2 2" />
            <circle cx="35" cy="0" r="8" fill="var(--clr-svg-active-gate)" stroke="var(--clr-success)" strokeWidth="1.5" />
            <text x="31" y="4" fill="var(--clr-success)" fontSize="11" fontWeight="bold">✕</text>
            <text x="48" y="4" fill="var(--clr-success)" fontSize="8.5" fontWeight="700" fontFamily="var(--font-mono)">
              TRAPPED AT GATE
            </text>
          </g>
        ) : (
          // Escaped! Continues straight to corrupt analytics warehouse
          <g>
            <path
              d="M 620 185 L 690 185"
              stroke="var(--clr-signal-orange)"
              strokeWidth="2.5"
              strokeDasharray="4 2"
              markerEnd="url(#arrow-orange)"
            />
            <text x="625" y="177" fill="var(--clr-signal-orange)" fontSize="8" fontWeight="700" fontFamily="var(--font-mono)">
              SURVIVING LEAK
            </text>
          </g>
        )}

        {/* ── STAGE 4: BUSINESS METRICS & WAREHOUSE (x: 695, y: 70) ────────── */}
        <g className="pipeline-stage" transform="translate(695, 70)">
          <rect
            x="0"
            y="0"
            width="125"
            height="100"
            fill={isDetected ? "var(--clr-svg-node-bg)" : isSurvived ? "var(--clr-tech-panel)" : "var(--clr-svg-node-bg)"}
            stroke={isDetected ? "var(--clr-success)" : isSurvived ? "var(--clr-signal-orange)" : "var(--clr-svg-node-border)"}
            strokeWidth={1.5}
            rx="2"
          />
          <rect
            x="0"
            y="0"
            width="125"
            height="20"
            fill={isDetected ? "var(--clr-success)" : isSurvived ? "var(--clr-signal-orange)" : "var(--clr-svg-header-bg)"}
          />
          <text x="8" y="14" fill="#FFFFFF" fontSize="9" fontWeight="700" fontFamily="var(--font-mono)">
            04 // METRICS
          </text>

          <text
            x="10"
            y="42"
            fill="var(--clr-text-primary)"
            fontSize="10"
            fontWeight="600"
            fontFamily="var(--font-sans)"
          >
            Total Revenue
          </text>

          {isDetected ? (
            <>
              <text x="10" y="62" fill="var(--clr-success)" fontSize="13" fontWeight="700" fontFamily="var(--font-mono)">
                ₹11,300.00
              </text>
              <text x="10" y="80" fill="var(--clr-text-muted)" fontSize="8" fontFamily="var(--font-mono)">
                Protected · 0 Drift
              </text>
            </>
          ) : isSurvived ? (
            <>
              <text x="10" y="62" fill="var(--clr-signal-orange)" fontSize="13" fontWeight="700" fontFamily="var(--font-mono)">
                ₹12,100.00
              </text>
              <text x="10" y="80" fill="var(--clr-text-secondary)" fontSize="8" fontFamily="var(--font-mono)">
                Corrupted (+₹800)
              </text>
            </>
          ) : (
            <>
              <text x="10" y="62" fill="var(--clr-text-primary)" fontSize="13" fontWeight="700" fontFamily="var(--font-mono)">
                ₹11,300.00
              </text>
              <text x="10" y="80" fill="var(--clr-text-muted)" fontSize="8" fontFamily="var(--font-mono)">
                Baseline State
              </text>
            </>
          )}
        </g>

        {/* Lower technical telemetry bar inside SVG */}
        <line x1="20" y1="245" x2="820" y2="245" stroke="var(--clr-svg-grid)" strokeWidth="1" />
        <text x="25" y="263" fill="var(--clr-text-muted)" fontSize="9" fontFamily="var(--font-mono)">
          STATUS: {isDetected ? "GATE ENFORCED [UNIQUE_CHECK=PASS]" : "FAULT ESCAPING [UNIQUE_CHECK=DISABLED]"}
        </text>
        <text x="440" y="263" fill="var(--clr-text-muted)" fontSize="9" fontFamily="var(--font-mono)">
          SYNTHETIC TEST VECTOR // DATA-TRIPWIRE ENGINE
        </text>
        <text x="760" y="263" fill="var(--clr-text-primary)" fontSize="9" fontWeight="700" fontFamily="var(--font-mono)">
          SEC-01
        </text>
      </svg>
    </div>
  );
}
