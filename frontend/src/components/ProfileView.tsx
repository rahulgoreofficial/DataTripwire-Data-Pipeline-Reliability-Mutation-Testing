/**
 * ProfileView (Dataset Profile & Inspection).
 *
 * Technical inspection view rendering multi-domain selection, column schema,
 * null distributions, numeric telemetry statistics, and pipeline compatibility status.
 */

import { useState } from "react";
import type { DatasetResponse } from "../types/api";

interface ProfileViewProps {
  dataset: DatasetResponse;
  onProceed: (domain?: string) => void;
  activeDomain?: string;
  onSelectDomain?: (domain: string) => void;
}

const TYPE_BADGE_MAP: Record<string, string> = {
  integer: "badge-navy",
  float: "badge-muted",
  string: "badge-muted",
  date: "badge-success",
  unknown: "badge-warning",
};

export function ProfileView({
  dataset,
  onProceed,
  activeDomain,
  onSelectDomain,
}: ProfileViewProps) {
  const { profile, filename, warnings } = dataset;

  const isMfg = Boolean(
    profile.is_manufacturing_compatible ||
    dataset.is_manufacturing_compatible ||
    profile.detected_domain === "manufacturing"
  );
  const isSales = Boolean(profile.is_sales_compatible || dataset.is_sales_compatible);
  const initialDomain = activeDomain || (isMfg ? "manufacturing" : isSales ? "sales" : "general");

  const [currentDomain, setCurrentDomain] = useState<string>(initialDomain);

  const handleDomainChange = (dom: string) => {
    setCurrentDomain(dom);
    if (onSelectDomain) {
      onSelectDomain(dom);
    }
  };

  const isCurrentDomainCompatible =
    currentDomain === "manufacturing"
      ? isMfg
      : currentDomain === "sales"
      ? isSales
      : false;

  const totalNullCells = Object.values(profile.null_counts).reduce((s, v) => s + v, 0);

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
            Telemetry // Dataset Inspection & Domain Detection
          </div>
          <h2 style={{ marginBottom: "6px" }}>Pipeline Profile: {filename}</h2>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            DATASET_ID: {profile.dataset_id} · DETECTED: {profile.detected_domain?.toUpperCase() || (isMfg ? "MANUFACTURING" : isSales ? "SALES" : "GENERAL")}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "14px", flexWrap: "wrap" }}>
          <span
            className={`badge ${
              currentDomain === "general"
                ? "badge-muted"
                : isCurrentDomainCompatible
                ? "badge-success"
                : "badge-danger"
            }`}
          >
            {currentDomain === "manufacturing"
              ? isMfg
                ? "✓ Manufacturing IoT Compatible"
                : "✗ Incompatible with Manufacturing Schema"
              : currentDomain === "sales"
              ? isSales
                ? "✓ Sales Schema Compatible"
                : "✗ Incompatible with Sales Schema"
              : "ℹ General CSV Profiling"}
          </span>

          <button
            id="btn-proceed-configure"
            className="btn btn-signal"
            onClick={() => onProceed(currentDomain)}
            disabled={!isCurrentDomainCompatible}
            title={
              !isCurrentDomainCompatible
                ? currentDomain === "general"
                  ? "Select a domain-specific profile (Sales or Manufacturing) to run mutations"
                  : `Dataset is incompatible with ${currentDomain === "manufacturing" ? "Manufacturing IoT" : "Sales"} schema`
                : undefined
            }
          >
            <span>Open Mutation Lab →</span>
          </button>
        </div>
      </div>

      {/* ── DOMAIN PROFILE SELECTOR STRIP ─────────────────────────── */}
      <div
        className="card"
        style={{
          marginBottom: "24px",
          padding: "14px 18px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "14px",
          backgroundColor: "var(--clr-surface-raised)",
          border: "1px solid var(--clr-border)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.74rem",
              fontWeight: 700,
              letterSpacing: "0.06em",
              color: "var(--clr-text-secondary)",
              textTransform: "uppercase",
            }}
          >
            Active Domain Profile:
          </span>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button
              id="domain-pill-mfg"
              className={`btn btn-sm ${currentDomain === "manufacturing" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => handleDomainChange("manufacturing")}
            >
              <span>⚙️ Manufacturing / IoT</span>
              {isMfg && <span style={{ marginLeft: "4px", color: "var(--clr-success)" }}>✓</span>}
            </button>

            <button
              id="domain-pill-sales"
              className={`btn btn-sm ${currentDomain === "sales" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => handleDomainChange("sales")}
            >
              <span>⚡ E-commerce Sales</span>
              {isSales && <span style={{ marginLeft: "4px", color: "var(--clr-success)" }}>✓</span>}
            </button>

            <button
              id="domain-pill-general"
              className={`btn btn-sm ${currentDomain === "general" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => handleDomainChange("general")}
            >
              <span>📊 General CSV Profiling</span>
            </button>
          </div>
        </div>

        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.74rem", color: "var(--clr-text-muted)" }}>
          {currentDomain === "manufacturing"
            ? "Targets: Reading Uniqueness, Machine Telemetry, Defect Consistency"
            : currentDomain === "sales"
            ? "Targets: Order Uniqueness, Quantities, Prices, Revenue Ledger"
            : "Structural Inspection Mode · Domain Mutation Engine Paused"}
        </div>
      </div>

      {/* ── DOMAIN-SPECIFIC COMPATIBILITY GUIDANCE ─────────────────── */}
      {currentDomain === "sales" && !isSales && (
        <div className="alert alert-warning" style={{ marginBottom: "24px" }}>
          <span>ℹ️</span>
          <span>
            This dataset is missing required sales schema fields:{" "}
            <code>transaction_id, customer_id, quantity, unit_price, transaction_date</code>.
            {isMfg ? " Switch to Manufacturing / Industrial IoT domain above to enable mutation testing." : " Mutation testing requires a compatible schema."}
          </span>
        </div>
      )}

      {currentDomain === "manufacturing" && !isMfg && (
        <div className="alert alert-warning" style={{ marginBottom: "24px" }}>
          <span>ℹ️</span>
          <span>
            This dataset is missing required industrial telemetry fields:{" "}
            <code>reading_id, timestamp, machine_id, temperature_c, pressure_bar, vibration_mm_s, units_produced, defect_count</code>.
            {isSales ? " Switch to E-commerce Sales domain above to enable mutation testing." : " Mutation testing requires a compatible schema."}
          </span>
        </div>
      )}

      {currentDomain === "general" && (
        <div
          className="alert"
          style={{
            marginBottom: "24px",
            backgroundColor: "var(--clr-tech-panel)",
            border: "1px solid var(--clr-border)",
            color: "var(--clr-text-primary)",
          }}
        >
          <span>ℹ️</span>
          <span>
            <strong>General CSV Profiling Active:</strong> Column hygiene, null distributions, and statistics are available.
            Domain-specific mutation testing is available for <strong>Manufacturing IoT</strong> or <strong>E-commerce Sales</strong>.
            Select a supported domain profile above to test pipeline safeguards.
          </span>
        </div>
      )}

      {/* ── WARNINGS (if any) ─────────────────────────────────────── */}
      {warnings.length > 0 && currentDomain !== "manufacturing" && (
        <div style={{ marginBottom: "24px" }}>
          {warnings.map((w, i) => (
            <div key={i} className="alert alert-warning" style={{ marginBottom: "8px" }}>
              <span>⚠️</span>
              <span>{w}</span>
            </div>
          ))}
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
          <div
            style={{
              padding: "18px 22px",
              borderBottom: "1px solid var(--clr-border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
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
                      <td
                        style={{
                          fontFamily: "var(--font-mono)",
                          color: nullCount > 0 ? "var(--clr-signal-orange)" : "var(--clr-text-secondary)",
                        }}
                      >
                        {nullCount}
                      </td>
                      <td>
                        <div className="null-bar-wrap">
                          <div className="null-bar">
                            <div
                              className="null-bar-fill"
                              style={{
                                width: `${100 - nullPct}%`,
                                backgroundColor: nullPct > 0 ? "var(--clr-signal-orange)" : "var(--clr-success)",
                              }}
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
                  <div className="card-subtitle">
                    {currentDomain === "manufacturing"
                      ? "Sensor telemetry signals & production stats"
                      : "Statistical metrics from baseline sample"}
                  </div>
                </div>
              </div>

              {Object.entries(profile.numeric_summaries).map(([col, stats]) => (
                <div key={col} style={{ marginBottom: "18px" }}>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.78rem",
                      fontWeight: 700,
                      color: "var(--clr-signal-orange)",
                      marginBottom: "8px",
                    }}
                  >
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
                        <div
                          style={{
                            fontSize: "0.68rem",
                            fontFamily: "var(--font-mono)",
                            color: "var(--clr-text-muted)",
                            textTransform: "uppercase",
                          }}
                        >
                          {k}
                        </div>
                        <div
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.88rem",
                            fontWeight: 700,
                            color: "var(--clr-text-primary)",
                          }}
                        >
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
              {currentDomain === "manufacturing"
                ? "Enter the Mutation Lab to inject a duplicate sensor reading or telemetry anomaly and evaluate whether validation checkpoints trap the fault."
                : "Proceed to the Mutation Lab to introduce synthetic faults and test whether pipeline validation safeguards detect the corrupt state."}
            </p>
            <button
              className="btn btn-primary w-full"
              onClick={() => onProceed(currentDomain)}
              disabled={!isCurrentDomainCompatible}
            >
              Configure Mutation Experiment →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
