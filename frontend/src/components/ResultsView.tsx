/**
 * ResultsView (Forensic Investigation & Business Impact).
 *
 * Technical investigation dashboard featuring:
 * 1. Signature before-and-after business metrics comparison
 * 2. Live pipeline flow status illustration
 * 3. Mutation outcome table (Survived vs Detected) with forensic evidence
 * 4. Actionable rule recommendations with one-click test toggle
 */

import { useState } from "react";
import type { EvaluationReport, RuleRecommendation } from "../types/api";
import { PipelineIllustration } from "./PipelineIllustration";

interface ResultsViewProps {
  report: EvaluationReport;
  onReset: () => void;
  onRetestWithSafeguard?: (ruleKey: string) => void;
  activeDomain?: string;
}

const MUTATION_LABELS: Record<string, string> = {
  duplicate_row: "Duplicate Row",
  missing_required_value: "Missing Required Value",
  invalid_quantity: "Invalid Quantity",
  invalid_unit_price: "Invalid Unit Price",
  dropped_row: "Dropped Row",
  // Manufacturing IoT mutations
  duplicate_sensor_reading: "Duplicate Sensor Reading",
  missing_sensor_value: "Missing Sensor Value",
  invalid_sensor_value: "Invalid Sensor Value",
  dropped_sensor_reading: "Dropped Sensor Reading",
  invalid_production_value: "Invalid Production Value",
};

