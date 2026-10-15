/**
 * ConfigureView (The Mutation Lab).
 *
 * Engineering workbench for synthesizing controlled data faults,
 * selecting validation safeguards, and triggering evaluations.
 */

import { useState } from "react";
import { runEvaluation } from "../api/client";
import type {
  DatasetResponse,
  EvaluationCreateRequest,
  EvaluationReport,
  MutationBuilder,
  MutationType,
  ValidationRuleConfig,
} from "../types/api";

interface ConfigureViewProps {
  dataset: DatasetResponse;
  onEvaluationComplete: (report: EvaluationReport) => void;
  presetRules?: Partial<ValidationRuleConfig> | null;
  initialUniqueness?: boolean;
}

const MUTATION_TYPES: { value: MutationType; label: string; description: string }[] = [
  {
    value: "duplicate_row",
    label: "Duplicate Row",
    description: "Clones target transaction (e.g. ORD-101) to simulate upstream ingestion replay.",
  },
  {
    value: "missing_required_value",
    label: "Missing Required Value",
    description: "Nullifies a mandatory column to test schema non-null enforcement.",
  },
  {
    value: "invalid_quantity",
    label: "Invalid Quantity",
    description: "Sets item quantity to zero or negative to test range rules.",
  },
  {
    value: "invalid_unit_price",
    label: "Invalid Unit Price",
    description: "Sets price to a negative value to test domain non-negative validation.",
  },
  {
    value: "dropped_row",
    label: "Dropped Row",
    description: "Deletes a transaction to test row-count reconciliation safeguards.",
  },
];

const DEFAULT_RULES: ValidationRuleConfig = {
  check_required_columns: true,
  check_required_values: true,
  check_quantity_positive: true,
  check_unit_price_nonnegative: true,
  check_valid_transaction_date: true,
  check_unique_transaction_id: false, // Core demo: disabled by default!
  check_expected_row_count: false,
  expected_row_count: null,
};

const RULE_DEFINITIONS: {
  key: keyof ValidationRuleConfig;
  name: string;
  desc: string;
  isKeyDemo?: boolean;
}[] = [
  {
    key: "check_unique_transaction_id",
    name: "Unique Transaction ID",
    desc: "Enforces that transaction_id is distinct. Toggle this to test duplicate escape vs detection.",
    isKeyDemo: true,
  },
  {
    key: "check_required_columns",
    name: "Schema Completeness",
    desc: "Requires all mandated columns to exist in the record stream.",
  },
  {
    key: "check_required_values",
    name: "Non-Null Values",
    desc: "Ensures essential columns contain non-null values.",
  },
  {
    key: "check_quantity_positive",
    name: "Positive Quantity Check",
    desc: "Verifies item quantity is strictly > 0.",
  },
  {
    key: "check_unit_price_nonnegative",
    name: "Non-negative Unit Price",
    desc: "Verifies unit price is ≥ $0.00.",
  },
  {
    key: "check_valid_transaction_date",
    name: "ISO-8601 Date Format",
    desc: "Validates YYYY-MM-DD date parsing.",
  },
  {
    key: "check_expected_row_count",
    name: "Row Count Reconciliation",
    desc: "Validates stream count matches expected baseline (detects dropped rows).",
  },
];

let uidSeq = 0;
const generateId = () => `mut-${++uidSeq}`;

function createDefaultDuplicate(): MutationBuilder {
  return {
    id: generateId(),
    mutation_type: "duplicate_row",
    target_transaction_id: "ORD-101",
    target_column: "",
    value: "",
    description: "Duplicate transaction ORD-101 (₹800 revenue impact)",
  };
}

