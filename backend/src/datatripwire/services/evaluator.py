"""Core evaluation engine for DataTripwire.

Orchestrates independent synthetic mutation testing against tabular datasets:
- Baseline metrics and baseline findings extraction
- Isolated mutation application on fresh DataFrame copies
- Baseline vs. mutated finding fingerprint comparison
- Data-driven fault detection matching (no hardcoded detection flags)
- Downstream business impact quantification
- Deterministic rule recommendations for surviving faults
- Evaluation report generation and mutation scoring
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
import uuid
import pandas as pd

from datatripwire.config import SALES_SCHEMA_COLUMNS
from datatripwire.domain.enums import MutationType
from datatripwire.domain.models import (
    EvaluationReport,
    MutationEvaluation,
    MutationSpec,
    PipelineMetrics,
    ValidationFinding,
)
from datatripwire.exceptions import IncompatibleSchemaError
from datatripwire.schemas import MutationRequestItem, ValidationRuleConfig
from datatripwire.services.metrics import calculate_metric_deltas, calculate_sales_metrics
from datatripwire.services.mutation_engine import apply_mutation
from datatripwire.services.recommendations import generate_recommendations_for_surviving_mutations
from datatripwire.services.validators import (
    RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH,
    RULE_CODE_QUANTITY_NOT_POSITIVE,
    RULE_CODE_REQUIRED_VALUE_MISSING,
    RULE_CODE_TRANSACTION_ID_DUPLICATE,
    RULE_CODE_UNIT_PRICE_NEGATIVE,
    compute_finding_fingerprint,
    run_validation,
)


def _is_finding_relevant_to_mutation(
    finding: ValidationFinding,
    mutation_meta: Dict[str, Any],
) -> bool:
    """Determine whether a newly introduced validation finding matches the injected mutation fault."""
    expected_rule = mutation_meta.get("expected_rule_code")
    if not expected_rule or finding.rule_id != expected_rule:
        return False

    target_rec = mutation_meta.get("target_record_id")
    target_col = mutation_meta.get("target_column")

    # Column match check if applicable
    if target_col and finding.affected_column and finding.affected_column != target_col:
        return False

    # Record match check if applicable
    if target_rec and finding.affected_record_ids:
        if target_rec not in finding.affected_record_ids:
            return False

    return True


class EvaluationService:
    """Service orchestrating dataset evaluations and mutation testing runs."""

    def evaluate_dataset(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        mutations: List[MutationRequestItem],
        rules: Optional[ValidationRuleConfig] = None,
        report_id: Optional[str] = None,
    ) -> EvaluationReport:
        """Run an evaluation batch on a dataset.
        
        Args:
            df: Immutable baseline DataFrame.
            dataset_id: Target dataset identifier.
            mutations: List of mutation request specifications.
            rules: Validation rules configuration to apply.
            report_id: Optional custom report ID (generates UUID if omitted).
            
        Returns:
            Fully populated EvaluationReport instance.
            
        Raises:
            IncompatibleSchemaError if dataset lacks canonical sales columns.
        """
        # Validate sales schema compatibility
        missing_sales_cols = [c for c in SALES_SCHEMA_COLUMNS if c not in df.columns]
        if missing_sales_cols:
            raise IncompatibleSchemaError(missing_sales_cols)

        rule_config = rules or ValidationRuleConfig()
        rep_id = report_id or f"REP-{uuid.uuid4().hex[:8].upper()}"
        baseline_row_count = len(df)

        # 1. Compute baseline business metrics
        baseline_metrics = calculate_sales_metrics(df)

        # 2. Extract baseline validation findings on original clean data
        # For expected row count, reference is the baseline row count itself
        baseline_findings = run_validation(
            df,
            config=rule_config,
            reference_row_count=baseline_row_count,
        )
        baseline_fingerprints: Set[str] = {
            compute_finding_fingerprint(f) for f in baseline_findings
        }

        evaluations: List[MutationEvaluation] = []
        surviving_evals: List[MutationEvaluation] = []

        # 3. Process each mutation independently against a fresh copy of the original dataset
        for idx, m_req in enumerate(mutations):
            mut_id = f"MUT-{idx + 1:03d}"
            desc = m_req.description or f"Evaluate {m_req.mutation_type.value} on {m_req.target_transaction_id or 'default'}"

            spec = MutationSpec(
                mutation_id=mut_id,
                mutation_type=m_req.mutation_type,
                target_column=m_req.target_column,
                target_record_id=m_req.target_transaction_id,
                params={
                    **m_req.params,
                    **({"value": m_req.value} if m_req.value is not None else {}),
                    **({"target_transaction_id": m_req.target_transaction_id} if m_req.target_transaction_id else {}),
                },
                description=desc,
                reproducibility_seed=m_req.reproducibility_seed,
            )

            # Apply mutation to a fresh deep copy
            mutated_df, mut_meta = apply_mutation(df, spec)

            if not mut_meta.get("applied", False):
                # Mutation could not be applied
                evaluations.append(
                    MutationEvaluation(
                        mutation_spec=spec,
                        applied=False,
                        detected=None,
                        findings=[],
                        baseline_metrics=baseline_metrics,
                        mutated_metrics=None,
                        metric_deltas=None,
                        failure_reason=mut_meta.get("failure_reason", "Mutation injection failed"),
                    )
                )
                continue

            # Compute mutated pipeline metrics
            mutated_metrics = calculate_sales_metrics(mutated_df)
            metric_deltas = calculate_metric_deltas(baseline_metrics, mutated_metrics)

            # Run validation suite on mutated dataset copy
            # Use original baseline_row_count as reference so dropped rows can be detected if enabled
            mutated_findings = run_validation(
                mutated_df,
                config=rule_config,
                reference_row_count=baseline_row_count,
            )

            # Isolate NEW findings introduced by the mutation
            new_findings: List[ValidationFinding] = []
            for f in mutated_findings:
                fp = compute_finding_fingerprint(f)
                if fp not in baseline_fingerprints:
                    new_findings.append(f)

            # Determine detection strictly from actual relevant new findings
            detected = False
            for nf in new_findings:
                if _is_finding_relevant_to_mutation(nf, mut_meta):
                    detected = True
                    break

            eval_item = MutationEvaluation(
                mutation_spec=spec,
                applied=True,
                detected=detected,
                findings=mutated_findings,
                baseline_metrics=baseline_metrics,
                mutated_metrics=mutated_metrics,
                metric_deltas=metric_deltas,
                failure_reason=None,
            )
            evaluations.append(eval_item)

            if not detected:
                surviving_evals.append(eval_item)

        # 4. Generate recommendations for surviving mutations
        recommendations = generate_recommendations_for_surviving_mutations(surviving_evals)

        # 5. Calculate summary totals
        total_attempted = len(mutations)
        successfully_applied = sum(1 for e in evaluations if e.applied)
        detected_mutations = sum(1 for e in evaluations if e.applied and e.detected is True)
        surviving_mutations = sum(1 for e in evaluations if e.applied and e.detected is False)
        failed_evaluations = sum(1 for e in evaluations if not e.applied)

        # Compute aggregate summary deltas across all applied mutations
        aggregate_revenue_deltas = [
            Decimal(e.metric_deltas["revenue_delta_abs"])
            for e in evaluations
            if e.metric_deltas and "revenue_delta_abs" in e.metric_deltas
        ]
        max_rev_impact = max(aggregate_revenue_deltas, key=abs) if aggregate_revenue_deltas else Decimal("0.00")

        summary_deltas = {
            "baseline_revenue": str(baseline_metrics.total_revenue),
            "baseline_transaction_count": baseline_metrics.transaction_count,
            "max_revenue_impact_abs": str(max_rev_impact),
            "total_surviving": surviving_mutations,
            "total_detected": detected_mutations,
        }

        return EvaluationReport(
            report_id=rep_id,
            dataset_id=dataset_id,
            created_at=datetime.now(timezone.utc),
            total_attempted=total_attempted,
            successfully_applied=successfully_applied,
            detected_mutations=detected_mutations,
            surviving_mutations=surviving_mutations,
            failed_evaluations=failed_evaluations,
            evaluations=evaluations,
            recommendations=recommendations,
            baseline_metrics=baseline_metrics,
            summary_deltas=summary_deltas,
            metadata={
                "evaluated_rules": rule_config.model_dump(),
                "dataset_row_count": baseline_row_count,
            },
        )
