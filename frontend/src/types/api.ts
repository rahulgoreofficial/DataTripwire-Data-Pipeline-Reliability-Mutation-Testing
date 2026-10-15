/**
 * TypeScript type definitions mirroring the DataTripwire backend API contracts.
 * All types are derived from the Pydantic domain models and API schemas.
 */

// ─── Enumerations ─────────────────────────────────────────────────────────────

export type DataDomain = "sales" | "manufacturing" | "general";

export type MutationType =
  // Sales
  | "duplicate_row"
  | "missing_required_value"
  | "invalid_quantity"
  | "invalid_unit_price"
  | "dropped_row"
  // Manufacturing
  | "duplicate_sensor_reading"
  | "missing_sensor_value"
  | "invalid_sensor_value"
  | "dropped_sensor_reading"
  | "invalid_production_value";

export type FindingSeverity = "critical" | "high" | "medium" | "low" | "info";

export type RuleType =
  | "uniqueness"
  | "completeness"
  | "not_null"
  | "range"
  | "value_range"
  | "format"
  | "data_type"
  | "date_validity"
  | "consistency"
  | "referential_integrity"
  | "row_count"
  | "schema";

export type RecommendationStatus = "suggested" | "accepted" | "rejected" | "implemented";

// ─── Domain Metadata ──────────────────────────────────────────────────────────

export interface DomainMetadata {
  domain_id: string;
  name: string;
  description: string;
  primary_key: string | null;
  required_columns: string[];
  schema_columns: string[];
  supported_mutation_types: string[];
  is_compatible?: boolean;
  missing_columns?: string[];
}

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
  is_manufacturing_compatible?: boolean;
  detected_domain?: string;
  domain_compatibility?: Record<string, boolean>;
  supported_domains?: DomainMetadata[];
  warnings: string[];
  created_at: string;
}

export interface PipelineMetrics {
  domain?: string;
  // Sales domain metrics
  total_revenue?: string | null;
  transaction_count?: number | null;
  customer_count?: number | null;
  average_order_value?: string | null;
  // Manufacturing IoT domain metrics
  total_readings?: number | null;
  unique_machines?: number | null;
  unique_facilities?: number | null;
  total_units_produced?: number | null;
  total_defect_count?: number | null;
  total_energy_kwh?: number | null;
  avg_temperature_c?: number | null;
  max_temperature_c?: number | null;
  avg_vibration_mm_s?: number | null;
  max_vibration_mm_s?: number | null;
  avg_pressure_bar?: number | null;
  avg_motor_current_a?: number | null;
  avg_quality_pass_rate_pct?: number | null;
  manufacturing_metrics?: Record<string, unknown>;
  additional_metrics?: Record<string, unknown>;
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
  // Sales rules
  check_required_columns?: boolean;
  check_required_values?: boolean;
  check_quantity_positive?: boolean;
  check_unit_price_nonnegative?: boolean;
  check_valid_transaction_date?: boolean;
  check_unique_transaction_id?: boolean;
  check_expected_row_count?: boolean;
  expected_row_count?: number | null;
  // Manufacturing rules
  check_reading_id_unique?: boolean;
  check_machine_timestamp_unique?: boolean;
  check_timestamp_validity?: boolean;
  check_sensor_numeric?: boolean;
  check_non_negative_measurements?: boolean;
  check_quality_pass_rate_bounds?: boolean;
  check_production_consistency?: boolean;
  check_temperature_bounds?: boolean;
  temperature_min_c?: number;
  temperature_max_c?: number;
  check_expected_record_count?: boolean;
  expected_record_count?: number | null;
}

export interface MutationRequestItem {
  mutation_type: MutationType;
  target_transaction_id?: string;
  target_record_id?: string;
  target_column?: string;
  value?: unknown;
  params?: Record<string, unknown>;
  description?: string;
  reproducibility_seed?: number;
}

export interface EvaluationCreateRequest {
  domain?: string;
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
  is_manufacturing_compatible?: boolean;
  detected_domain?: string;
  supported_domains?: DomainMetadata[];
  domain_compatibility?: Record<string, boolean>;
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
  target_transaction_id: string; // used for target record id
  target_record_id?: string; // used for manufacturing sensor reading id
  target_column: string;
  value: string;
  description: string;
}
