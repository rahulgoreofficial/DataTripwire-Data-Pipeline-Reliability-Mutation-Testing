/**
 * DataTripwire — Root Application Shell.
 *
 * "THE DATA RELIABILITY LAB"
 * Orchestrates the end-to-end workflow:
 * 01 OVERVIEW → 02 DATASET PROFILE → 03 MUTATION LAB → 04 INVESTIGATION
 */

import { useState } from "react";
import type { AppView, DatasetResponse, EvaluationReport, ValidationRuleConfig } from "./types/api";
import { Navbar } from "./components/Navbar";
import { UploadView } from "./components/UploadView";
import { ProfileView } from "./components/ProfileView";
import { ConfigureView } from "./components/ConfigureView";
import { ResultsView } from "./components/ResultsView";

type StepDef = { view: AppView; label: string; num: string };
const STEPS: StepDef[] = [
  { view: "upload", label: "Overview & Ingest", num: "01" },
  { view: "profile", label: "Dataset Profile", num: "02" },
  { view: "configure", label: "Mutation Lab", num: "03" },
  { view: "results", label: "Investigation", num: "04" },
];

const VIEW_ORDER: AppView[] = ["upload", "profile", "configure", "results"];

export default function App() {
  const [view, setView] = useState<AppView>("upload");
  const [dataset, setDataset] = useState<DatasetResponse | null>(null);
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [presetRules, setPresetRules] = useState<Partial<ValidationRuleConfig> | null>(null);
  const [activeDomain, setActiveDomain] = useState<string>("sales");

  const currentIdx = VIEW_ORDER.indexOf(view);

  const canAccess = (v: AppView): boolean => {
    switch (v) {
      case "upload":
        return true;
      case "profile":
        return dataset !== null;
      case "configure":
        return (
          dataset !== null &&
          (Boolean(dataset.profile.is_sales_compatible) ||
            Boolean(dataset.profile.is_manufacturing_compatible) ||
            Boolean(dataset.is_sales_compatible) ||
            Boolean(dataset.is_manufacturing_compatible))
        );
      case "results":
        return report !== null;
    }
  };

  const isDone = (v: AppView): boolean => {
    const idx = VIEW_ORDER.indexOf(v);
    return idx < currentIdx;
  };

  const handleDatasetLoaded = (ds: DatasetResponse) => {
    setDataset(ds);
    setReport(null);
    setPresetRules(null);
    const isMfg = Boolean(
      ds.profile.is_manufacturing_compatible ||
      ds.is_manufacturing_compatible ||
      ds.profile.detected_domain === "manufacturing"
    );
    const isSales = Boolean(ds.profile.is_sales_compatible || ds.is_sales_compatible);
    setActiveDomain(isMfg ? "manufacturing" : isSales ? "sales" : "general");
    setView("profile");
  };

  const handleProceedToConfigure = (domain?: string) => {
    if (domain) {
      setActiveDomain(domain);
    }
    setView("configure");
  };

  const handleEvaluationComplete = (r: EvaluationReport) => {
    setReport(r);
    setView("results");
  };

  const handleResetToConfigure = () => {
    setView("configure");
  };

  const handleRetestWithSafeguard = (ruleKey: string) => {
    setPresetRules({ [ruleKey]: true });
    setView("configure");
  };

  const handleResetToOverview = () => {
    setView("upload");
  };

  return (
    <div className="app-layout">
      {/* Precision Top Navbar */}
      <Navbar onResetToOverview={handleResetToOverview} />

      {/* Engineering Step Navigation Bar */}
      <nav className="step-tabs-bar" aria-label="Workflow Steps">
        <div className="container">
          <div className="step-tabs" role="tablist">
            {STEPS.map(({ view: v, label, num }) => (
              <button
                key={v}
                id={`tab-${v}`}
                role="tab"
                aria-selected={view === v}
                aria-controls={`panel-${v}`}
                className={[
                  "step-tab",
                  view === v ? "active" : "",
                  isDone(v) ? "done" : "",
                ]
                  .join(" ")
                  .trim()}
                disabled={!canAccess(v)}
                onClick={() => canAccess(v) && setView(v)}
              >
                <span className="step-num">{isDone(v) ? "✓" : num}</span>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Lab Content Area */}
      <main className="main-content" role="main">
        <div className="container">
          {/* View 1: Overview & Ingest */}
          <section
            id="panel-upload"
            role="tabpanel"
            aria-labelledby="tab-upload"
            hidden={view !== "upload"}
          >
            {view === "upload" && <UploadView onDatasetLoaded={handleDatasetLoaded} />}
          </section>

          {/* View 2: Dataset Profile */}
          <section
            id="panel-profile"
            role="tabpanel"
            aria-labelledby="tab-profile"
            hidden={view !== "profile"}
          >
            {view === "profile" && dataset && (
              <ProfileView
                dataset={dataset}
                onProceed={handleProceedToConfigure}
                activeDomain={activeDomain}
                onSelectDomain={setActiveDomain}
              />
            )}
          </section>

          {/* View 3: Mutation Lab */}
          <section
            id="panel-configure"
            role="tabpanel"
            aria-labelledby="tab-configure"
            hidden={view !== "configure"}
          >
            {view === "configure" && dataset && (
              <ConfigureView
                dataset={dataset}
                onEvaluationComplete={handleEvaluationComplete}
                presetRules={presetRules}
                activeDomain={activeDomain}
              />
            )}
          </section>

          {/* View 4: Results & Investigation */}
          <section
            id="panel-results"
            role="tabpanel"
            aria-labelledby="tab-results"
            hidden={view !== "results"}
          >
            {view === "results" && report && (
              <ResultsView
                report={report}
                onReset={handleResetToConfigure}
                onRetestWithSafeguard={handleRetestWithSafeguard}
                activeDomain={activeDomain}
              />
            )}
          </section>
        </div>
      </main>

      {/* Lab Engineering Footer */}
      <footer
        style={{
          borderTop: "1px solid var(--clr-border)",
          padding: "20px 0",
          backgroundColor: "var(--clr-surface)",
        }}
      >
        <div
          className="container"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "0.74rem",
            color: "var(--clr-text-secondary)",
            fontFamily: "var(--font-mono)",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontWeight: 700, color: "var(--clr-text-primary)" }}>DATATRIPWIRE</span>
            <span>// DATA RELIABILITY LAB · MUTATION TESTING ENGINE</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <span>100% LOCAL RUNTIME</span>
            <span>ZERO EXTERNAL CLOUD TELEMETRY</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
