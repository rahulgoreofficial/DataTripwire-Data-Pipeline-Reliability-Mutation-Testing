"""Unit tests for the Manufacturing / Industrial IoT domain.

Verifies schema recognition, validation rules, mutation operators, metrics,
recommendations, and dataset immutability for industrial telemetry datasets.
"""

import numpy as np
import pandas as pd
import pytest

from datatripwire.config import SAMPLE_MANUFACTURING_CSV
from datatripwire.domain.enums import MutationType, RuleType
from datatripwire.domain.models import MutationEvaluation, MutationSpec
from datatripwire.domains.manufacturing import (
    ManufacturingDomainProfile,
    RULE_CODE_MFG_EXPECTED_RECORD_COUNT_MISMATCH,
    RULE_CODE_MFG_INVALID_TIMESTAMP,
    RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE,
    RULE_CODE_MFG_MEASUREMENT_NEGATIVE,
    RULE_CODE_MFG_PRODUCTION_INCONSISTENCY,
    RULE_CODE_MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS,
    RULE_CODE_MFG_READING_ID_DUPLICATE,
    RULE_CODE_MFG_REQUIRED_COLUMN_MISSING,
    RULE_CODE_MFG_REQUIRED_VALUE_MISSING,
    RULE_CODE_MFG_SENSOR_NUMERIC_INVALID,
    RULE_CODE_MFG_TEMPERATURE_OUT_OF_BOUNDS,
)
from datatripwire.domains.registry import get_domain_registry
from datatripwire.schemas import ValidationRuleConfig
from datatripwire.services.profiler import profile_dataframe


@pytest.fixture
def mfg_profile() -> ManufacturingDomainProfile:
    return ManufacturingDomainProfile()


@pytest.fixture
def sample_mfg_df() -> pd.DataFrame:
    """Deterministic 20-row manufacturing test fixture."""
    return pd.read_csv(SAMPLE_MANUFACTURING_CSV)


class TestManufacturingSchemaRecognition:
    """Verifies recognition and compatibility checking for manufacturing datasets."""

    def test_manufacturing_schema_recognized(self, sample_mfg_df):
        registry = get_domain_registry()
        detected = registry.detect_domain(sample_mfg_df)
        assert detected.domain_id == "manufacturing"

    def test_manufacturing_compatibility_flags(self, sample_mfg_df):
        profile = profile_dataframe(sample_mfg_df, dataset_id="ds-test-mfg", filename="test_mfg.csv")
        assert profile.is_manufacturing_compatible is True
        assert profile.is_sales_compatible is False
        assert profile.detected_domain == "manufacturing"
        assert profile.row_count == 20
        assert profile.column_count == 18

    def test_missing_required_column_fails_compatibility(self, sample_mfg_df, mfg_profile):
        corrupted = sample_mfg_df.drop(columns=["temperature_c"])
        compat, missing = mfg_profile.is_compatible(corrupted)
        assert compat is False
        assert "temperature_c" in missing


