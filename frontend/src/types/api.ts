/**
 * TypeScript type definitions mirroring the DataTripwire backend API contracts.
 * All types are derived from the Pydantic domain models and API schemas.
 */

// ─── Enumerations ─────────────────────────────────────────────────────────────

export type MutationType =
  | "duplicate_row"
  | "missing_required_value"
  | "invalid_quantity"
  | "invalid_unit_price"
  | "dropped_row";

export type FindingSeverity = "critical" | "high" | "medium" | "low" | "info";

export type RuleType =
  | "uniqueness"
  | "completeness"
  | "range"
  | "format"
  | "referential_integrity"
  | "row_count"
  | "schema";

export type RecommendationStatus = "suggested" | "accepted" | "rejected" | "implemented";

// ─── Core Domain Models ───────────────────────────────────────────────────────

export interface DatasetProfile {
  dataset_id: string;
  filename: string;
  row_count: number;
  column_count: number;
  column_names: string[];
  column_types: Record<string, string>;
  null_counts: Record<string, number>;
  null_percentages: Record<string, number>;
  duplicate_row_count: number;
  numeric_summaries: Record<string, Record<string, number>>;
  is_sales_compatible: boolean;
  warnings: string[];
  created_at: string;
}

export interface PipelineMetrics {
  total_revenue: string; // Decimal serialized as string
  transaction_count: number;
  customer_count: number;
  average_order_value: string | null;
  additional_metrics: Record<string, unknown>;
}

export interface ValidationFinding {
  finding_id: string;
  rule_id: string;
  rule_type: RuleType;
  severity: FindingSeverity;
  affected_column: string | null;
  affected_record_ids: string[];
  explanation: string;
  detected: boolean;
}

export interface MutationSpec {
  mutation_id: string;
  mutation_type: MutationType;
  target_column: string | null;
  target_record_id: string | null;
  params: Record<string, unknown>;
  description: string;
  reproducibility_seed: number | null;
}

export interface MutationEvaluation {
  mutation_spec: MutationSpec;
  applied: boolean;
  detected: boolean | null;
  findings: ValidationFinding[];
  baseline_metrics: PipelineMetrics | null;
  mutated_metrics: PipelineMetrics | null;
  metric_deltas: Record<string, unknown> | null;
  failure_reason: string | null;
  evaluated_at: string | null;
}

export interface RuleRecommendation {
  recommendation_id: string;
  rule_type: RuleType;
  target_column: string | null;
  description: string;
  rationale: string;
  suggested_rule_config: Record<string, unknown>;
  code_snippet: string | null;
  status: RecommendationStatus;
}

export interface EvaluationReport {
  report_id: string;
  dataset_id: string;
  created_at: string;
  total_attempted: number;
  successfully_applied: number;
  detected_mutations: number;
  surviving_mutations: number;
  failed_evaluations: number;
  mutation_score: number | null;
  evaluations: MutationEvaluation[];
  recommendations: RuleRecommendation[];
  baseline_metrics: PipelineMetrics | null;
  summary_deltas: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
}

// ─── API Request/Response Schemas ─────────────────────────────────────────────

export interface ValidationRuleConfig {
  check_required_columns: boolean;
  check_required_values: boolean;
  check_quantity_positive: boolean;
  check_unit_price_nonnegative: boolean;
  check_valid_transaction_date: boolean;
  check_unique_transaction_id: boolean;
  check_expected_row_count: boolean;
  expected_row_count: number | null;
}

export interface MutationRequestItem {
  mutation_type: MutationType;
  target_transaction_id?: string;
  target_column?: string;
  value?: unknown;
  params?: Record<string, unknown>;
  description?: string;
  reproducibility_seed?: number;
}

export interface EvaluationCreateRequest {
  mutations: MutationRequestItem[];
  rules: ValidationRuleConfig;
  options?: Record<string, unknown>;
}

export interface DatasetResponse {
  dataset_id: string;
  filename: string;
  uploaded_at: string;
  profile: DatasetProfile;
  is_sales_compatible: boolean;
  warnings: string[];
}

export interface EvaluationSummaryItem {
  report_id: string;
  dataset_id: string;
  created_at: string;
  total_attempted: number;
  successfully_applied: number;
  detected_mutations: number;
  surviving_mutations: number;
  failed_evaluations: number;
  mutation_score: number | null;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  environment: string | null;
}

export interface ApiError {
  error: string;
  detail: string;
  code: string;
}

// ─── UI State Types ────────────────────────────────────────────────────────────

export type AppView = "upload" | "profile" | "configure" | "results";

export type LoadingState = "idle" | "loading" | "success" | "error";

export interface MutationBuilder {
  id: string; // local UI ID
  mutation_type: MutationType;
  target_transaction_id: string;
  target_column: string;
  value: string;
  description: string;
}