export function ConfigureView({
  dataset,
  onEvaluationComplete,
  presetRules,
  initialUniqueness = false,
}: ConfigureViewProps) {
  const [mutations, setMutations] = useState<MutationBuilder[]>([createDefaultDuplicate()]);
  const [rules, setRules] = useState<ValidationRuleConfig>(() => ({
    ...DEFAULT_RULES,
    ...(initialUniqueness ? { check_unique_transaction_id: true } : {}),
    ...(presetRules ?? {}),
  }));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addMutation = () => {
    setMutations((prev) => [
      ...prev,
      {
        id: generateId(),
        mutation_type: "duplicate_row",
        target_transaction_id: "ORD-102",
        target_column: "",
        value: "",
        description: "",
      },
    ]);
  };

  const updateMutation = (id: string, patch: Partial<MutationBuilder>) => {
    setMutations((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)));
  };

  const removeMutation = (id: string) => {
    setMutations((prev) => prev.filter((m) => m.id !== id));
  };

  const toggleRule = (key: keyof ValidationRuleConfig) => {
    setRules((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const setUniquenessRule = (enable: boolean) => {
    setRules((prev) => ({ ...prev, check_unique_transaction_id: enable }));
  };

  const buildPayload = (): EvaluationCreateRequest => ({
    mutations: mutations.map((m) => {
      const item: EvaluationCreateRequest["mutations"][0] = {
        mutation_type: m.mutation_type,
        target_transaction_id: m.target_transaction_id || undefined,
        description: m.description || undefined,
      };
      if (m.target_column) item.target_column = m.target_column;
      if (m.value !== "") item.value = Number(m.value);
      return item;
    }),
    rules,
  });

  const handleRun = async () => {
    if (mutations.length === 0) {
      setError("Please add at least one synthetic mutation to evaluate.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const payload = buildPayload();
      const report = await runEvaluation(dataset.profile.dataset_id, payload);
      onEvaluationComplete(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation execution failed.");
    } finally {
      setLoading(false);
    }
  };

  const isUniquenessActive = rules.check_unique_transaction_id;

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
            Workbench // Mutation Configuration
          </div>
          <h2 style={{ marginBottom: "6px" }}>The Mutation Lab</h2>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            DATASET: {dataset.filename} · {dataset.profile.row_count} BASELINE RECORDS
          </p>
        </div>

        <button
          id="btn-run-evaluation"
          className="btn btn-signal btn-lg"
          onClick={handleRun}
          disabled={loading || mutations.length === 0}
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="spinner" />
              <span>Executing Evaluation Engine…</span>
            </>
          ) : (
            <>
              <span>⚡</span>
              <span>
                Execute Evaluation ({mutations.length} {mutations.length === 1 ? "Fault" : "Faults"}) →
              </span>
            </>
          )}
        </button>
      </div>

      {/* ── CORE HACKATHON DEMO CONTROL BANNER ────────────────────── */}
      <div className="demo-preset-banner">
        <div className="demo-preset-info">
          <div className="demo-preset-title">
            DEMO TRIPWIRE SCENARIO: DUPLICATE ROW EVALUATION
          </div>
          <div className="demo-preset-desc">
            {isUniquenessActive ? (
              <span>
                <strong>HARDENED STATE:</strong> Unique Transaction ID check is{" "}
                <strong>ENABLED</strong>. Injected duplicates will be trapped and blocked at the
                validation gate.
              </span>
            ) : (
              <span>
                <strong>BASELINE VULNERABILITY:</strong> Unique Transaction ID check is{" "}
                <strong>DISABLED</strong>. Injected duplicate ORD-101 will silently bypass
                safeguards and inflate revenue by +₹800.
              </span>
            )}
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", flexShrink: 0 }}>
          <button
            type="button"
            className={`btn btn-sm ${!isUniquenessActive ? "btn-signal" : "btn-secondary"}`}
            onClick={() => setUniquenessRule(false)}
          >
            Step 1: Uniqueness OFF (Silent Escape)
          </button>
          <button
            type="button"
            className={`btn btn-sm ${isUniquenessActive ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setUniquenessRule(true)}
          >
            Step 2: Uniqueness ON (Trapped)
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: "20px" }}>
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* ── WORKBENCH GRID ────────────────────────────────────────── */}
      <div className="lab-layout">
        {/* Left: Mutation Synthesizer */}
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
              <h3 style={{ marginBottom: "2px" }}>Active Mutation Vectors</h3>
              <p style={{ fontSize: "0.8rem" }}>
                Synthetic anomalies injected into isolated copies of the dataset
              </p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={addMutation}>
              + Add Mutation
            </button>
          </div>

          {mutations.map((mut, idx) => {
            const mutDef = MUTATION_TYPES.find((m) => m.value === mut.mutation_type);
            const needsColumn =
              mut.mutation_type === "missing_required_value" ||
              mut.mutation_type === "invalid_quantity" ||
              mut.mutation_type === "invalid_unit_price";
            const needsValue =
              mut.mutation_type === "invalid_quantity" ||
              mut.mutation_type === "invalid_unit_price";

            return (
              <div key={mut.id} className="mutation-card-item">
                <div className="mutation-card-header">
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        fontSize: "0.76rem",
                        color: "var(--clr-signal-orange)",
                      }}
                    >
                      FAULT #{idx + 1}
                    </span>
                    <span className="badge badge-orange">{mutDef?.label}</span>
                  </div>

                  {mutations.length > 1 && (
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => removeMutation(mut.id)}
                      style={{ color: "var(--clr-danger)" }}
                      title="Remove mutation"
                    >
                      Remove
                    </button>
                  )}
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "14px",
                    marginBottom: "12px",
                  }}
                >
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor={`mut-type-${mut.id}`}>
                      Mutation Class
                    </label>
                    <select
                      id={`mut-type-${mut.id}`}
                      className="form-control"
                      value={mut.mutation_type}
                      onChange={(e) =>
                        updateMutation(mut.id, {
                          mutation_type: e.target.value as MutationType,
                        })
                      }
                    >
                      {MUTATION_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor={`mut-target-${mut.id}`}>
                      Target Transaction ID
                    </label>
                    <input
                      id={`mut-target-${mut.id}`}
                      className="form-control"
                      type="text"
                      placeholder="e.g. ORD-101"
                      value={mut.target_transaction_id}
                      onChange={(e) =>
                        updateMutation(mut.id, { target_transaction_id: e.target.value })
                      }
                    />
                  </div>
                </div>

                {needsColumn && (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: needsValue ? "1fr 1fr" : "1fr",
                      gap: "14px",
                      marginBottom: "12px",
                    }}
                  >
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label" htmlFor={`mut-col-${mut.id}`}>
                        Target Column
                      </label>
                      <select
                        id={`mut-col-${mut.id}`}
                        className="form-control"
                        value={mut.target_column}
                        onChange={(e) =>
                          updateMutation(mut.id, { target_column: e.target.value })
                        }
                      >
                        <option value="">Select column…</option>
                        {dataset.profile.column_names.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </div>

                    {needsValue && (
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label className="form-label" htmlFor={`mut-val-${mut.id}`}>
                          Corrupt Numerical Value
                        </label>
                        <input
                          id={`mut-val-${mut.id}`}
                          className="form-control"
                          type="number"
                          placeholder="-1 or 0"
                          value={mut.value}
                          onChange={(e) =>
                            updateMutation(mut.id, { value: e.target.value })
                          }
                        />
                      </div>
                    )}
                  </div>
                )}

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" htmlFor={`mut-desc-${mut.id}`}>
                    Hypothesis / Description
                  </label>
                  <input
                    id={`mut-desc-${mut.id}`}
                    className="form-control"
                    type="text"
                    placeholder="e.g. Duplicate row injection to verify uniqueness constraint"
                    value={mut.description}
                    onChange={(e) =>
                      updateMutation(mut.id, { description: e.target.value })
                    }
                  />
                </div>

                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--clr-text-secondary)",
                    marginTop: "10px",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  ENGINE BEHAVIOR: {mutDef?.description}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Validation Rule Enforcements */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Validation Checkpoints</div>
              <div className="card-subtitle">
                Rules currently active in the pipeline test harness
              </div>
            </div>
            <span className="badge badge-navy">
              {Object.values(rules).filter((v) => v === true).length} Enabled
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            {RULE_DEFINITIONS.map(({ key, name, desc, isKeyDemo }) => {
              const checked = Boolean(rules[key]);
              return (
                <div
                  key={key}
                  className={`rule-toggle-row ${isKeyDemo ? "highlighted" : ""}`}
                >
                  <div className="rule-info">
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span className="rule-name">{name}</span>
                      {isKeyDemo && (
                        <span className="badge badge-orange" style={{ fontSize: "0.62rem" }}>
                          DEMO PIVOT
                        </span>
                      )}
                    </div>
                    <div className="rule-desc">{desc}</div>
                  </div>

                  <input
                    id={`rule-toggle-${key}`}
                    type="checkbox"
                    className={`switch-input ${isKeyDemo ? "switch-orange" : ""}`}
                    checked={checked}
                    onChange={() => toggleRule(key)}
                    aria-label={`Toggle ${name}`}
                  />
                </div>
              );
            })}
          </div>

          <div
            style={{
              marginTop: "20px",
              paddingTop: "16px",
              borderTop: "1px solid var(--clr-border)",
            }}
          >
            <button
              className="btn btn-signal w-full"
              onClick={handleRun}
              disabled={loading || mutations.length === 0}
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  <span>Evaluating Pipeline…</span>
                </>
              ) : (
                <>Run Mutation Experiment →</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