function formatCurrency(val: string | number | null | undefined): string {
  if (val === null || val === undefined || val === "") return "—";
  const n = typeof val === "number" ? val : parseFloat(val);
  if (isNaN(n)) return String(val);
  return `₹${n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function ResultsView({ report, onReset, onRetestWithSafeguard, activeDomain }: ResultsViewProps) {
  const [selectedEvalIndex, setSelectedEvalIndex] = useState<number>(0);

  const isMfg =
    activeDomain === "manufacturing" ||
    report.metadata?.domain === "manufacturing" ||
    report.baseline_metrics?.domain === "manufacturing" ||
    (report.baseline_metrics?.total_readings !== undefined && report.baseline_metrics?.total_readings !== null);

  const survived = report.evaluations.filter((e) => e.applied && e.detected === false);
  const hasSurvived = survived.length > 0;
  const activeEval = report.evaluations[selectedEvalIndex] ?? report.evaluations[0];
  const isDetected = activeEval?.detected === true;

  // Sales domain metrics
  const baselineRevStr =
    activeEval?.baseline_metrics?.total_revenue ??
    report.baseline_metrics?.total_revenue ??
    "11300.00";
  const mutatedRevStr =
    activeEval?.mutated_metrics?.total_revenue ??
    (activeEval?.metric_deltas?.revenue_delta !== undefined
      ? String(parseFloat(baselineRevStr) + Number(activeEval.metric_deltas.revenue_delta))
      : baselineRevStr);

  const baselineRevNum = parseFloat(baselineRevStr) || 0;
  const rawMutatedRevNum = parseFloat(mutatedRevStr) || 0;
  const effectiveMutatedRevNum = isDetected ? baselineRevNum : rawMutatedRevNum;
  const deltaAmount = isDetected ? 0 : (effectiveMutatedRevNum - baselineRevNum);
  const deltaPct = baselineRevNum > 0 ? (deltaAmount / baselineRevNum) * 100 : 0;

  // Manufacturing domain metrics
  const baselineReadings =
    activeEval?.baseline_metrics?.total_readings ??
    report.baseline_metrics?.total_readings ??
    0;
  const baselineUnits =
    activeEval?.baseline_metrics?.total_units_produced ??
    report.baseline_metrics?.total_units_produced ??
    0;
  const rawMutatedUnits =
    activeEval?.mutated_metrics?.total_units_produced ??
    (activeEval?.metric_deltas?.units_produced_delta !== undefined
      ? baselineUnits + Number(activeEval.metric_deltas.units_produced_delta)
      : baselineUnits);
  const effectiveMutatedUnits = isDetected ? baselineUnits : rawMutatedUnits;
  const deltaUnits = isDetected ? 0 : (effectiveMutatedUnits - baselineUnits);
  const deltaUnitsPct = baselineUnits > 0 ? (deltaUnits / baselineUnits) * 100 : 0;

  return (
    <div>
      {/* ── HEADER ROW ────────────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          marginBottom: "24px",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div className="hero-kicker" style={{ marginBottom: "8px" }}>
            Investigation // Evaluation Findings · {isMfg ? "Industrial IoT Domain" : "E-Commerce Sales Domain"}
          </div>
          <h2 style={{ marginBottom: "6px" }}>Pipeline Reliability Audit</h2>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            REPORT_ID: {report.report_id} · DATASET: {report.dataset_id} · DOMAIN: {isMfg ? "MANUFACTURING TELEMETRY" : "RETAIL SALES"}
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <button className="btn btn-secondary" onClick={onReset}>
            ← Adjust Configuration
          </button>
        </div>
      </div>

      {/* ── SIGNATURE BUSINESS/OPERATIONAL IMPACT COMPARISON ─────────── */}
      <div className="signature-comparison-card">
        <div className="signature-comparison-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  color: hasSurvived ? "var(--clr-signal-orange)" : "var(--clr-success)",
                }}
              >
                {isMfg ? "OPERATIONAL TELEMETRY INTEGRITY ANALYSIS" : "BUSINESS METRIC INTEGRITY ANALYSIS"}
              </span>
              <span
                className={`badge ${hasSurvived ? "badge-danger" : "badge-success"}`}
                style={{ fontSize: "0.68rem" }}
              >
                {hasSurvived ? "Silent Metric Drift Detected" : "Metrics Protected"}
              </span>
            </div>
            <p style={{ fontSize: "0.82rem", color: "#A3AAB8", marginTop: "4px" }}>
              {isMfg
                ? "Comparing pre-mutation industrial telemetry baseline against post-mutation corrupted pipeline state"
                : "Comparing pre-mutation ledger baseline against post-mutation corrupted pipeline state"}
            </p>
          </div>

          <div style={{ textAlign: "right" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "#8C95B0" }}>
              DETECTION SCORE
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "1.8rem",
                fontWeight: 700,
                color:
                  report.mutation_score !== null && report.mutation_score !== undefined
                    ? report.mutation_score === 100
                      ? "var(--clr-success)"
                      : "var(--clr-signal-orange)"
                    : "var(--clr-text-muted)",
              }}
            >
              {report.mutation_score !== null && report.mutation_score !== undefined
                ? `${report.mutation_score.toFixed(0)}%`
                : "N/A"}
            </div>
          </div>
        </div>

        <div className="signature-comparison-grid">
          {/* Baseline Node */}
          <div className="metric-node">
            <span className="metric-node-kicker">
              {isMfg ? "Baseline Production Units" : "Baseline Revenue (Clean)"}
            </span>
            <span className="metric-node-amount">
              {isMfg ? `${baselineUnits.toLocaleString()} Units` : formatCurrency(baselineRevNum)}
            </span>
            <span className="metric-node-subtext">
              {isMfg
                ? `${baselineReadings.toLocaleString()} Verified Sensor Frames · 0 Anomalies`
                : "15 Verified Transactions · 0 Anomalies"}
            </span>
          </div>

          <div className="metric-divider-arrow">→</div>

          {/* Mutated Node */}
          <div className="metric-node">
            <span className="metric-node-kicker">
              {isDetected
                ? "Pipeline Output (Protected)"
                : isMfg
                ? "Mutated Units (Observed)"
                : "Mutated Revenue (Observed)"}
            </span>
            <span
              className="metric-node-amount"
              style={{
                color: isDetected
                  ? "var(--clr-success)"
                  : (isMfg ? Math.abs(deltaUnits) > 0 : Math.abs(deltaAmount) > 0)
                  ? "var(--clr-signal-orange)"
                  : "#FFFFFF",
              }}
            >
              {isMfg
                ? `${effectiveMutatedUnits.toLocaleString()} Units`
                : formatCurrency(effectiveMutatedRevNum)}
            </span>
            <span className="metric-node-subtext">
              {isDetected
                ? "Corrupt Records Intercepted & Blocked"
                : isMfg
                ? activeEval?.mutation_spec.mutation_type === "duplicate_sensor_reading"
                  ? "Includes Unchecked Duplicate Telemetry Frame"
                  : "Post-Mutation Pipeline State"
                : activeEval?.mutation_spec.mutation_type === "duplicate_row"
                ? "Includes Unchecked Duplicate ORD-101"
                : "Post-Mutation Pipeline State"}
            </span>
          </div>

          <div className="metric-divider-arrow">=</div>

          {/* Business/Operational Impact Delta */}
          <div
            className={`metric-delta-box ${
              (isMfg ? Math.abs(deltaUnits) === 0 : Math.abs(deltaAmount) === 0) ? "safe" : ""
            }`}
          >
            <span className="metric-delta-label">
              {(isMfg ? Math.abs(deltaUnits) === 0 : Math.abs(deltaAmount) === 0)
                ? "Drift Magnitude (Zero)"
                : isMfg
                ? "Net Production Drift"
                : "Net Revenue Distortion"}
            </span>
            <span className="metric-delta-amount">
              {isMfg
                ? deltaUnits > 0
                  ? `+${deltaUnits.toLocaleString()} Units`
                  : `${deltaUnits.toLocaleString()} Units`
                : deltaAmount > 0
                ? `+${formatCurrency(deltaAmount)}`
                : formatCurrency(deltaAmount)}
            </span>
            <span className="metric-delta-pct">
              {(isMfg ? Math.abs(deltaUnits) === 0 : Math.abs(deltaAmount) === 0)
                ? "0.0% variance from ground truth"
                : isMfg
                ? `${deltaUnitsPct > 0 ? "+" : ""}${deltaUnitsPct.toFixed(2)}% downstream aggregation drift`
                : `${deltaPct > 0 ? "+" : ""}${deltaPct.toFixed(2)}% downstream ledger error`}
            </span>
          </div>
        </div>
      </div>

      {/* ── MANUFACTURING OPERATIONAL TELEMETRY METRICS STRIP ─────── */}
      {isMfg && report.baseline_metrics && (
        <div
          className="card"
          style={{
            marginBottom: "24px",
            padding: "16px 20px",
            backgroundColor: "var(--clr-surface-raised)",
          }}
        >
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.72rem",
              fontWeight: 700,
              color: "var(--clr-signal-orange)",
              letterSpacing: "0.06em",
              marginBottom: "12px",
              textTransform: "uppercase",
            }}
          >
            Industrial Telemetry Baseline Measurements
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
              gap: "16px",
            }}
          >
            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--clr-text-secondary)" }}>
                Avg Operating Temp
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                {report.baseline_metrics.avg_temperature_c?.toFixed(1) ?? "—"} °C
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--clr-text-secondary)" }}>
                Max: {report.baseline_metrics.max_temperature_c?.toFixed(1) ?? "—"} °C
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--clr-text-secondary)" }}>
                Avg Vibration
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                {report.baseline_metrics.avg_vibration_mm_s?.toFixed(2) ?? "—"} mm/s
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--clr-text-secondary)" }}>
                Max: {report.baseline_metrics.max_vibration_mm_s?.toFixed(2) ?? "—"} mm/s
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--clr-text-secondary)" }}>
                Avg Pressure
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                {report.baseline_metrics.avg_pressure_bar?.toFixed(2) ?? "—"} bar
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--clr-text-secondary)" }}>
                Current: {report.baseline_metrics.avg_motor_current_a?.toFixed(1) ?? "—"} A
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--clr-text-secondary)" }}>
                Total Energy Consumed
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                {report.baseline_metrics.total_energy_kwh?.toFixed(1) ?? "—"} kWh
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--clr-text-secondary)" }}>
                Across distinct intervals
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--clr-text-secondary)" }}>
                Total Defects
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                {report.baseline_metrics.total_defect_count?.toLocaleString() ?? "—"}
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--clr-text-secondary)" }}>
                Defective units
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--clr-text-secondary)" }}>
                Quality Pass Rate
              </div>
              <div
                style={{
                  fontSize: "1.15rem",
                  fontWeight: 700,
                  fontFamily: "var(--font-mono)",
                  color: "var(--clr-success)",
                }}
              >
                {report.baseline_metrics.avg_quality_pass_rate_pct?.toFixed(2) ?? "—"}%
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--clr-text-secondary)" }}>
                Production average
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── LIVE PIPELINE DIAGRAM LINKED TO EVALUATION STATE ──────── */}
      <div style={{ marginBottom: "28px" }}>
        <PipelineIllustration
          mode="live"
          status={hasSurvived ? "survived" : "detected"}
          mutationType={
            activeEval?.mutation_spec.mutation_type ||
            (isMfg ? "duplicate_sensor_reading" : "duplicate_row")
          }
          hasUniquenessRule={!hasSurvived}
          domain={isMfg ? "manufacturing" : "sales"}
        />
      </div>

      {/* ── RESULTS & EVIDENCE DUAL COLUMN ────────────────────────── */}
      <div className="results-grid">
        {/* Left: Mutation Findings Breakdown */}
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "16px",
            }}
          >
            <div>
              <h3 style={{ marginBottom: "2px" }}>Mutation Verification Ledger</h3>
              <p style={{ fontSize: "0.8rem" }}>
                Inspecting whether active rules detected each injected synthetic fault
              </p>
            </div>
            <span className="badge badge-muted">
              {report.evaluations.length} Evaluated
            </span>
          </div>

          {report.evaluations.map((ev, idx) => {
            const isDet = ev.detected === true;
            const isSel = idx === selectedEvalIndex;

            return (
              <div
                key={ev.mutation_spec.mutation_id}
                className={`eval-card ${isDet ? "detected" : "survived"}`}
                onClick={() => setSelectedEvalIndex(idx)}
                style={{
                  borderWidth: isSel ? "2px" : "1px",
                  borderColor: isSel
                    ? isDet
                      ? "var(--clr-success)"
                      : "var(--clr-signal-orange)"
                    : undefined,
                }}
              >
                <div className="eval-card-header">
                  <span className={`badge ${isDet ? "badge-success" : "badge-orange"}`}>
                    {isDet ? "DETECTED ✓" : "SURVIVED ⚠"}
                  </span>

                  <span className="eval-card-title">
                    {MUTATION_LABELS[ev.mutation_spec.mutation_type] || ev.mutation_spec.mutation_type}
                    {ev.mutation_spec.target_record_id && (
                      <code style={{ marginLeft: "8px", color: "var(--clr-text-primary)" }}>
                        [{ev.mutation_spec.target_record_id}]
                      </code>
                    )}
                  </span>

                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                    {ev.findings.length} {ev.findings.length === 1 ? "finding" : "findings"}
                  </span>
                </div>

                <div className="eval-body">
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "8px",
                      fontSize: "0.8rem",
                    }}
                  >
                    <span style={{ color: "var(--clr-text-secondary)" }}>
                      Hypothesis: {ev.mutation_spec.description || "Synthesized test vector"}
                    </span>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontWeight: 600,
                        color: isDet ? "var(--clr-success)" : "var(--clr-signal-orange)",
                      }}
                    >
                      {isDet
                        ? "Checkpoints triggered"
                        : "Bypassed validation boundaries silently"}
                    </span>
                  </div>

                  {/* Forensic Evidence details */}
                  {ev.findings.length > 0 ? (
                    <div style={{ marginTop: "10px" }}>
                      <div
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          color: "var(--clr-text-primary)",
                          textTransform: "uppercase",
                          marginBottom: "4px",
                        }}
                      >
                        Evidence & Rule Traces
                      </div>
                      {ev.findings.map((f) => (
                        <div key={f.finding_id} className="evidence-block">
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                            <strong>RULE: {f.rule_id}</strong>
                            <span className="badge badge-muted">{f.severity}</span>
                          </div>
                          <div>{f.explanation}</div>
                          {f.affected_record_ids.length > 0 && (
                            <div style={{ marginTop: "4px", color: "var(--clr-text-secondary)", fontSize: "0.74rem" }}>
                              Records: {f.affected_record_ids.join(", ")}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div
                      className="evidence-block"
                      style={{
                        backgroundColor: "var(--clr-orange-bg)",
                        borderColor: "var(--clr-orange-border)",
                        color: "var(--clr-signal-orange)",
                      }}
                    >
                      <strong>VULNERABILITY VERIFIED:</strong> No validation rules flagged this
                      mutation. The {MUTATION_LABELS[ev.mutation_spec.mutation_type] || ev.mutation_spec.mutation_type}
                      {ev.mutation_spec.target_record_id ? ` on ${ev.mutation_spec.target_record_id}` : ""} traversed the pipeline undetected
                      {isMfg
                        ? ev.metric_deltas?.units_produced_delta !== undefined && Number(ev.metric_deltas.units_produced_delta) !== 0
                          ? `, causing a ${Number(ev.metric_deltas.units_produced_delta) > 0 ? "+" : ""}${Number(ev.metric_deltas.units_produced_delta).toLocaleString()} units distortion in downstream manufacturing ledgers.`
                          : ". Safeguards must be hardened to detect this fault."
                        : ev.metric_deltas?.revenue_delta !== undefined && Number(ev.metric_deltas.revenue_delta) !== 0
                        ? `, causing a ${Number(ev.metric_deltas.revenue_delta) > 0 ? "+" : ""}${formatCurrency(Number(ev.metric_deltas.revenue_delta))} silent revenue distortion in downstream ledgers.`
                        : ". Safeguards must be hardened to detect this fault."}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Recommendations & Actionable Remediation */}
        <div>
          <div style={{ marginBottom: "16px" }}>
            <h3 style={{ marginBottom: "2px" }}>Remediation Safeguards</h3>
            <p style={{ fontSize: "0.8rem" }}>
              Recommended rules to close identified detection vulnerabilities
            </p>
          </div>

          {report.recommendations.length > 0 ? (
            report.recommendations.map((reco: RuleRecommendation) => (
              <div
                key={reco.recommendation_id}
                className={`reco-card ${hasSurvived ? "highlight" : ""}`}
              >
                <div className="reco-header">
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span className="badge badge-navy">RECOMMENDED SAFEGUARD</span>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          fontSize: "0.76rem",
                          color: "var(--clr-signal-orange)",
                        }}
                      >
                        {reco.rule_type.toUpperCase()}
                      </span>
                    </div>
                    <h4 style={{ marginTop: "6px", marginBottom: "4px" }}>
                      {reco.description}
                    </h4>
                  </div>
                </div>

                <p style={{ fontSize: "0.82rem", color: "var(--clr-text-secondary)", lineHeight: 1.5 }}>
                  {reco.rationale}
                </p>

                {reco.code_snippet && (
                  <div className="code-snippet-box">
                    <code>{reco.code_snippet}</code>
                  </div>
                )}

                {hasSurvived && (
                  <div style={{ marginTop: "16px" }}>
                    <button
                      id={`btn-retest-safeguard-${reco.recommendation_id}`}
                      className="btn btn-signal w-full"
                      onClick={() => {
                        const ruleKey =
                          Object.keys(reco.suggested_rule_config)[0] ||
                          (isMfg ? "check_machine_timestamp_unique" : "check_unique_transaction_id");
                        onRetestWithSafeguard?.(ruleKey);
                      }}
                    >
                      ⚡ Test Recommended Safeguard ({reco.rule_type.toUpperCase()}) →
                    </button>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="card">
              <div style={{ color: "var(--clr-success)", fontWeight: 600, marginBottom: "4px" }}>
                ✓ No Safeguard Gaps Identified
              </div>
              <p style={{ fontSize: "0.82rem" }}>
                All injected mutation vectors were successfully trapped by current pipeline validation checkpoints.
              </p>
            </div>
          )}

          {/* Quick comparison info */}
          <div className="card" style={{ marginTop: "16px", backgroundColor: "var(--clr-surface-raised)" }}>
            <h4 style={{ marginBottom: "6px" }}>The Two-Step Hackathon Demo</h4>
            <ol style={{ fontSize: "0.82rem", paddingLeft: "16px", color: "var(--clr-text-secondary)", lineHeight: 1.6 }}>
              {isMfg ? (
                <>
                  <li>
                    <strong>Evaluation 1:</strong> Duplicate sensor reading with Composite Machine/Timestamp Uniqueness OFF → 0% score, duplicate telemetry stream leak. (Survived)
                  </li>
                  <li>
                    <strong>Evaluation 2:</strong> Duplicate sensor reading with Composite Machine/Timestamp Uniqueness ON → 100% score, zero drift. (Trapped)
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <strong>Evaluation 1:</strong> Duplicate row with Uniqueness OFF → 0% score, ₹800 drift. (Survived)
                  </li>
                  <li>
                    <strong>Evaluation 2:</strong> Duplicate row with Uniqueness ON → 100% score, ₹0 drift. (Trapped)
                  </li>
                </>
              )}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
