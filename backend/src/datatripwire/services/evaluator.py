"""Core evaluation engine for DataTripwire.

Orchestrates independent synthetic mutation testing against tabular datasets:
- Domain resolution (Sales, Manufacturing, General)
- Baseline metrics and baseline findings extraction
- Isolated mutation application on fresh DataFrame copies
- Baseline vs. mutated finding fingerprint comparison
- Data-driven fault detection matching (no hardcoded detection flags)
- Downstream business or operational impact quantification
- Deterministic rule recommendations for surviving faults
- Evaluation report generation and mutation scoring
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
import uuid
import pandas as pd

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
from datatripwire.services.validators import compute_finding_fingerprint


def _is_finding_relevant_to_mutation(
    finding: ValidationFinding,
    mutation_meta: Dict[str, Any],
) -> bool:
    """Determine whether a newly introduced validation finding matches the injected mutation fault."""
    expected_rule = mutation_meta.get("expected_rule_code")
    alt_rules = mutation_meta.get("alternative_expected_rule_codes", [])

    if not expected_rule or (finding.rule_id != expected_rule and finding.rule_id not in alt_rules):
        return False

    target_rec = mutation_meta.get("target_record_id")
    target_col = mutation_meta.get("target_column")

    # Column match check if applicable
    if target_col and finding.affected_column and finding.affected_column != target_col:
        # Special case: composite machine/timestamp check affects machine_id or timestamp
        if not (target_col in ("reading_id", "transaction_id") and finding.affected_column in ("machine_id", "timestamp")):
            return False

    # Record match check if applicable
    if target_rec and finding.affected_record_ids:
        if target_rec not in finding.affected_record_ids:
            return False

    return True


class EvaluationService:
    """Service orchestrating dataset evaluations and mutation testing runs across domains."""

    def evaluate_dataset(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        mutations: List[MutationRequestItem],
        rules: Optional[ValidationRuleConfig] = None,
        report_id: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> EvaluationReport:
        """Run an evaluation batch on a dataset.
        
        Args:
            df: Immutable baseline DataFrame.
            dataset_id: Target dataset identifier.
            mutations: List of mutation request specifications.
            rules: Validation rules configuration to apply.
            report_id: Optional custom report ID (generates UUID if omitted).
            domain: Explicit domain selector ('sales', 'manufacturing') or auto-detect if None.
            
        Returns:
            Fully populated EvaluationReport instance.
            
        Raises:
            IncompatibleSchemaError if dataset lacks required columns for the domain.
        """
        from datatripwire.domains.registry import get_domain_registry
        registry = get_domain_registry()
        if domain:
            domain_profile = registry.get(domain)
        else:
            domain_profile = registry.detect_domain(df)

        # Check compatibility with the domain
        is_compat, missing_cols = domain_profile.is_compatible(df)
        if not is_compat:
            raise IncompatibleSchemaError(missing_cols)

        if domain_profile.domain_id == "general":
            raise IncompatibleSchemaError(
                ["General CSV Profiling datasets do not support mutation testing. "
                 "Please select or upload a dataset compatible with a supported domain."]
            )

        rule_config = rules or ValidationRuleConfig()
        rep_id = report_id or f"REP-{uuid.uuid4().hex[:8].upper()}"
        baseline_row_count = len(df)

        # 1. Compute baseline domain metrics
        baseline_metrics = domain_profile.calculate_metrics(df)

        # 2. Extract baseline validation findings on original clean data
        baseline_findings = domain_profile.validate(
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
            target_id = m_req.target_record_id or m_req.target_transaction_id
            desc = m_req.description or f"Evaluate {m_req.mutation_type.value} on {target_id or 'default'}"

            spec = MutationSpec(
                mutation_id=mut_id,
                mutation_type=m_req.mutation_type,
                target_column=m_req.target_column,
                target_record_id=target_id,
                params={
                    **m_req.params,
                    **({"value": m_req.value} if m_req.value is not None else {}),
                    **({"target_transaction_id": target_id} if target_id else {}),
                    **({"target_reading_id": target_id} if target_id else {}),
                },
                description=desc,
                reproducibility_seed=m_req.reproducibility_seed,
            )

            # Apply mutation to a fresh deep copy
            mutated_df, mut_meta = domain_profile.apply_mutation(df, spec)

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
            mutated_metrics = domain_profile.calculate_metrics(mutated_df)
            metric_deltas = domain_profile.calculate_metric_deltas(baseline_metrics, mutated_metrics)

            # Run validation suite on mutated dataset copy
            mutated_findings = domain_profile.validate(
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
                if domain_profile.is_finding_relevant_to_mutation(nf, mut_meta):
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
        recommendations = domain_profile.generate_recommendations(surviving_evals)

        # 5. Calculate summary totals
        total_attempted = len(mutations)
        successfully_applied = sum(1 for e in evaluations if e.applied)
        detected_mutations = sum(1 for e in evaluations if e.applied and e.detected is True)
        surviving_mutations = sum(1 for e in evaluations if e.applied and e.detected is False)
        failed_evaluations = sum(1 for e in evaluations if not e.applied)

        # Build domain-specific summary deltas
        summary_deltas: Dict[str, Any] = {
            "domain": domain_profile.domain_id,
            "total_surviving": surviving_mutations,
            "total_detected": detected_mutations,
        }

        if domain_profile.domain_id == "sales":
            aggregate_revenue_deltas = [
                Decimal(e.metric_deltas["revenue_delta_abs"])
                for e in evaluations
                if e.metric_deltas and "revenue_delta_abs" in e.metric_deltas
            ]
            max_rev_impact = max(aggregate_revenue_deltas, key=abs) if aggregate_revenue_deltas else Decimal("0.00")
            summary_deltas.update({
                "baseline_revenue": str(baseline_metrics.total_revenue) if baseline_metrics.total_revenue is not None else "0.00",
                "baseline_transaction_count": baseline_metrics.transaction_count or 0,
                "max_revenue_impact_abs": str(max_rev_impact),
            })
        elif domain_profile.domain_id == "manufacturing":
            summary_deltas.update({
                "baseline_readings": baseline_metrics.total_readings or 0,
                "baseline_units_produced": baseline_metrics.total_units_produced or 0,
                "baseline_defect_count": baseline_metrics.total_defect_count or 0,
                "baseline_energy_kwh": baseline_metrics.total_energy_kwh or 0.0,
                "baseline_avg_temp_c": baseline_metrics.avg_temperature_c or 0.0,
                "baseline_avg_vibration": baseline_metrics.avg_vibration_mm_s or 0.0,
            })

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
                "domain": domain_profile.domain_id,
                "evaluated_rules": rule_config.model_dump(),
                "dataset_row_count": baseline_row_count,
            },
        )
