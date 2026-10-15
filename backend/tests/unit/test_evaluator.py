"""Unit tests for the core evaluation service.

Implements and verifies all 11 required testing scenarios from Section 20:
- SCENARIO 1: DUPLICATE NOT DETECTED
- SCENARIO 2: DUPLICATE DETECTED
- SCENARIO 3: MISSING VALUE
- SCENARIO 4: INVALID QUANTITY
- SCENARIO 5: INVALID UNIT PRICE
- SCENARIO 6: DROPPED ROW
- SCENARIO 7: EMPTY ELIGIBLE MUTATION SET
- SCENARIO 8: FAILED MUTATION APPLICATION
- SCENARIO 9: PRE-EXISTING FINDINGS
- SCENARIO 10: IMMUTABILITY
- SCENARIO 11: PARTIAL FAILURE
"""

from decimal import Decimal
import pandas as pd
import pytest

from datatripwire.domain.enums import MutationType, RuleType
from datatripwire.schemas import MutationRequestItem, ValidationRuleConfig
from datatripwire.services.evaluator import EvaluationService


@pytest.fixture
def sample_sales_df():
    """Returns a deterministic clean 3-row sales dataset (baseline revenue = ₹2,400.00)."""
    return pd.DataFrame({
        "transaction_id": ["ORD-101", "ORD-102", "ORD-103"],
        "customer_id": ["CUST-1", "CUST-2", "CUST-3"],
        "quantity": [2, 1, 3],
        "unit_price": [500.0, 800.0, 200.0],
        "transaction_date": ["2026-03-01", "2026-03-01", "2026-03-02"],
    })


