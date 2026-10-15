"""Deterministic rule recommendation engine for DataTripwire.

Generates targeted, explainable data-quality rule recommendations when
injected mutations escape existing validation safeguards.
"""

from typing import List, Set
from datatripwire.domain.enums import MutationType, RecommendationStatus, RuleType
from datatripwire.domain.models import MutationEvaluation, RuleRecommendation


def generate_recommendations_for_surviving_mutations(
    surviving_evaluations: List[MutationEvaluation],
) -> List[RuleRecommendation]:
    """Generate deterministic validation rule recommendations for surviving mutations.
    
    Args:
        surviving_evaluations: Evaluations where the fault escaped (detected == False).
        
    Returns:
        List of distinct, actionable RuleRecommendation instances.
    """
    recommendations: List[RuleRecommendation] = []
    seen_rule_targets: Set[str] = set()
    rec_counter = 1

    for eval_item in surviving_evaluations:
        if eval_item.detected is not False or not eval_item.applied:
            # Only recommend rules for mutations that successfully applied and genuinely escaped
            continue

        spec = eval_item.mutation_spec
        mtype = spec.mutation_type
        target_col = spec.target_column

        # Deduplication key based on rule type and target column
        dedup_key = f"{mtype.value}::{target_col}"
        if dedup_key in seen_rule_targets:
            continue
        seen_rule_targets.add(dedup_key)

        rec_id = f"REC-{rec_counter:03d}"
        rec_counter += 1

        if mtype == MutationType.DUPLICATE_ROW:
            recommendations.append(
                RuleRecommendation(
                    recommendation_id=rec_id,
                    rule_type=RuleType.UNIQUENESS,
                    target_column="transaction_id",
                    description="Enforce unique constraint on primary key column 'transaction_id'",
                    rationale=(
                        f"Mutation '{spec.mutation_id}' duplicated a transaction without being caught, "
                        "silently inflating revenue and transaction counts. Enabling uniqueness verification "
                        "on 'transaction_id' prevents duplicate ingestion."
                    ),
                    suggested_rule_config={"check_unique_transaction_id": True},
                    code_snippet="df['transaction_id'].duplicated().any() == False",
                    status=RecommendationStatus.SUGGESTED,
                )
            )

        elif mtype == MutationType.MISSING_REQUIRED_VALUE:
            col_name = target_col or "quantity"
            recommendations.append(
                RuleRecommendation(
                    recommendation_id=rec_id,
                    rule_type=RuleType.NOT_NULL,
                    target_column=col_name,
                    description=f"Enforce NOT NULL constraint on required column '{col_name}'",
                    rationale=(
                        f"Mutation '{spec.mutation_id}' injected missing values into '{col_name}' without being caught. "
                        "Missing values in mandatory columns cause corrupted calculations and incomplete reports."
                    ),
                    suggested_rule_config={"check_required_values": True},
                    code_snippet=f"df['{col_name}'].isna().any() == False",
                    status=RecommendationStatus.SUGGESTED,
                )
            )

        elif mtype == MutationType.INVALID_QUANTITY:
            recommendations.append(
                RuleRecommendation(
                    recommendation_id=rec_id,
                    rule_type=RuleType.VALUE_RANGE,
                    target_column="quantity",
                    description="Enforce positive quantity rule (quantity > 0)",
                    rationale=(
                        f"Mutation '{spec.mutation_id}' injected a non-positive quantity that escaped detection. "
                        "Quantities must be strictly greater than zero to maintain accurate sales metrics."
                    ),
                    suggested_rule_config={"check_quantity_positive": True},
                    code_snippet="(df['quantity'] > 0).all()",
                    status=RecommendationStatus.SUGGESTED,
                )
            )

        elif mtype == MutationType.INVALID_UNIT_PRICE:
            recommendations.append(
                RuleRecommendation(
                    recommendation_id=rec_id,
                    rule_type=RuleType.VALUE_RANGE,
                    target_column="unit_price",
                    description="Enforce non-negative unit price rule (unit_price >= 0.00)",
                    rationale=(
                        f"Mutation '{spec.mutation_id}' injected a negative unit price that escaped detection. "
                        "Unit prices must be non-negative to prevent erroneous revenue deductions."
                    ),
                    suggested_rule_config={"check_unit_price_nonnegative": True},
                    code_snippet="(df['unit_price'] >= 0.00).all()",
                    status=RecommendationStatus.SUGGESTED,
                )
            )

        elif mtype == MutationType.DROPPED_ROW:
            recommendations.append(
                RuleRecommendation(
                    recommendation_id=rec_id,
                    rule_type=RuleType.VALUE_RANGE,
                    target_column=None,
                    description="Enforce expected row count reconciliation against control total",
                    rationale=(
                        f"Mutation '{spec.mutation_id}' dropped a transaction row without triggering any validation. "
                        "Reconciling row counts against an upstream control record prevents silent record loss."
                    ),
                    suggested_rule_config={"check_expected_row_count": True},
                    code_snippet="len(df) == expected_row_count",
                    status=RecommendationStatus.SUGGESTED,
                )
            )

    return recommendations