class TestManufacturingValidationRules:
    """Verifies each manufacturing validation safeguard."""

    def test_missing_sensor_value_detected(self, sample_mfg_df, mfg_profile):
        df_mut = sample_mfg_df.copy()
        df_mut.at[2, "temperature_c"] = np.nan

        config = ValidationRuleConfig(check_required_values=True)
        findings = mfg_profile.validate(df_mut, config=config)

        missing_findings = [f for f in findings if f.rule_id == RULE_CODE_MFG_REQUIRED_VALUE_MISSING]
        assert len(missing_findings) == 1
        assert missing_findings[0].affected_column == "temperature_c"
        assert "RDG-03-0001" in missing_findings[0].affected_record_ids

    def test_duplicate_reading_id_detected_when_enabled(self, sample_mfg_df, mfg_profile):
        df_mut = pd.concat([sample_mfg_df, sample_mfg_df.iloc[[0]]], ignore_index=True)

        # Baseline: uniqueness check is False
        baseline_findings = mfg_profile.validate(df_mut, config=ValidationRuleConfig(check_reading_id_unique=False))
        assert not any(f.rule_id == RULE_CODE_MFG_READING_ID_DUPLICATE for f in baseline_findings)

        # Hardened: uniqueness check is True
        hardened_findings = mfg_profile.validate(df_mut, config=ValidationRuleConfig(check_reading_id_unique=True))
        dup_findings = [f for f in hardened_findings if f.rule_id == RULE_CODE_MFG_READING_ID_DUPLICATE]
        assert len(dup_findings) == 1
        assert "RDG-01-0001" in dup_findings[0].affected_record_ids

    def test_duplicate_machine_and_timestamp_detected_when_enabled(self, sample_mfg_df, mfg_profile):
        df_mut = pd.concat([sample_mfg_df, sample_mfg_df.iloc[[1]]], ignore_index=True)

        # Baseline: check_machine_timestamp_unique is False
        baseline_findings = mfg_profile.validate(df_mut, config=ValidationRuleConfig(check_machine_timestamp_unique=False))
        assert not any(f.rule_id == RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE for f in baseline_findings)

        # Hardened: check_machine_timestamp_unique is True
        hardened_findings = mfg_profile.validate(df_mut, config=ValidationRuleConfig(check_machine_timestamp_unique=True))
        dup_findings = [f for f in hardened_findings if f.rule_id == RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE]
        assert len(dup_findings) == 1
        assert "RDG-02-0001" in dup_findings[0].affected_record_ids

    def test_same_timestamp_across_different_machines_is_valid(self, sample_mfg_df, mfg_profile):
        # Rows 0, 1, 2 have the same timestamp 2026-10-08T00:00:00, but different machine_ids (MCH-CNC-01, 02, 03)
        # This must NOT be flagged as duplicate!
        config = ValidationRuleConfig(check_machine_timestamp_unique=True)
        findings = mfg_profile.validate(sample_mfg_df, config=config)
        assert not any(f.rule_id == RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE for f in findings)

    def test_negative_vibration_or_pressure_detected(self, sample_mfg_df, mfg_profile):
        df_mut = sample_mfg_df.copy()
        df_mut.at[3, "vibration_mm_s"] = -0.5
        df_mut.at[4, "pressure_bar"] = -2.1

        config = ValidationRuleConfig(check_non_negative_measurements=True)
        findings = mfg_profile.validate(df_mut, config=config)

        neg_findings = [f for f in findings if f.rule_id == RULE_CODE_MFG_MEASUREMENT_NEGATIVE]
        assert len(neg_findings) == 2
        neg_cols = {f.affected_column for f in neg_findings}
        assert "vibration_mm_s" in neg_cols
        assert "pressure_bar" in neg_cols

    def test_invalid_quality_percentage_detected(self, sample_mfg_df, mfg_profile):
        df_mut = sample_mfg_df.copy()
        df_mut.at[0, "quality_pass_rate_pct"] = 105.0

        config = ValidationRuleConfig(check_quality_pass_rate_bounds=True)
        findings = mfg_profile.validate(df_mut, config=config)

        qual_findings = [f for f in findings if f.rule_id == RULE_CODE_MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS]
        assert len(qual_findings) == 1

    def test_production_inconsistency_detected(self, sample_mfg_df, mfg_profile):
        df_mut = sample_mfg_df.copy()
        # Row 1 has units_produced=8, defect_count=0 -> set defect_count to 20
        df_mut.at[1, "defect_count"] = 20

        config = ValidationRuleConfig(check_production_consistency=True)
        findings = mfg_profile.validate(df_mut, config=config)

        prod_findings = [f for f in findings if f.rule_id == RULE_CODE_MFG_PRODUCTION_INCONSISTENCY]
        assert len(prod_findings) == 1
        assert "RDG-02-0001" in prod_findings[0].affected_record_ids

    def test_temperature_out_of_bounds_detected(self, sample_mfg_df, mfg_profile):
        df_mut = sample_mfg_df.copy()
        df_mut.at[5, "temperature_c"] = 120.5  # Exceeds max 95.0

        config = ValidationRuleConfig(check_temperature_bounds=True, temperature_max_c=95.0)
        findings = mfg_profile.validate(df_mut, config=config)

        temp_findings = [f for f in findings if f.rule_id == RULE_CODE_MFG_TEMPERATURE_OUT_OF_BOUNDS]
        assert len(temp_findings) == 1
        assert "RDG-06-0001" in temp_findings[0].affected_record_ids

    def test_expected_record_count_reconciliation(self, sample_mfg_df, mfg_profile):
        df_dropped = sample_mfg_df.iloc[:-1].copy()  # 19 rows instead of 20

        config = ValidationRuleConfig(check_expected_record_count=True, expected_record_count=20)
        findings = mfg_profile.validate(df_dropped, config=config, reference_row_count=20)

        row_findings = [f for f in findings if f.rule_id == RULE_CODE_MFG_EXPECTED_RECORD_COUNT_MISMATCH]
        assert len(row_findings) == 1