class TestEvaluationScenarios:
    """Test suite covering Scenarios 1 through 11."""

    def test_scenario_1_duplicate_not_detected(self, sample_sales_df):
        """SCENARIO 1: Duplicate mutation with uniqueness disabled escapes detection.
        
        Calculates revenue from mutated data (+₹800) and produces uniqueness recommendation.
        """
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.DUPLICATE_ROW,
                target_transaction_id="ORD-102",
            )
        ]
        # Baseline rules: uniqueness disabled
        rules = ValidationRuleConfig(check_unique_transaction_id=False)

        report = service.evaluate_dataset(
            df=sample_sales_df,
            dataset_id="DS-SCENARIO-1",
            mutations=mutations,
            rules=rules,
        )

        assert report.total_attempted == 1
        assert report.successfully_applied == 1
        assert report.detected_mutations == 0
        assert report.surviving_mutations == 1
        assert report.failed_evaluations == 0
        assert report.mutation_score == 0.0

        eval_result = report.evaluations[0]
        assert eval_result.applied is True
        assert eval_result.detected is False  # Fault escaped!
        assert eval_result.mutated_metrics.total_revenue == Decimal("3200.00")
        assert eval_result.mutated_metrics.transaction_count == 4
        assert eval_result.metric_deltas["revenue_delta_abs"] == "800.00"

        # Verify uniqueness rule recommendation
        assert len(report.recommendations) == 1
        assert report.recommendations[0].rule_type == RuleType.UNIQUENESS
        assert report.recommendations[0].target_column == "transaction_id"

    def test_scenario_2_duplicate_detected(self, sample_sales_df):
        """SCENARIO 2: Same duplicate mutation with uniqueness enabled is detected."""
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.DUPLICATE_ROW,
                target_transaction_id="ORD-102",
            )
        ]
        # Hardened rules: uniqueness enabled
        rules = ValidationRuleConfig(check_unique_transaction_id=True)

        report = service.evaluate_dataset(
            df=sample_sales_df,
            dataset_id="DS-SCENARIO-2",
            mutations=mutations,
            rules=rules,
        )

        assert report.successfully_applied == 1
        assert report.detected_mutations == 1
        assert report.surviving_mutations == 0
        assert report.mutation_score == 100.0

        eval_result = report.evaluations[0]
        assert eval_result.detected is True

        # Finding must identify the duplicate
        dup_finding = [f for f in eval_result.findings if f.rule_id == "TRANSACTION_ID_DUPLICATE"][0]
        assert "ORD-102" in dup_finding.affected_record_ids

        # Detected fault must NOT generate recommendations as unresolved
        assert len(report.recommendations) == 0

    def test_scenario_3_missing_value(self, sample_sales_df):
        """SCENARIO 3: Missing value injected into valid row is detected; original unchanged."""
        original_copy = sample_sales_df.copy(deep=True)
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.MISSING_REQUIRED_VALUE,
                target_transaction_id="ORD-101",
                target_column="customer_id",
            )
        ]
        rules = ValidationRuleConfig(check_required_values=True)

        report = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-3", mutations, rules)

        assert report.detected_mutations == 1
        assert report.mutation_score == 100.0
        assert report.evaluations[0].detected is True

        # Verify immutability of original input
        pd.testing.assert_frame_equal(sample_sales_df, original_copy)

    def test_scenario_4_invalid_quantity(self, sample_sales_df):
        """SCENARIO 4: Invalid quantity (0) injected and verified detected."""
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.INVALID_QUANTITY,
                target_transaction_id="ORD-103",
                value=0,
            )
        ]
        rules = ValidationRuleConfig(check_quantity_positive=True)

        report = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-4", mutations, rules)

        assert report.detected_mutations == 1
        eval_item = report.evaluations[0]
        assert eval_item.detected is True
        assert any(f.rule_id == "QUANTITY_NOT_POSITIVE" for f in eval_item.findings)

    def test_scenario_5_invalid_unit_price(self, sample_sales_df):
        """SCENARIO 5: Negative unit price injected and verified detected."""
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.INVALID_UNIT_PRICE,
                target_transaction_id="ORD-101",
                value=-250.0,
            )
        ]
        rules = ValidationRuleConfig(check_unit_price_nonnegative=True)

        report = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-5", mutations, rules)

        assert report.detected_mutations == 1
        eval_item = report.evaluations[0]
        assert eval_item.detected is True
        assert any(f.rule_id == "UNIT_PRICE_NEGATIVE" for f in eval_item.findings)

    def test_scenario_6_dropped_row(self, sample_sales_df):
        """SCENARIO 6: Dropped row survives when expected-row-count disabled, detected when enabled."""
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.DROPPED_ROW,
                target_transaction_id="ORD-102",
            )
        ]

        # Part 1: Row count check disabled -> survives
        rules_disabled = ValidationRuleConfig(check_expected_row_count=False)
        rep_disabled = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-6A", mutations, rules_disabled)
        assert rep_disabled.evaluations[0].detected is False
        assert rep_disabled.surviving_mutations == 1

        # Part 2: Row count check enabled with baseline count -> detected
        rules_enabled = ValidationRuleConfig(
            check_expected_row_count=True,
            expected_row_count=len(sample_sales_df),
        )
        rep_enabled = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-6B", mutations, rules_enabled)
        assert rep_enabled.evaluations[0].detected is True
        assert rep_enabled.detected_mutations == 1

    def test_scenario_7_empty_eligible_mutation_set(self, sample_sales_df):
        """SCENARIO 7: When all mutations fail to apply, mutation_score is None (not 0.0 or NaN)."""
        service = EvaluationService()
        # Nonexistent targets cannot be applied
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.DUPLICATE_ROW,
                target_transaction_id="NONEXISTENT-1",
            ),
            MutationRequestItem(
                mutation_type=MutationType.INVALID_QUANTITY,
                target_transaction_id="NONEXISTENT-2",
            ),
        ]

        report = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-7", mutations)
        assert report.total_attempted == 2
        assert report.successfully_applied == 0
        assert report.failed_evaluations == 2
        # Score must be None when denominator is 0
        assert report.mutation_score is None

    def test_scenario_8_failed_mutation_application(self, sample_sales_df):
        """SCENARIO 8: Failed mutation does not count as detected or in score denominator."""
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.INVALID_QUANTITY,
                target_transaction_id="ORD-101",
                value=0,
            ),
            MutationRequestItem(
                mutation_type=MutationType.DUPLICATE_ROW,
                target_transaction_id="NONEXISTENT-ID",
            ),
        ]
        rules = ValidationRuleConfig(check_quantity_positive=True)

        report = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-8", mutations, rules)
        assert report.total_attempted == 2
        assert report.successfully_applied == 1
        assert report.failed_evaluations == 1
        assert report.detected_mutations == 1
        # Score = 1 detected / 1 eligible applied * 100 = 100.0% (NOT 1 / 2 = 50%)
        assert report.mutation_score == 100.0

    def test_scenario_9_pre_existing_findings(self):
        """SCENARIO 9: Pre-existing baseline flaw is not falsely reported as detection of a new fault."""
        # Dataset starts with pre-existing invalid quantity on ORD-101
        dirty_df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-102"],
            "customer_id": ["C1", "C2"],
            "quantity": [-10, 5],  # ORD-101 is already invalid!
            "unit_price": [100.0, 200.0],
            "transaction_date": ["2026-03-01", "2026-03-02"],
        })

        service = EvaluationService()
        # Injected fault is a duplicate on ORD-102 with uniqueness disabled
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.DUPLICATE_ROW,
                target_transaction_id="ORD-102",
            )
        ]
        # Active rules check quantity (which will trigger for ORD-101), but uniqueness is disabled
        rules = ValidationRuleConfig(
            check_quantity_positive=True,
            check_unique_transaction_id=False,
        )

        report = service.evaluate_dataset(dirty_df, "DS-SCENARIO-9", mutations, rules)
        eval_item = report.evaluations[0]

        # The duplicate fault escaped! Pre-existing quantity finding must NOT count as detection
        assert eval_item.detected is False
        assert report.surviving_mutations == 1
        assert report.detected_mutations == 0

    def test_scenario_10_immutability(self, sample_sales_df):
        """SCENARIO 10: Running multiple back-to-back evaluations leaves original DataFrame pristine."""
        original_data = sample_sales_df.to_dict()
        service = EvaluationService()

        for _ in range(3):
            mutations = [
                MutationRequestItem(mutation_type=MutationType.DROPPED_ROW, target_transaction_id="ORD-101"),
                MutationRequestItem(mutation_type=MutationType.DUPLICATE_ROW, target_transaction_id="ORD-102"),
            ]
            service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-10", mutations)

        assert sample_sales_df.to_dict() == original_data

    def test_scenario_11_partial_failure(self, sample_sales_df):
        """SCENARIO 11: Batch with 1 valid and 1 invalid mutation handles both cleanly."""
        service = EvaluationService()
        mutations = [
            MutationRequestItem(
                mutation_type=MutationType.INVALID_QUANTITY,
                target_transaction_id="ORD-101",
                value=-1,
            ),
            MutationRequestItem(
                mutation_type=MutationType.DUPLICATE_ROW,
                target_transaction_id="DOES-NOT-EXIST",
            ),
        ]
        rules = ValidationRuleConfig(check_quantity_positive=True)

        report = service.evaluate_dataset(sample_sales_df, "DS-SCENARIO-11", mutations, rules)
        assert report.total_attempted == 2
        assert report.successfully_applied == 1
        assert report.failed_evaluations == 1
        assert report.detected_mutations == 1
        assert report.mutation_score == 100.0

        # Detailed item checks
        assert report.evaluations[0].applied is True
        assert report.evaluations[0].detected is True
        assert report.evaluations[1].applied is False
        assert report.evaluations[1].failure_reason is not None
