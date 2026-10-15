# DataTripwire: Development Roadmap

This document outlines the three planned implementation phases for DataTripwire, defining scope, deliverables, and acceptance criteria for each milestone.

---

## Roadmap Summary

| Phase | Title | Focus Area | Status |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Foundation & Architecture** | Domain contracts, schemas, sample fixture, test suite | **COMPLETE** |
| **Phase 2** | **Backend Engines & API** | Ingestion, mutator, validator, simulator, evaluator, FastAPI | **COMPLETE** |
| **Phase 3** | **Frontend Application** | React, TypeScript, Vite, interactive dashboard, live demo | Planned |

---

## Phase 1: Foundation, Architecture, and Domain Models

### Objective
Establish a clean, type-safe architectural foundation, standard data contracts, deterministic baseline data, and validation tests without premature backend or UI implementations.

### Deliverables
- [x] **Product Definition & System Architecture**: Documented in `docs/product_overview.md` and `docs/architecture.md`.
- [x] **Project Scaffolding**: Standard package structure (`backend/src/datatripwire/`), `.gitignore`, `.env.example`, and `pyproject.toml`.
- [x] **Domain Models & Contracts**: Pydantic v2 models for `DatasetProfile`, `MutationSpec`, `PipelineMetrics`, `ValidationFinding`, `MutationEvaluation`, `RuleRecommendation`, and `EvaluationReport`.
- [x] **Domain Enumerations**: Standardized `MutationType`, `FindingSeverity`, `RuleType`, `RecommendationStatus`, and `EvaluationStatus`.
- [x] **Deterministic Sample Dataset**: Clean 15-record e-commerce dataset (`sample_sales.csv`) with verified baseline revenue of ₹19,000.00 across 10 customers.
- [x] **Foundation Test Suite**: 41 unit tests covering model validations, boundary checks, zero-denominator edge cases, and CSV schema conformance.

---

## Phase 2: Backend Services and REST API (Completed)

### Objective
Implement the tabular data processing engine, mutation injection mechanisms, pipeline simulation, and FastAPI HTTP service.

### Deliverables
- [x] **Dataset Ingestion & Profiler**: Bounded CSV ingestion, header validation, null profiling, and sales schema compatibility.
- [x] **Business Metrics Engine**: Exact Decimal revenue arithmetic, order volume, customer counts, and impact deltas.
- [x] **Synthetic Mutation Engine**: 5 isolated mutation operators acting on DataFrame deep copies.
- [x] **Configurable Validation Engine**: 7 data-quality checks with baseline uniqueness omitted by default.
- [x] **Core Evaluator**: Baseline vs. mutated finding fingerprint comparison and honest detection logic.
- [x] **Deterministic Recommender**: Structured rule suggestions for escaping mutations.
- [x] **FastAPI REST API**: Versioned endpoints for sample loading, uploads, evaluations, and history.
- [x] **Automated Test Suite**: 115 passing tests across unit, evaluator scenarios, and API integration.
- [x] **Verified Demonstration**: 14-step end-to-end verification script.

### Planned Tasks & Modules
1. **Dataset Ingestion & Profiling Service** (`services/profiler.py`):
   - Ingest CSV tabular files via Pandas.
   - Infer data types, count nulls, and extract `DatasetProfile`.
2. **Mutation Injection Engine** (`services/mutator.py`):
   - `apply_mutation(df: pd.DataFrame, spec: MutationSpec) -> pd.DataFrame`
   - Implement:
     - `duplicate_row`: Duplicate specific transaction or random record.
     - `missing_required_value`: Set target cell to NaN/None.
     - `invalid_quantity`: Inject zero or negative quantity values.
     - `invalid_unit_price`: Inject negative unit price.
     - `dropped_row`: Remove specified record.
   - Operate strictly on DataFrame copies to preserve fixture immutability.
3. **Data-Quality Validation Engine** (`services/validator.py`):
   - Configurable rule definitions:
     - `NotNullRule(column)`
     - `PositiveValueRule(column)`
     - `NonNegativeValueRule(column)`
     - `DateFormatRule(column)`
     - `UniquenessRule(column)` (*Configurable: omitted in baseline suite*)
   - Returns structured `List[ValidationFinding]`.
4. **Pipeline Simulation & Impact Evaluator** (`services/evaluator.py`):
   - Compute baseline and mutated `PipelineMetrics`.
   - Calculate revenue and transaction deltas.
   - Map validation findings to determine whether the mutation was detected or escaped.
5. **Rule Recommendation Engine** (`services/recommender.py`):
   - Deterministically map escaping faults to rule configurations (e.g., escaping duplicate -> uniqueness rule on primary key).
6. **FastAPI Application** (`api/main.py`):
   - `POST /api/dataset/upload`
   - `GET /api/dataset/sample`
   - `POST /api/mutate/evaluate`
   - `POST /api/recommendations/retest`
7. **Backend Test Suite**:
   - Unit tests for all mutators, validators, and evaluator logic.
   - Integration tests verifying HTTP endpoints with TestClient.

---

## Phase 3: Frontend Web Application

### Objective
Build a modern, intuitive, responsive user interface using React, TypeScript, and Vite that allows users to crash-test data pipelines and observe downstream impacts.

### Planned Views & Features
1. **Data Ingestion View**:
   - Drag-and-drop CSV upload or one-click load of sample dataset.
   - Tabular preview and profiling metadata cards.
2. **Crash-Testing Cockpit**:
   - Interactive mutation selector with parameter controls.
   - Toggle baseline rules vs. hardened rules.
3. **Downstream Impact Dashboard**:
   - Side-by-side metric comparison cards (Baseline vs. Mutated).
   - Dynamic delta indicators (e.g., "Revenue error: +₹800.00").
   - Status badge: "FAULT ESCAPED" (red) or "FAULT DETECTED" (green).
4. **Rule Recommendation Console**:
   - Display actionable rule suggestions.
   - "Apply Rule & Re-test" button triggering live re-evaluation.
   - Visual before-and-after mutation score comparison (0% -> 100%).
5. **UX Polish**:
   - Fluid transitions, glassmorphic dark theme, loading spinners, empty states, and error toasts.

---

## Milestone Transition Criteria

Before commencing Phase 2:
1. All Phase 1 foundation tests must pass without errors.
2. All domain models and contracts must be finalized and frozen.
3. Sample datasets must be confirmed deterministic and verified.