class TestManufacturingMutations:
    """Verifies manufacturing synthetic fault injection and immutability."""

    def test_duplicate_sensor_reading_mutation(self, sample_mfg_df, mfg_profile):
        spec = MutationSpec(
            mutation_id="MUT-MFG-01",
            mutation_type=MutationType.DUPLICATE_SENSOR_READING,
            target_record_id="RDG-02-0001",
            description="Duplicate sensor reading RDG-02-0001",
        )
        mutated_df, meta = mfg_profile.apply_mutation(sample_mfg_df, spec)
        assert meta["applied"] is True
        assert len(mutated_df) == len(sample_mfg_df) + 1
        assert len(sample_mfg_df) == 20  # Original is untouched!
        assert meta["expected_rule_code"] == RULE_CODE_MFG_READING_ID_DUPLICATE

    def test_missing_sensor_value_mutation(self, sample_mfg_df, mfg_profile):
        spec = MutationSpec(
            mutation_id="MUT-MFG-02",
            mutation_type=MutationType.MISSING_SENSOR_VALUE,
            target_record_id="RDG-01-0001",
            target_column="temperature_c",
            description="Nullify temperature_c on RDG-01-0001",
        )
        mutated_df, meta = mfg_profile.apply_mutation(sample_mfg_df, spec)
        assert meta["applied"] is True
        assert pd.isna(mutated_df.at[0, "temperature_c"])
        assert pd.notna(sample_mfg_df.at[0, "temperature_c"])  # Original preserved

    def test_invalid_sensor_value_mutation(self, sample_mfg_df, mfg_profile):
        spec = MutationSpec(
            mutation_id="MUT-MFG-03",
            mutation_type=MutationType.INVALID_SENSOR_VALUE,
            target_record_id="RDG-02-0001",
            target_column="vibration_mm_s",
            params={"value": -1.5},
            description="Inject negative vibration into RDG-02-0001",
        )
        mutated_df, meta = mfg_profile.apply_mutation(sample_mfg_df, spec)
        assert meta["applied"] is True
        assert mutated_df.at[1, "vibration_mm_s"] == -1.5
        assert sample_mfg_df.at[1, "vibration_mm_s"] > 0

    def test_dropped_sensor_reading_mutation(self, sample_mfg_df, mfg_profile):
        spec = MutationSpec(
            mutation_id="MUT-MFG-04",
            mutation_type=MutationType.DROPPED_SENSOR_READING,
            target_record_id="RDG-05-0001",
            description="Drop sensor reading RDG-05-0001",
        )
        mutated_df, meta = mfg_profile.apply_mutation(sample_mfg_df, spec)
        assert meta["applied"] is True
        assert len(mutated_df) == 19
        assert len(sample_mfg_df) == 20

    def test_invalid_production_value_mutation(self, sample_mfg_df, mfg_profile):
        spec = MutationSpec(
            mutation_id="MUT-MFG-05",
            mutation_type=MutationType.INVALID_PRODUCTION_VALUE,
            target_record_id="RDG-03-0001",
            target_column="defect_count",
            params={"value": 85},
            description="Set defect_count to 85 exceeding units_produced",
        )
        mutated_df, meta = mfg_profile.apply_mutation(sample_mfg_df, spec)
        assert meta["applied"] is True
        assert mutated_df.at[2, "defect_count"] == 85


class TestManufacturingMetrics:
    """Verifies operational telemetry calculations and metric deltas."""

    def test_baseline_metrics_calculation(self, sample_mfg_df, mfg_profile):
        metrics = mfg_profile.calculate_metrics(sample_mfg_df)
        assert metrics.domain == "manufacturing"
        assert metrics.total_readings == 20
        assert metrics.unique_machines == 9
        assert metrics.unique_facilities == 2
        assert metrics.total_units_produced > 0
        assert metrics.total_defect_count == 1
        assert metrics.avg_temperature_c > 0.0
        assert metrics.max_temperature_c >= metrics.avg_temperature_c
        assert metrics.avg_vibration_mm_s > 0.0

    def test_metric_deltas_on_duplicate_mutation(self, sample_mfg_df, mfg_profile):
        baseline = mfg_profile.calculate_metrics(sample_mfg_df)
        # Add duplicate row 1 (units_produced=8, energy=2.83)
        dup_df = pd.concat([sample_mfg_df, sample_mfg_df.iloc[[1]]], ignore_index=True)
        mutated = mfg_profile.calculate_metrics(dup_df)

        deltas = mfg_profile.calculate_metric_deltas(baseline, mutated)
        assert deltas["readings_delta"] == 1
        assert deltas["units_produced_delta"] == 8
        assert deltas["energy_kwh_delta"] == 2.83


class TestManufacturingRecommendations:
    """Verifies rule recommendation generation when manufacturing mutations escape."""

    def test_uniqueness_recommendation_for_surviving_duplicate(self, mfg_profile):
        spec = MutationSpec(
            mutation_id="MUT-001",
            mutation_type=MutationType.DUPLICATE_SENSOR_READING,
            target_record_id="RDG-01-0001",
            description="Duplicate sensor reading",
        )
        eval_item = MutationEvaluation(
            mutation_spec=spec,
            applied=True,
            detected=False,  # Escaped!
            findings=[],
        )
        recs = mfg_profile.generate_recommendations([eval_item])
        assert len(recs) == 1
        assert recs[0].rule_type == RuleType.UNIQUENESS
        assert "check_machine_timestamp_unique" in recs[0].suggested_rule_config
        assert recs[0].suggested_rule_config["check_machine_timestamp_unique"] is True
