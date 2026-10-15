"""Unit tests for the rule recommendation engine.

Verifies:
1. Surviving mutations produce targeted, explainable recommendations.
2. Detected mutations do not produce recommendations.
3. Recommendations are deduplicated within a single evaluation run.
4. Generated recommendations contain structured configurations without executing arbitrary code.
"""

from datatripwire.domain.enums import MutationType, RecommendationStatus, RuleType
from datatripwire.domain.models import MutationEvaluation, MutationSpec
from datatripwire.services.recommendations import generate_recommendations_for_surviving_mutations


class TestRecommendations:
    """Test suite for generate_recommendations_for_surviving_mutations."""

    def test_surviving_duplicate_produces_uniqueness_recommendation(self):
        spec = MutationSpec(
            mutation_id="MUT-01",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="ORD-102",
            description="Duplicate transaction test",
        )
        eval_item = MutationEvaluation(
            mutation_spec=spec,
            applied=True,
            detected=False,  # Escaped!
        )
        recs = generate_recommendations_for_surviving_mutations([eval_item])

        assert len(recs) == 1
        assert recs[0].rule_type == RuleType.UNIQUENESS
        assert recs[0].target_column == "transaction_id"
        assert recs[0].suggested_rule_config == {"check_unique_transaction_id": True}
        assert recs[0].status == RecommendationStatus.SUGGESTED
        assert "duplicate" in recs[0].rationale.lower()

    def test_detected_mutation_produces_no_recommendations(self):
        spec = MutationSpec(
            mutation_id="MUT-02",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="ORD-102",
            description="Duplicate test",
        )
        eval_item = MutationEvaluation(
            mutation_spec=spec,
            applied=True,
            detected=True,  # Caught!
        )
        recs = generate_recommendations_for_surviving_mutations([eval_item])
        assert len(recs) == 0

    def test_unapplied_mutation_produces_no_recommendations(self):
        spec = MutationSpec(
            mutation_id="MUT-03",
            mutation_type=MutationType.DROPPED_ROW,
            description="Drop row test",
        )
        eval_item = MutationEvaluation(
            mutation_spec=spec,
            applied=False,
            detected=None,
        )
        recs = generate_recommendations_for_surviving_mutations([eval_item])
        assert len(recs) == 0

    def test_deduplicates_recommendations_for_same_fault_type(self):
        spec1 = MutationSpec(
            mutation_id="MUT-04A",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="ORD-101",
            description="Duplicate 101",
        )
        spec2 = MutationSpec(
            mutation_id="MUT-04B",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="ORD-102",
            description="Duplicate 102",
        )
        eval1 = MutationEvaluation(mutation_spec=spec1, applied=True, detected=False)
        eval2 = MutationEvaluation(mutation_spec=spec2, applied=True, detected=False)

        recs = generate_recommendations_for_surviving_mutations([eval1, eval2])
        # Two surviving duplicates should result in exactly one uniqueness recommendation
        assert len(recs) == 1
        assert recs[0].rule_type == RuleType.UNIQUENESS
