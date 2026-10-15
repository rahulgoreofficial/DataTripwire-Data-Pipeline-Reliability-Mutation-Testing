/**
 * ProfileView (Dataset Profile & Inspection).
 *
 * Technical inspection view rendering column schema, null distribution,
 * numeric statistics, and pipeline compatibility status.
 */

import type { DatasetResponse } from "../types/api";

interface ProfileViewProps {
  dataset: DatasetResponse;
  onProceed: () => void;
}

const TYPE_BADGE_MAP: Record<string, string> = {
  integer: "badge-navy",
  float: "badge-muted",
  string: "badge-muted",
  date: "badge-success",
  unknown: "badge-warning",
};

export function ProfileView({ dataset, onProceed }: ProfileViewProps) {
  const { profile, filename, warnings } = dataset;

  const totalNullCells = Object.values(profile.null_counts).reduce((s, v) => s + v, 0);

  return (
    <div>
      {/* ── HEADER ROW ────────────────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: "28px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div className="hero-kicker" style={{ marginBottom: "8px" }}>
            Telemetry // Dataset Inspection
          </div>
          <h2 style={{ marginBottom: "6px" }}>Pipeline Profile: {filename}</h2>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            DATASET_ID: {profile.dataset_id}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <span className={`badge ${profile.is_sales_compatible ? "badge-success" : "badge-danger"}`}>
            {profile.is_sales_compatible ? "✓ Sales Schema Compatible" : "✗ Incompatible Schema"}
          </span>

          <button
            id="btn-proceed-configure"
            className="btn btn-signal"
            onClick={onProceed}
            disabled={!profile.is_sales_compatible}
            title={!profile.is_sales_compatible ? "Dataset must be sales-compatible to run mutations" : undefined}
          >
            <span>Open Mutation Lab →</span>
          </button>
        </div>
      </div>

      {/* ── WARNINGS (if any) ─────────────────────────────────────── */}
      {warnings.length > 0 && (
        <div style={{ marginBottom: "24px" }}>
          {warnings.map((w, i) => (
            <div key={i} className="alert alert-warning" style={{ marginBottom: "8px" }}>
              <span>⚠️</span>
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {!profile.is_sales_compatible && (
        <div className="alert alert-warning" style={{ marginBottom: "24px" }}>
          <span>ℹ️</span>
          <span>
            This dataset is missing required sales schema fields:{" "}
            <code>transaction_id, customer_id, quantity, unit_price, transaction_date</code>.
            Mutation testing requires a compatible schema.
          </span>
        </div>
      )}

      {/* ── METRICS OVERVIEW BAR ──────────────────────────────────── */}
      <div className="profile-overview-bar">
        <div className="stat-cell">
          <div className="stat-cell-label">Total Records</div>
          <div className="stat-cell-value">{profile.row_count.toLocaleString()}</div>
        </div>

        <div className="stat-cell">
          <div className="stat-cell-label">Column Dimensions</div>
          <div className="stat-cell-value">{profile.column_count}</div>
        </div>

        <div className="stat-cell">
          <div className="stat-cell-label">Duplicate Rows</div>
          <div className={`stat-cell-value ${profile.duplicate_row_count > 0 ? "highlight-orange" : ""}`}>
            {profile.duplicate_row_count}
          </div>
        </div>

        <div className="stat-cell">
          <div className="stat-cell-label">Null Cells</div>
          <div className={`stat-cell-value ${totalNullCells > 0 ? "highlight-orange" : "highlight-green"}`}>
            {totalNullCells}
          </div>
        </div>
      </div>

      {/* ── MAIN INSPECTION CONTENT ───────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 0.6fr", gap: "28px", alignItems: "start" }}>
        {/* Left: Column Schema Table */}
        <div className="card" style={{ padding: "0" }}>
          <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--clr-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3 style={{ marginBottom: "2px" }}>Column Schema & Null Distribution</h3>
              <p style={{ fontSize: "0.8rem" }}>Type inference and data hygiene metrics across all columns</p>
            </div>
            <span className="badge badge-muted">{profile.column_names.length} Attributes</span>
          </div>

          <div className="data-table-container" style={{ border: "none" }}>
            <table className="data-table" aria-label="Dataset column attributes">
              <thead>
                <tr>
                  <th>Field Name</th>
                  <th>Inferred Type</th>
                  <th>Null Count</th>
                  <th>Completeness</th>
                </tr>
              </thead>
              <tbody>
                {profile.column_names.map((col) => {
                  const type = profile.column_types[col] ?? "unknown";
                  const nullCount = profile.null_counts[col] ?? 0;
                  const nullPct = profile.null_percentages[col] ?? 0;
                  const badgeCls = TYPE_BADGE_MAP[type] ?? "badge-muted";

                  return (
                    <tr key={col}>
                      <td>
                        <code style={{ fontWeight: 600, color: "var(--clr-text-primary)" }}>{col}</code>
                      </td>
                      <td>
                        <span className={`badge ${badgeCls}`}>{type}</span>
                      </td>
                      <td style={{ fontFamily: "var(--font-mono)", color: nullCount > 0 ? "var(--clr-signal-orange)" : "var(--clr-text-secondary)" }}>
                        {nullCount}
                      </td>
                      <td>
                        <div className="null-bar-wrap">
                          <div className="null-bar">
                            <div
                              className="null-bar-fill"
                              style={{ width: `${100 - nullPct}%`, backgroundColor: nullPct > 0 ? "var(--clr-signal-orange)" : "var(--clr-success)" }}
                            />
                          </div>
                          <span style={{ fontSize: "0.74rem", fontFamily: "var(--font-mono)", color: "var(--clr-text-secondary)" }}>
                            {(100 - nullPct).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Numeric Summaries & System Info */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {Object.keys(profile.numeric_summaries).length > 0 && (
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Numeric Distributions</div>
                  <div className="card-subtitle">Statistical metrics from baseline sample</div>
                </div>
              </div>

              {Object.entries(profile.numeric_summaries).map(([col, stats]) => (
                <div key={col} style={{ marginBottom: "18px" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem", fontWeight: 700, color: "var(--clr-signal-orange)", marginBottom: "8px" }}>
                    {col}
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                    {Object.entries(stats).map(([k, v]) => (
                      <div
                        key={k}
                        style={{
                          background: "var(--clr-surface-raised)",
                          border: "1px solid var(--clr-border-subtle)",
                          padding: "8px 12px",
                          borderRadius: "var(--radius-xs)",
                        }}
                      >
                        <div style={{ fontSize: "0.68rem", fontFamily: "var(--font-mono)", color: "var(--clr-text-muted)", textTransform: "uppercase" }}>
                          {k}
                        </div>
                        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem", fontWeight: 700, color: "var(--clr-text-primary)" }}>
                          {typeof v === "number" ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : v}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Quick Start Card */}
          <div className="card" style={{ backgroundColor: "var(--clr-surface-raised)" }}>
            <h4 style={{ marginBottom: "6px" }}>Next: Mutation Testing</h4>
            <p style={{ fontSize: "0.82rem", marginBottom: "16px" }}>
              Proceed to the Mutation Lab to introduce a duplicate transaction and test whether the pipeline validation rules detect the fault.
            </p>
            <button
              className="btn btn-primary w-full"
              onClick={onProceed}
              disabled={!profile.is_sales_compatible}
            >
              Configure Mutation Experiment →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
