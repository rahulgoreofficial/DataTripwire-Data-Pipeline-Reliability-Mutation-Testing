/**
 * UploadView (Entry Screen & Overview).
 *
 * Editorial layout featuring oversized typography, the custom SVG pipeline
 * mutation illustration, and instant access to load the bundled sales sample
 * or upload a custom CSV.
 */

import { useCallback, useRef, useState } from "react";
import { loadSampleDataset, loadSampleManufacturingDataset, uploadDataset } from "../api/client";
import type { DatasetResponse } from "../types/api";
import { PipelineIllustration } from "./PipelineIllustration";

interface UploadViewProps {
  onDatasetLoaded: (dataset: DatasetResponse) => void;
}

export function UploadView({ onDatasetLoaded }: UploadViewProps) {
  const [loading, setLoading] = useState<"idle" | "sample" | "sample-mfg" | "upload">("idle");
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleError = (err: unknown) => {
    const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
    setError(msg);
    setLoading("idle");
  };

  const doLoadSample = async () => {
    setError(null);
    setLoading("sample");
    try {
      const dataset = await loadSampleDataset();
      onDatasetLoaded(dataset);
    } catch (err) {
      handleError(err);
    }
  };

  const doLoadMfgSample = async () => {
    setError(null);
    setLoading("sample-mfg");
    try {
      const dataset = await loadSampleManufacturingDataset();
      onDatasetLoaded(dataset);
    } catch (err) {
      handleError(err);
    }
  };

  const doUpload = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".csv")) {
        setError("Only .csv files are supported by the validation engine.");
        return;
      }
      setError(null);
      setLoading("upload");
      try {
        const dataset = await uploadDataset(file);
        onDatasetLoaded(dataset);
      } catch (err) {
        handleError(err);
      }
    },
    [onDatasetLoaded]
  );

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void doUpload(file);
    e.target.value = "";
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void doUpload(file);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const onDragLeave = () => setDragging(false);

  const isLoading = loading !== "idle";

  return (
    <div className="hero-editorial">
      {/* ── TOP EDITORIAL SECTION ─────────────────────────────────── */}
      <div className="hero-editorial-grid">
        <div className="hero-editorial-left">
          <div className="hero-kicker">
            Data Reliability Lab // Phase 01: Stress Testing
          </div>

          <h1 className="hero-title">
            YOUR DATA LOOKS FINE.
            <span className="title-accent">PROVE IT.</span>
          </h1>

          <p className="hero-lead">
            Stress-test your data-quality safeguards before silent failures reach
            your business metrics. DataTripwire injects controlled mutations into
            live pipelines to verify if your validation rules catch or leak corrupt data.
          </p>

          <div className="hero-actions-bar" style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
            <button
              id="btn-load-sample"
              className="btn btn-signal btn-lg"
              onClick={doLoadSample}
              disabled={isLoading}
              aria-busy={loading === "sample"}
              title="Load E-commerce Sales canonical dataset"
            >
              {loading === "sample" ? (
                <>
                  <span className="spinner" />
                  <span>Loading Sales Demo…</span>
                </>
              ) : (
                <>
                  <span>⚡</span>
                  <span>Sales Demo (15 Tx)</span>
                </>
              )}
            </button>

            <button
              id="btn-load-sample-mfg"
              className="btn btn-primary btn-lg"
              onClick={doLoadMfgSample}
              disabled={isLoading}
              aria-busy={loading === "sample-mfg"}
              title="Load Manufacturing Industrial IoT telemetry dataset"
            >
              {loading === "sample-mfg" ? (
                <>
                  <span className="spinner" />
                  <span>Loading IoT Demo…</span>
                </>
              ) : (
                <>
                  <span>⚙️</span>
                  <span>Mfg IoT Demo (20 Rdg)</span>
                </>
              )}
            </button>

            <button
              id="btn-upload-custom-csv"
              className="btn btn-secondary btn-lg"
              onClick={() => !isLoading && fileRef.current?.click()}
              disabled={isLoading}
            >
              <span>📁</span>
              <span>Upload Custom CSV</span>
            </button>
          </div>

          <div className="hero-meta-strip">
            <div className="hero-meta-item">
              <span className="hero-meta-label">Testing Paradigm</span>
              <span className="hero-meta-value">Mutation Testing</span>
            </div>
            <div className="hero-meta-item">
              <span className="hero-meta-label">Ground Truth</span>
              <span className="hero-meta-value">Deterministic Seed</span>
            </div>
            <div className="hero-meta-item">
              <span className="hero-meta-label">Impact Metric</span>
              <span className="hero-meta-value">Revenue Integrity</span>
            </div>
          </div>
        </div>

        {/* Right side: Summary Specs & Ingestion options */}
        <div className="hero-editorial-right">
          {/* Dropzone container */}
          <div
            id="upload-dropzone"
            className={`upload-zone ${dragging ? "drag-over" : ""}`}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onClick={() => !isLoading && fileRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Upload CSV file"
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") fileRef.current?.click();
            }}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              onChange={onFileChange}
              aria-hidden="true"
              tabIndex={-1}
            />
            <div className="upload-icon-box">
              {loading === "upload" ? <span className="spinner spinner-dark" /> : "CSV"}
            </div>
            <h3 style={{ marginBottom: "6px" }}>Drop pipeline CSV here</h3>
            <p style={{ fontSize: "0.82rem", maxWidth: "260px", marginBottom: "16px" }}>
              Requires <code>transaction_id, customer_id, quantity, unit_price, transaction_date</code>
            </p>
            <span className="badge badge-muted">
              Auto-Profiled · Max 10MB
            </span>
          </div>

          {error && (
            <div className="alert alert-danger" style={{ marginTop: "16px" }}>
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── CUSTOM SVG DATA-FLOW VISUALIZATION ─────────────────────── */}
      <div style={{ marginTop: "54px" }}>
        <PipelineIllustration
          mode="hero"
          mutationType="duplicate_row"
          hasUniquenessRule={false}
          status="neutral"
        />
      </div>

      {/* ── 3-STEP METHODOLOGY BAR ─────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "24px",
          marginTop: "16px",
        }}
      >
        <div className="card">
          <div className="badge badge-muted" style={{ marginBottom: "10px" }}>01 // INJECT</div>
          <h4 style={{ marginBottom: "6px" }}>Controlled Fault Injection</h4>
          <p style={{ fontSize: "0.82rem" }}>
            Introduce precise mutations (duplicates, missing values, corrupt prices) without contaminating source records.
          </p>
        </div>

        <div className="card">
          <div className="badge badge-muted" style={{ marginBottom: "10px" }}>02 // EVALUATE</div>
          <h4 style={{ marginBottom: "6px" }}>Safeguard Verification</h4>
          <p style={{ fontSize: "0.82rem" }}>
            Execute existing data quality validation rules to observe whether checkpoints detect or leak the fault.
          </p>
        </div>

        <div className="card">
          <div className="badge badge-muted" style={{ marginBottom: "10px" }}>03 // EVIDENCE</div>
          <h4 style={{ marginBottom: "6px" }}>Business Drift Analysis</h4>
          <p style={{ fontSize: "0.82rem" }}>
            Measure real ledger impact on revenue metrics and synthesize automated rule recommendations.
          </p>
        </div>
      </div>
    </div>
  );
}
