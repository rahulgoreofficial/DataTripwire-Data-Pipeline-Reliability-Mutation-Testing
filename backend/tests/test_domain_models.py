"""Tests for DataTripwire domain models and enumerations.

Verifies:
1. Domain models accept valid configurations.
2. Domain models reject invalid inputs and invalid boundary conditions.
3. Enumerations enforce permitted values and reject invalid values.
4. EvaluationReport mutation score calculation handles nonzero and zero denominators.
5. Unapplied mutations are never marked as detected.
6. Monetary precision and average order value computations.
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from datatripwire.domain.enums import (
    EvaluationStatus,
    FindingSeverity,
    MutationType,
    RecommendationStatus,
    RuleType,
)
from datatripwire.domain.models import (
    DatasetProfile,
    EvaluationReport,
    MutationEvaluation,
    MutationSpec,
    PipelineMetrics,
    RuleRecommendation,
    ValidationFinding,
)


class TestDomainEnumerations:
    """Verifies enumeration constraints and rejection of unsupported values."""

    def test_mutation_type_supported_values(self):
        valid_types = [
            "duplicate_row",
            "missing_required_value",
            "invalid_quantity",
            "invalid_unit_price",
            "dropped_row",
        ]
        for val in valid_types:
            assert MutationType(val).value == val

    def test_mutation_type_rejects_invalid(self):
        with pytest.raises(ValueError):
            MutationType("unsupported_mutation")

    def test_finding_severity_supported_values(self):
        for val in ["info", "warning", "error", "critical"]:
            assert FindingSeverity(val).value == val

    def test_finding_severity_rejects_invalid(self):
        with pytest.raises(ValueError):
            FindingSeverity("catastrophic")

    def test_rule_type_supported_values(self):
        for val in ["uniqueness", "not_null", "value_range", "data_type", "date_validity"]:
            assert RuleType(val).value == val

    def test_rule_type_rejects_invalid(self):
        with pytest.raises(ValueError):
            RuleType("arbitrary_check")

    def test_recommendation_status_supported_values(self):
        for val in ["suggested", "applied", "dismissed"]:
            assert RecommendationStatus(val).value == val

    def test_evaluation_status_supported_values(self):
        for val in ["detected", "escaped", "inapplicable", "failed"]:
            assert EvaluationStatus(val).value == val


class TestDatasetProfile:
    """Verifies DatasetProfile metadata model contracts and validations."""

    def test_valid_dataset_profile(self):
        profile = DatasetProfile(
            dataset_id="DS-001",
            filename="sales_q1.csv",
            row_count=100,
            column_count=5,
            column_names=["transaction_id", "customer_id", "quantity", "unit_price", "transaction_date"],
            column_types={"quantity": "integer", "unit_price": "float"},
            null_counts={"quantity": 0, "unit_price": 0},
            duplicate_row_count=0,
        )
        assert profile.dataset_id == "DS-001"
        assert profile.row_count == 100
        assert profile.column_count == 5
        assert len(profile.column_names) == 5

    def test_rejects_negative_row_count(self):
        with pytest.raises(ValidationError):
            DatasetProfile(
                dataset_id="DS-001",
                filename="sales.csv",
                row_count=-1,
                column_count=5,
            )

    def test_rejects_blank_dataset_id(self):
        with pytest.raises(ValidationError):
            DatasetProfile(
                dataset_id="   ",
                filename="sales.csv",
                row_count=10,
                column_count=5,
            )

    def test_rejects_negative_null_count(self):
        with pytest.raises(ValidationError):
            DatasetProfile(
                dataset_id="DS-001",
                filename="sales.csv",
                row_count=10,
                column_count=2,
                null_counts={"quantity": -3},
            )


class TestMutationSpec:
    """Verifies MutationSpec model contracts, defaults, and boundary checks."""

    def test_valid_mutation_spec(self):
        spec = MutationSpec(
            mutation_id="MUT-101",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="ORD-102",
            description="Duplicate transaction ORD-102 to test uniqueness enforcement",
        )
        assert spec.mutation_id == "MUT-101"
        assert spec.mutation_type == MutationType.DUPLICATE_ROW
        assert spec.target_record_id == "ORD-102"

    def test_rejects_blank_mutation_id(self):
        with pytest.raises(ValidationError):
            MutationSpec(
                mutation_id="",
                mutation_type=MutationType.INVALID_QUANTITY,
                description="Invalid quantity test",
            )

    def test_rejects_whitespace_target_column(self):
        with pytest.raises(ValidationError):
            MutationSpec(
                mutation_id="MUT-102",
                mutation_type=MutationType.INVALID_QUANTITY,
                target_column="   ",
                description="Invalid quantity test",
            )

    def test_column_mutation_defaults_target_column(self):
        spec = MutationSpec(
            mutation_id="MUT-103",
            mutation_type=MutationType.INVALID_QUANTITY,
            description="Inject non-positive quantity",
        )
        assert spec.target_column == "quantity"


class TestPipelineMetrics:
    """Verifies precision monetary calculations and metric contracts."""

    def test_valid_pipeline_metrics_with_float_input(self):
        metrics = PipelineMetrics(
            total_revenue=2400.0,
            transaction_count=3,
            customer_count=3,
        )
        assert metrics.total_revenue == Decimal("2400.00")
        assert metrics.transaction_count == 3
        # Computed AOV = 2400.00 / 3 = 800.00
        assert metrics.average_order_value == Decimal("800.00")

    def test_revenue_quantized_to_two_decimal_places(self):
        metrics = PipelineMetrics(
            total_revenue="19000.555",
            transaction_count=10,
            customer_count=5,
        )
        # Rounded half up to 19000.56
        assert metrics.total_revenue == Decimal("19000.56")

    def test_rejects_negative_transaction_count(self):
        with pytest.raises(ValidationError):
            PipelineMetrics(
                total_revenue=1000.0,
                transaction_count=-1,
                customer_count=1,
            )

    def test_zero_transactions_handles_aov(self):
        metrics = PipelineMetrics(
            total_revenue=0.0,
            transaction_count=0,
            customer_count=0,
        )
        assert metrics.average_order_value is None


class TestValidationFinding:
    """Verifies validation finding contracts."""

    def test_valid_validation_finding(self):
        finding = ValidationFinding(
            finding_id="FIND-001",
            rule_id="RULE-UNIQUE-TXN",
            rule_type=RuleType.UNIQUENESS,
            severity=FindingSeverity.ERROR,
            affected_column="transaction_id",
            affected_record_ids=["ORD-102"],
            explanation="Duplicate transaction_id 'ORD-102' detected across 2 records",
            detected=True,
        )
        assert finding.finding_id == "FIND-001"
        assert finding.severity == FindingSeverity.ERROR
        assert finding.affected_record_ids == ["ORD-102"]

    def test_rejects_empty_rule_id(self):
        with pytest.raises(ValidationError):
            ValidationFinding(
                finding_id="FIND-001",
                rule_id="",
                rule_type=RuleType.NOT_NULL,
                severity=FindingSeverity.WARNING,
                explanation="Missing value",
            )


class TestMutationEvaluation:
    """Verifies mutation evaluation results and honest detection rules."""

    def test_valid_detected_evaluation(self):
        spec = MutationSpec(
            mutation_id="MUT-01",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="ORD-102",
            description="Duplicate record test",
        )
        evaluation = MutationEvaluation(
            mutation_spec=spec,
            applied=True,
            detected=True,
            metric_deltas={"revenue_delta": "800.00", "count_delta": 1},
        )
        assert evaluation.applied is True
        assert evaluation.detected is True

    def test_unapplied_mutation_cannot_be_marked_detected(self):
        spec = MutationSpec(
            mutation_id="MUT-02",
            mutation_type=MutationType.DROPPED_ROW,
            description="Drop record test",
        )
        with pytest.raises(ValueError, match="Unapplied mutation cannot be marked as detected"):
            MutationEvaluation(
                mutation_spec=spec,
                applied=False,
                detected=True,
                failure_reason="Target record not found",
            )


class TestRuleRecommendation:
    """Verifies rule recommendation data model."""

    def test_valid_rule_recommendation(self):
        rec = RuleRecommendation(
            recommendation_id="REC-001",
            rule_type=RuleType.UNIQUENESS,
            target_column="transaction_id",
            description="Enforce unique transaction_id constraint",
            rationale="Duplicate transaction ORD-102 escaped detection, inflating revenue by ₹800.00",
            suggested_rule_config={"columns": ["transaction_id"], "allow_duplicates": False},
            status=RecommendationStatus.SUGGESTED,
        )
        assert rec.recommendation_id == "REC-001"
        assert rec.rule_type == RuleType.UNIQUENESS
        assert rec.status == RecommendationStatus.SUGGESTED


class TestEvaluationReport:
    """Verifies EvaluationReport aggregation, consistency, and mutation score formulas."""

    def test_mutation_score_with_nonzero_denominator(self):
        report = EvaluationReport(
            report_id="REP-001",
            dataset_id="DS-SALES-01",
            total_attempted=5,
            successfully_applied=4,
            detected_mutations=3,
            surviving_mutations=1,
            failed_evaluations=1,
        )
        # Score = (3 / 4) * 100 = 75.0%
        assert report.mutation_score == 75.0

    def test_mutation_score_with_zero_eligible_mutations(self):
        report = EvaluationReport(
            report_id="REP-002",
            dataset_id="DS-SALES-01",
            total_attempted=3,
            successfully_applied=0,
            detected_mutations=0,
            surviving_mutations=0,
            failed_evaluations=3,
        )
        # Denominator is 0: must return None, NOT raise ZeroDivisionError, NOT return NaN or 0.0
        assert report.mutation_score is None

    def test_failed_mutations_do_not_count_as_detected_or_in_denominator(self):
        # 10 attempted, 8 successfully applied, 2 failed
        # Out of 8 applied: 4 detected, 4 survived
        report = EvaluationReport(
            report_id="REP-003",
            dataset_id="DS-SALES-01",
            total_attempted=10,
            successfully_applied=8,
            detected_mutations=4,
            surviving_mutations=4,
            failed_evaluations=2,
        )
        # Score = 4 / 8 * 100 = 50.0% (not 4 / 10 = 40.0%)
        assert report.mutation_score == 50.0

    def test_rejects_inconsistent_detected_and_surviving_sum(self):
        with pytest.raises(ValueError, match="cannot exceed successfully applied"):
            EvaluationReport(
                report_id="REP-004",
                dataset_id="DS-SALES-01",
                total_attempted=5,
                successfully_applied=3,
                detected_mutations=3,
                surviving_mutations=2,  # 3 + 2 = 5 > 3
                failed_evaluations=0,
            )

    def test_rejects_inconsistent_applied_and_failed_sum(self):
        with pytest.raises(ValueError, match="cannot exceed total attempted"):
            EvaluationReport(
                report_id="REP-005",
                dataset_id="DS-SALES-01",
                total_attempted=4,
                successfully_applied=3,
                detected_mutations=2,
                surviving_mutations=1,
                failed_evaluations=2,  # 3 + 2 = 5 > 4
            )
