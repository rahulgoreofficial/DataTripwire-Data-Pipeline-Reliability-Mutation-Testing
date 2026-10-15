"""Manufacturing and Industrial IoT Domain Profile for DataTripwire.

Encapsulates schema requirements, validation safeguards, synthetic mutation operators,
operational telemetry metrics, and rule recommendations for industrial manufacturing datasets.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from datatripwire.config import (
    MANUFACTURING_PRIMARY_KEY,
    MANUFACTURING_REQUIRED_COLUMNS,
    MANUFACTURING_SCHEMA_COLUMNS,
)
from datatripwire.domain.enums import (
    FindingSeverity,
    MutationType,
    RecommendationStatus,
    RuleType,
)
from datatripwire.domain.models import (
    MutationEvaluation,
    MutationSpec,
    PipelineMetrics,
    RuleRecommendation,
    ValidationFinding,
)
from datatripwire.domains.base import BaseDomainProfile
from datatripwire.schemas import ValidationRuleConfig


# Stable machine-readable rule codes for manufacturing
RULE_CODE_MFG_REQUIRED_COLUMN_MISSING = "MFG_REQUIRED_COLUMN_MISSING"
RULE_CODE_MFG_REQUIRED_VALUE_MISSING = "MFG_REQUIRED_VALUE_MISSING"
RULE_CODE_MFG_READING_ID_DUPLICATE = "MFG_READING_ID_DUPLICATE"
RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE = "MFG_MACHINE_TIMESTAMP_DUPLICATE"
RULE_CODE_MFG_INVALID_TIMESTAMP = "MFG_INVALID_TIMESTAMP"
RULE_CODE_MFG_SENSOR_NUMERIC_INVALID = "MFG_SENSOR_NUMERIC_INVALID"
RULE_CODE_MFG_MEASUREMENT_NEGATIVE = "MFG_MEASUREMENT_NEGATIVE"
RULE_CODE_MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS = "MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS"
RULE_CODE_MFG_PRODUCTION_INCONSISTENCY = "MFG_PRODUCTION_INCONSISTENCY"
RULE_CODE_MFG_TEMPERATURE_OUT_OF_BOUNDS = "MFG_TEMPERATURE_OUT_OF_BOUNDS"
RULE_CODE_MFG_EXPECTED_RECORD_COUNT_MISMATCH = "MFG_EXPECTED_RECORD_COUNT_MISMATCH"

# Numeric columns expected to be non-negative in industrial telemetry
NON_NEGATIVE_SENSOR_COLUMNS = [
    "pressure_bar",
    "vibration_mm_s",
    "motor_current_a",
    "power_kw",
    "energy_kwh_20min",
    "units_produced",
    "defect_count",
]


def _resolve_mfg_target_index(
    df: pd.DataFrame,
    target_record_id: Optional[str] = None,
    row_index: Optional[int] = None,
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """Resolve target reading ID or integer row index in a manufacturing DataFrame."""
    if len(df) == 0:
        return None, None, "Dataset is empty; no target sensor reading can be selected"

    if target_record_id is not None:
        clean_id = target_record_id.strip()
        id_col = "reading_id" if "reading_id" in df.columns else df.columns[0]
        matching = df[df[id_col].astype(str).str.strip() == clean_id]
        if len(matching) == 0:
            return None, None, f"Target sensor reading with identifier '{clean_id}' was not found"
        int_idx = df.index.get_loc(matching.index[0])
        return int_idx, clean_id, None

    if row_index is not None:
        if row_index < 0 or row_index >= len(df):
            return None, None, f"Row index {row_index} is out of bounds (0 to {len(df) - 1})"
        rec_id = str(df.iloc[row_index].get("reading_id", f"row_{row_index}"))
        return row_index, rec_id, None

    # Default to the first available record
    rec_id = str(df.iloc[0].get("reading_id", "row_0"))
    return 0, rec_id, None


class ManufacturingDomainProfile(BaseDomainProfile):
    """Adapter for industrial equipment telemetry and manufacturing data pipelines."""

    @property
    def domain_id(self) -> str:
        return "manufacturing"

    @property
    def name(self) -> str:
        return "Manufacturing / Industrial IoT"

    @property
    def description(self) -> str:
        return "Industrial telemetry and production monitoring tracking machines, sensor signals, power, and defects."

    @property
    def primary_key_column(self) -> Optional[str]:
        return MANUFACTURING_PRIMARY_KEY

    @property
    def required_columns(self) -> List[str]:
        return list(MANUFACTURING_REQUIRED_COLUMNS)

    @property
    def schema_columns(self) -> List[str]:
        return list(MANUFACTURING_SCHEMA_COLUMNS)

    @property
    def supported_mutation_types(self) -> List[MutationType]:
        return [
            MutationType.DUPLICATE_SENSOR_READING,
            MutationType.MISSING_SENSOR_VALUE,
            MutationType.INVALID_SENSOR_VALUE,
            MutationType.DROPPED_SENSOR_READING,
            MutationType.INVALID_PRODUCTION_VALUE,
            # Backwards-compatible aliases
            MutationType.DUPLICATE_ROW,
            MutationType.DROPPED_ROW,
        ]

    def is_compatible(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        missing = [c for c in self.required_columns if c not in df.columns]
        return len(missing) == 0, missing

    def validate(
        self,
        df: pd.DataFrame,
        config: Optional[ValidationRuleConfig] = None,
        reference_row_count: Optional[int] = None,
    ) -> List[ValidationFinding]:
        """Execute manufacturing data-quality checks on a dataset DataFrame."""
        rule_config = config or ValidationRuleConfig()
        findings: List[ValidationFinding] = []
        finding_idx = 1

        def get_record_id(row_idx: int) -> str:
            if "reading_id" in df.columns:
                val = df.at[row_idx, "reading_id"]
                if pd.notna(val) and str(val).strip():
                    return str(val).strip()
            return f"row_{row_idx}"

        # 1. Essential columns check
        if rule_config.check_required_columns:
            missing_cols = [c for c in self.required_columns if c not in df.columns]
            for col in missing_cols:
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-COL-{finding_idx}",
                        rule_id=RULE_CODE_MFG_REQUIRED_COLUMN_MISSING,
                        rule_type=RuleType.DATA_TYPE,
                        severity=FindingSeverity.CRITICAL,
                        affected_column=col,
                        affected_record_ids=[],
                        explanation=f"Required manufacturing telemetry column '{col}' is missing from the dataset.",
                        detected=True,
                    )
                )
                finding_idx += 1

        # 2. Required values not missing check
        if rule_config.check_required_values:
            cols_to_check = [c for c in self.required_columns if c in df.columns]
            for col in cols_to_check:
                null_mask = df[col].isna()
                if null_mask.any():
                    violating_indices = df.index[null_mask].tolist()
                    violating_ids = [get_record_id(idx) for idx in violating_indices]
                    findings.append(
                        ValidationFinding(
                            finding_id=f"FIND-MFG-VAL-{finding_idx}",
                            rule_id=RULE_CODE_MFG_REQUIRED_VALUE_MISSING,
                            rule_type=RuleType.NOT_NULL,
                            severity=FindingSeverity.ERROR,
                            affected_column=col,
                            affected_record_ids=violating_ids,
                            explanation=f"Mandatory telemetry column '{col}' contains missing (null/NaN) values in {len(violating_ids)} record(s).",
                            detected=True,
                        )
                    )
                    finding_idx += 1

        # 3. Reading ID uniqueness check (CONFIGURABLE - False in baseline)
        if rule_config.check_reading_id_unique and "reading_id" in df.columns:
            non_null_ids = df["reading_id"].dropna().astype(str).str.strip()
            duplicate_mask = non_null_ids.duplicated(keep=False)
            if duplicate_mask.any():
                dup_ids = sorted(list(set(non_null_ids[duplicate_mask].tolist())))
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-RDG-{finding_idx}",
                        rule_id=RULE_CODE_MFG_READING_ID_DUPLICATE,
                        rule_type=RuleType.UNIQUENESS,
                        severity=FindingSeverity.CRITICAL,
                        affected_column="reading_id",
                        affected_record_ids=dup_ids,
                        explanation=f"Duplicate reading_id detected for {len(dup_ids)} identifier(s): {dup_ids[:5]}",
                        detected=True,
                    )
                )
                finding_idx += 1

        # 4. Machine and timestamp composite uniqueness check (CONFIGURABLE - False in baseline)
        if rule_config.check_machine_timestamp_unique and "machine_id" in df.columns and "timestamp" in df.columns:
            subset_cols = ["machine_id", "timestamp"]
            dup_mask = df.duplicated(subset=subset_cols, keep=False)
            if dup_mask.any():
                violating_indices = df.index[dup_mask].tolist()
                violating_ids = [get_record_id(idx) for idx in violating_indices]
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-MCHTS-{finding_idx}",
                        rule_id=RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE,
                        rule_type=RuleType.UNIQUENESS,
                        severity=FindingSeverity.CRITICAL,
                        affected_column="machine_id",
                        affected_record_ids=violating_ids,
                        explanation=(
                            f"Duplicate telemetry records detected for identical (machine_id, timestamp) "
                            f"combinations across {len(violating_ids)} reading(s)."
                        ),
                        detected=True,
                    )
                )
                finding_idx += 1

        # 5. Timestamp validity check
        if rule_config.check_timestamp_validity and "timestamp" in df.columns:
            violating_ids: List[str] = []
            for idx, val in df["timestamp"].items():
                if pd.isna(val):
                    continue
                val_str = str(val).strip()
                try:
                    # Parse standard ISO formats
                    pd.to_datetime(val_str)
                except Exception:
                    violating_ids.append(get_record_id(idx))

            if violating_ids:
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-TS-{finding_idx}",
                        rule_id=RULE_CODE_MFG_INVALID_TIMESTAMP,
                        rule_type=RuleType.DATE_VALIDITY,
                        severity=FindingSeverity.ERROR,
                        affected_column="timestamp",
                        affected_record_ids=violating_ids,
                        explanation=f"Invalid date/time format in 'timestamp' column for {len(violating_ids)} record(s).",
                        detected=True,
                    )
                )
                finding_idx += 1

        # 6. Sensor numeric validity check
        if rule_config.check_sensor_numeric:
            numeric_cols = [
                c for c in [
                    "temperature_c", "pressure_bar", "vibration_mm_s",
                    "motor_current_a", "power_kw", "energy_kwh_20min",
                    "units_produced", "defect_count", "quality_pass_rate_pct"
                ] if c in df.columns
            ]
            for col in numeric_cols:
                violating_ids = []
                for idx, val in df[col].items():
                    if pd.isna(val):
                        continue
                    try:
                        num = float(val)
                        if not np.isfinite(num):
                            violating_ids.append(get_record_id(idx))
                    except (ValueError, TypeError):
                        violating_ids.append(get_record_id(idx))

                if violating_ids:
                    findings.append(
                        ValidationFinding(
                            finding_id=f"FIND-MFG-NUM-{finding_idx}",
                            rule_id=RULE_CODE_MFG_SENSOR_NUMERIC_INVALID,
                            rule_type=RuleType.DATA_TYPE,
                            severity=FindingSeverity.ERROR,
                            affected_column=col,
                            affected_record_ids=violating_ids,
                            explanation=f"Column '{col}' contains non-numeric or non-finite values in {len(violating_ids)} record(s).",
                            detected=True,
                        )
                    )
                    finding_idx += 1

        # 7. Non-negative measurements check
        if rule_config.check_non_negative_measurements:
            for col in NON_NEGATIVE_SENSOR_COLUMNS:
                if col not in df.columns:
                    continue
                violating_ids = []
                for idx, val in df[col].items():
                    if pd.isna(val):
                        continue
                    try:
                        num = float(val)
                        if num < 0:
                            violating_ids.append(get_record_id(idx))
                    except (ValueError, TypeError):
                        pass

                if violating_ids:
                    findings.append(
                        ValidationFinding(
                            finding_id=f"FIND-MFG-NEG-{finding_idx}",
                            rule_id=RULE_CODE_MFG_MEASUREMENT_NEGATIVE,
                            rule_type=RuleType.VALUE_RANGE,
                            severity=FindingSeverity.ERROR,
                            affected_column=col,
                            affected_record_ids=violating_ids,
                            explanation=f"Physical telemetry column '{col}' contains negative measurements in {len(violating_ids)} record(s).",
                            detected=True,
                        )
                    )
                    finding_idx += 1

        # 8. Quality percentage range [0.0, 100.0] check
        if rule_config.check_quality_pass_rate_bounds and "quality_pass_rate_pct" in df.columns:
            violating_ids = []
            for idx, val in df["quality_pass_rate_pct"].items():
                if pd.isna(val):
                    continue
                try:
                    pct = float(val)
                    if pct < 0.0 or pct > 100.0:
                        violating_ids.append(get_record_id(idx))
                except (ValueError, TypeError):
                    violating_ids.append(get_record_id(idx))

            if violating_ids:
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-QUAL-{finding_idx}",
                        rule_id=RULE_CODE_MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS,
                        rule_type=RuleType.VALUE_RANGE,
                        severity=FindingSeverity.ERROR,
                        affected_column="quality_pass_rate_pct",
                        affected_record_ids=violating_ids,
                        explanation=f"Column 'quality_pass_rate_pct' contains values outside valid 0-100% range in {len(violating_ids)} record(s).",
                        detected=True,
                    )
                )
                finding_idx += 1

        # 9. Production consistency: defect_count <= units_produced
        if rule_config.check_production_consistency and "units_produced" in df.columns and "defect_count" in df.columns:
            violating_ids = []
            for idx, row in df.iterrows():
                u_val = row["units_produced"]
                d_val = row["defect_count"]
                if pd.isna(u_val) or pd.isna(d_val):
                    continue
                try:
                    u = float(u_val)
                    d = float(d_val)
                    if d < 0 or (d > u and u >= 0) or (u == 0 and d > 0):
                        violating_ids.append(get_record_id(idx))
                except (ValueError, TypeError):
                    pass

            if violating_ids:
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-PRD-{finding_idx}",
                        rule_id=RULE_CODE_MFG_PRODUCTION_INCONSISTENCY,
                        rule_type=RuleType.CONSISTENCY,
                        severity=FindingSeverity.ERROR,
                        affected_column="defect_count",
                        affected_record_ids=violating_ids,
                        explanation=f"Production inconsistency: 'defect_count' exceeds 'units_produced' in {len(violating_ids)} record(s).",
                        detected=True,
                    )
                )
                finding_idx += 1

        # 10. Configurable temperature bounds check
        if rule_config.check_temperature_bounds and "temperature_c" in df.columns:
            t_min = rule_config.temperature_min_c
            t_max = rule_config.temperature_max_c
            violating_ids = []
            for idx, val in df["temperature_c"].items():
                if pd.isna(val):
                    continue
                try:
                    temp = float(val)
                    if temp < t_min or temp > t_max:
                        violating_ids.append(get_record_id(idx))
                except (ValueError, TypeError):
                    pass

            if violating_ids:
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-TEMP-{finding_idx}",
                        rule_id=RULE_CODE_MFG_TEMPERATURE_OUT_OF_BOUNDS,
                        rule_type=RuleType.VALUE_RANGE,
                        severity=FindingSeverity.WARNING,
                        affected_column="temperature_c",
                        affected_record_ids=violating_ids,
                        explanation=f"Sensor 'temperature_c' violated operating thresholds [{t_min}°C, {t_max}°C] in {len(violating_ids)} record(s).",
                        detected=True,
                    )
                )
                finding_idx += 1

        # 11. Expected record count check (CONFIGURABLE - False in baseline)
        if rule_config.check_expected_record_count:
            expected = rule_config.expected_record_count if rule_config.expected_record_count is not None else reference_row_count
            if expected is not None and len(df) != expected:
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-MFG-ROW-{finding_idx}",
                        rule_id=RULE_CODE_MFG_EXPECTED_RECORD_COUNT_MISMATCH,
                        rule_type=RuleType.VALUE_RANGE,
                        severity=FindingSeverity.ERROR,
                        affected_column=None,
                        affected_record_ids=[],
                        explanation=f"Telemetry stream count mismatch: expected {expected} readings, but observed {len(df)} readings.",
                        detected=True,
                    )
                )
                finding_idx += 1

        return findings

    def apply_mutation(
        self,
        df: pd.DataFrame,
        spec: MutationSpec,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply a synthetic data fault to a fresh deep copy of a manufacturing DataFrame."""
        mutated_df = df.copy(deep=True)
        mtype = spec.mutation_type

        target_rec_id = spec.target_record_id or spec.params.get("target_reading_id") or spec.params.get("target_transaction_id")
        target_row_idx = spec.params.get("row_index")

        # 1. DUPLICATE_SENSOR_READING (or DUPLICATE_ROW)
        if mtype in (MutationType.DUPLICATE_SENSOR_READING, MutationType.DUPLICATE_ROW):
            idx, rec_id, err = _resolve_mfg_target_index(mutated_df, target_rec_id, target_row_idx)
            if err:
                return mutated_df, {"applied": False, "failure_reason": err}

            row_to_duplicate = mutated_df.iloc[[idx]].copy()
            mutated_df = pd.concat([mutated_df, row_to_duplicate], ignore_index=True)
            new_row_idx = len(mutated_df) - 1

            metadata = {
                "applied": True,
                "mutation_id": spec.mutation_id,
                "mutation_type": mtype.value,
                "target_record_id": rec_id,
                "target_column": "reading_id",
                "affected_record_ids": [rec_id],
                "affected_row_indices": [idx, new_row_idx],
                "old_row_count": len(df),
                "new_row_count": len(mutated_df),
                "expected_rule_code": RULE_CODE_MFG_READING_ID_DUPLICATE,
                "alternative_expected_rule_codes": [
                    RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE,
                ],
            }
            return mutated_df, metadata

        # 2. MISSING_SENSOR_VALUE (or MISSING_REQUIRED_VALUE)
        if mtype in (MutationType.MISSING_SENSOR_VALUE, MutationType.MISSING_REQUIRED_VALUE):
            target_col = spec.target_column or spec.params.get("target_column") or "temperature_c"
            if target_col not in mutated_df.columns:
                return mutated_df, {
                    "applied": False,
                    "failure_reason": f"Target sensor column '{target_col}' not found in dataset",
                }

            idx, rec_id, err = _resolve_mfg_target_index(mutated_df, target_rec_id, target_row_idx)
            if err:
                return mutated_df, {"applied": False, "failure_reason": err}

            current_val = mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)]
            if pd.isna(current_val):
                return mutated_df, {
                    "applied": False,
                    "failure_reason": f"Target cell ({rec_id}, {target_col}) is already null; no-op",
                }

            mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)] = np.nan

            metadata = {
                "applied": True,
                "mutation_id": spec.mutation_id,
                "mutation_type": mtype.value,
                "target_record_id": rec_id,
                "target_column": target_col,
                "affected_record_ids": [rec_id],
                "affected_row_indices": [idx],
                "old_value": str(current_val),
                "new_value": None,
                "expected_rule_code": RULE_CODE_MFG_REQUIRED_VALUE_MISSING,
            }
            return mutated_df, metadata

        # 3. INVALID_SENSOR_VALUE
        if mtype == MutationType.INVALID_SENSOR_VALUE:
            target_col = spec.target_column or spec.params.get("target_column") or "vibration_mm_s"
            if target_col not in mutated_df.columns:
                return mutated_df, {
                    "applied": False,
                    "failure_reason": f"Target sensor column '{target_col}' not found in dataset",
                }

            idx, rec_id, err = _resolve_mfg_target_index(mutated_df, target_rec_id, target_row_idx)
            if err:
                return mutated_df, {"applied": False, "failure_reason": err}

            current_val = mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)]

            # Choose sensible invalid value based on target column if not provided
            injected_val = spec.params.get("value")
            if injected_val is None:
                if target_col == "temperature_c":
                    injected_val = 150.0  # Excessive operating temperature
                elif target_col in ("pressure_bar", "vibration_mm_s", "motor_current_a", "power_kw", "energy_kwh_20min"):
                    injected_val = -2.5   # Physical impossibility
                elif target_col == "quality_pass_rate_pct":
                    injected_val = 125.0  # Percentage out of 0-100 range
                else:
                    injected_val = -10.0

            mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)] = injected_val

            # Determine expected rule code
            if target_col == "temperature_c" and float(injected_val) > 95.0:
                expected_rule = RULE_CODE_MFG_TEMPERATURE_OUT_OF_BOUNDS
            elif target_col == "quality_pass_rate_pct":
                expected_rule = RULE_CODE_MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS
            elif target_col in NON_NEGATIVE_SENSOR_COLUMNS and float(injected_val) < 0:
                expected_rule = RULE_CODE_MFG_MEASUREMENT_NEGATIVE
            else:
                expected_rule = RULE_CODE_MFG_MEASUREMENT_NEGATIVE

            metadata = {
                "applied": True,
                "mutation_id": spec.mutation_id,
                "mutation_type": mtype.value,
                "target_record_id": rec_id,
                "target_column": target_col,
                "affected_record_ids": [rec_id],
                "affected_row_indices": [idx],
                "old_value": str(current_val),
                "new_value": injected_val,
                "expected_rule_code": expected_rule,
            }
            return mutated_df, metadata

        # 4. DROPPED_SENSOR_READING (or DROPPED_ROW)
        if mtype in (MutationType.DROPPED_SENSOR_READING, MutationType.DROPPED_ROW):
            idx, rec_id, err = _resolve_mfg_target_index(mutated_df, target_rec_id, target_row_idx)
            if err:
                return mutated_df, {"applied": False, "failure_reason": err}

            dropped_dict = mutated_df.iloc[idx].to_dict()
            mutated_df = mutated_df.drop(mutated_df.index[idx]).reset_index(drop=True)

            metadata = {
                "applied": True,
                "mutation_id": spec.mutation_id,
                "mutation_type": mtype.value,
                "target_record_id": rec_id,
                "target_column": None,
                "affected_record_ids": [rec_id],
                "affected_row_indices": [idx],
                "dropped_record": {k: str(v) for k, v in dropped_dict.items()},
                "old_row_count": len(df),
                "new_row_count": len(mutated_df),
                "expected_rule_code": RULE_CODE_MFG_EXPECTED_RECORD_COUNT_MISMATCH,
            }
            return mutated_df, metadata

        # 5. INVALID_PRODUCTION_VALUE
        if mtype == MutationType.INVALID_PRODUCTION_VALUE:
            target_col = spec.target_column or "defect_count"
            if target_col not in mutated_df.columns:
                return mutated_df, {
                    "applied": False,
                    "failure_reason": f"Target production column '{target_col}' not found in dataset",
                }

            idx, rec_id, err = _resolve_mfg_target_index(mutated_df, target_rec_id, target_row_idx)
            if err:
                return mutated_df, {"applied": False, "failure_reason": err}

            current_val = mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)]
            units_val = mutated_df.iat[idx, mutated_df.columns.get_loc("units_produced")] if "units_produced" in mutated_df.columns else 10

            injected_val = spec.params.get("value")
            if injected_val is None:
                # Set defect_count significantly higher than units_produced
                try:
                    injected_val = int(units_val) + 15 if pd.notna(units_val) else 50
                except Exception:
                    injected_val = 50

            mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)] = injected_val

            metadata = {
                "applied": True,
                "mutation_id": spec.mutation_id,
                "mutation_type": mtype.value,
                "target_record_id": rec_id,
                "target_column": target_col,
                "affected_record_ids": [rec_id],
                "affected_row_indices": [idx],
                "old_value": str(current_val),
                "new_value": injected_val,
                "expected_rule_code": RULE_CODE_MFG_PRODUCTION_INCONSISTENCY,
            }
            return mutated_df, metadata

        return mutated_df, {
            "applied": False,
            "failure_reason": f"Unsupported mutation type '{mtype}' for manufacturing domain",
        }

    def calculate_metrics(self, df: pd.DataFrame) -> PipelineMetrics:
        """Calculate real industrial telemetry and production metrics from actual DataFrame."""
        total_readings = int(len(df))

        # Unique entities
        unique_machines = int(df["machine_id"].dropna().nunique()) if "machine_id" in df.columns else 0
        unique_facilities = int(df["facility_id"].dropna().nunique()) if "facility_id" in df.columns else 0

        # Production and defect counts
        if "units_produced" in df.columns:
            total_units = int(pd.to_numeric(df["units_produced"], errors="coerce").fillna(0).sum())
        else:
            total_units = 0

        if "defect_count" in df.columns:
            total_defects = int(pd.to_numeric(df["defect_count"], errors="coerce").fillna(0).sum())
        else:
            total_defects = 0

        # Energy consumption: Sum 20-min intervals if present
        if "energy_kwh_20min" in df.columns:
            total_energy = float(round(pd.to_numeric(df["energy_kwh_20min"], errors="coerce").dropna().sum(), 2))
        else:
            total_energy = 0.0

        # Temperature stats
        if "temperature_c" in df.columns:
            temp_series = pd.to_numeric(df["temperature_c"], errors="coerce").dropna()
            avg_temp = float(round(temp_series.mean(), 2)) if len(temp_series) > 0 else 0.0
            max_temp = float(round(temp_series.max(), 2)) if len(temp_series) > 0 else 0.0
        else:
            avg_temp, max_temp = 0.0, 0.0

        # Vibration stats
        if "vibration_mm_s" in df.columns:
            vib_series = pd.to_numeric(df["vibration_mm_s"], errors="coerce").dropna()
            avg_vib = float(round(vib_series.mean(), 3)) if len(vib_series) > 0 else 0.0
            max_vib = float(round(vib_series.max(), 3)) if len(vib_series) > 0 else 0.0
        else:
            avg_vib, max_vib = 0.0, 0.0

        # Pressure stats
        if "pressure_bar" in df.columns:
            press_series = pd.to_numeric(df["pressure_bar"], errors="coerce").dropna()
            avg_press = float(round(press_series.mean(), 2)) if len(press_series) > 0 else 0.0
        else:
            avg_press = 0.0

        # Motor current stats
        if "motor_current_a" in df.columns:
            cur_series = pd.to_numeric(df["motor_current_a"], errors="coerce").dropna()
            avg_current = float(round(cur_series.mean(), 2)) if len(cur_series) > 0 else 0.0
        else:
            avg_current = 0.0

        # Quality pass rate stats
        if "quality_pass_rate_pct" in df.columns:
            q_series = pd.to_numeric(df["quality_pass_rate_pct"], errors="coerce").dropna()
            avg_pass_rate = float(round(q_series.mean(), 2)) if len(q_series) > 0 else 100.0
        else:
            avg_pass_rate = 100.0

        structured_mfg = {
            "total_readings": total_readings,
            "unique_machines": unique_machines,
            "unique_facilities": unique_facilities,
            "total_units_produced": total_units,
            "total_defect_count": total_defects,
            "total_energy_kwh": total_energy,
            "avg_temperature_c": avg_temp,
            "max_temperature_c": max_temp,
            "avg_vibration_mm_s": avg_vib,
            "max_vibration_mm_s": max_vib,
            "avg_pressure_bar": avg_press,
            "avg_motor_current_a": avg_current,
            "avg_quality_pass_rate_pct": avg_pass_rate,
        }

        return PipelineMetrics(
            domain="manufacturing",
            total_readings=total_readings,
            unique_machines=unique_machines,
            unique_facilities=unique_facilities,
            total_units_produced=total_units,
            total_defect_count=total_defects,
            total_energy_kwh=total_energy,
            avg_temperature_c=avg_temp,
            max_temperature_c=max_temp,
            avg_vibration_mm_s=avg_vib,
            max_vibration_mm_s=max_vib,
            avg_pressure_bar=avg_press,
            avg_motor_current_a=avg_current,
            avg_quality_pass_rate_pct=avg_pass_rate,
            manufacturing_metrics=structured_mfg,
            additional_metrics={
                "metric_aggregation": "Industrial batch summation for energy/production; arithmetic mean for physical telemetry",
            },
        )

    def calculate_metric_deltas(
        self,
        baseline: PipelineMetrics,
        mutated: PipelineMetrics,
    ) -> Dict[str, Any]:
        """Compute operational drift between clean baseline and mutated telemetry."""
        readings_delta = (mutated.total_readings or 0) - (baseline.total_readings or 0)
        units_delta = (mutated.total_units_produced or 0) - (baseline.total_units_produced or 0)
        defects_delta = (mutated.total_defect_count or 0) - (baseline.total_defect_count or 0)
        energy_delta = round((mutated.total_energy_kwh or 0.0) - (baseline.total_energy_kwh or 0.0), 2)
        temp_delta = round((mutated.avg_temperature_c or 0.0) - (baseline.avg_temperature_c or 0.0), 2)
        vib_delta = round((mutated.avg_vibration_mm_s or 0.0) - (baseline.avg_vibration_mm_s or 0.0), 3)
        max_temp_delta = round((mutated.max_temperature_c or 0.0) - (baseline.max_temperature_c or 0.0), 2)
        max_vib_delta = round((mutated.max_vibration_mm_s or 0.0) - (baseline.max_vibration_mm_s or 0.0), 3)

        return {
            "readings_baseline": baseline.total_readings,
            "readings_mutated": mutated.total_readings,
            "readings_delta": readings_delta,
            "units_produced_baseline": baseline.total_units_produced,
            "units_produced_mutated": mutated.total_units_produced,
            "units_produced_delta": units_delta,
            "defects_baseline": baseline.total_defect_count,
            "defects_mutated": mutated.total_defect_count,
            "defects_delta": defects_delta,
            "energy_kwh_baseline": baseline.total_energy_kwh,
            "energy_kwh_mutated": mutated.total_energy_kwh,
            "energy_kwh_delta": energy_delta,
            "avg_temperature_baseline": baseline.avg_temperature_c,
            "avg_temperature_mutated": mutated.avg_temperature_c,
            "avg_temperature_delta": temp_delta,
            "max_temperature_baseline": baseline.max_temperature_c,
            "max_temperature_mutated": mutated.max_temperature_c,
            "max_temperature_delta": max_temp_delta,
            "avg_vibration_baseline": baseline.avg_vibration_mm_s,
            "avg_vibration_mutated": mutated.avg_vibration_mm_s,
            "avg_vibration_delta": vib_delta,
            "max_vibration_baseline": baseline.max_vibration_mm_s,
            "max_vibration_mutated": mutated.max_vibration_mm_s,
            "max_vibration_delta": max_vib_delta,
        }

    def generate_recommendations(
        self,
        surviving_evaluations: List[MutationEvaluation],
    ) -> List[RuleRecommendation]:
        """Generate targeted rule recommendations for manufacturing faults that escaped validation."""
        recommendations: List[RuleRecommendation] = []
        seen_keys: set = set()
        rec_counter = 1

        for eval_item in surviving_evaluations:
            if eval_item.detected is not False or not eval_item.applied:
                continue

            spec = eval_item.mutation_spec
            mtype = spec.mutation_type
            target_col = spec.target_column

            dedup_key = f"{mtype.value}::{target_col}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            rec_id = f"REC-MFG-{rec_counter:03d}"
            rec_counter += 1

            if mtype in (MutationType.DUPLICATE_SENSOR_READING, MutationType.DUPLICATE_ROW):
                recommendations.append(
                    RuleRecommendation(
                        recommendation_id=rec_id,
                        rule_type=RuleType.UNIQUENESS,
                        target_column="machine_id, timestamp",
                        description="Enforce composite uniqueness constraint on (machine_id, timestamp) and reading_id",
                        rationale=(
                            f"Mutation '{spec.mutation_id}' duplicated an industrial sensor reading without detection, "
                            "silently distorting energy consumption and unit counts. Enabling uniqueness safeguards "
                            "on (machine_id, timestamp) prevents ingestion replay faults."
                        ),
                        suggested_rule_config={
                            "check_machine_timestamp_unique": True,
                            "check_reading_id_unique": True,
                        },
                        code_snippet="df.duplicated(subset=['machine_id', 'timestamp']).any() == False",
                        status=RecommendationStatus.SUGGESTED,
                    )
                )

            elif mtype in (MutationType.MISSING_SENSOR_VALUE, MutationType.MISSING_REQUIRED_VALUE):
                col = target_col or "temperature_c"
                recommendations.append(
                    RuleRecommendation(
                        recommendation_id=rec_id,
                        rule_type=RuleType.NOT_NULL,
                        target_column=col,
                        description=f"Enforce mandatory NOT NULL constraint on sensor column '{col}'",
                        rationale=(
                            f"Mutation '{spec.mutation_id}' removed required telemetry values from '{col}' without being caught. "
                            "Missing sensor signals corrupt condition-monitoring calculations."
                        ),
                        suggested_rule_config={"check_required_values": True},
                        code_snippet=f"df['{col}'].isna().any() == False",
                        status=RecommendationStatus.SUGGESTED,
                    )
                )

            elif mtype == MutationType.INVALID_SENSOR_VALUE:
                col = target_col or "vibration_mm_s"
                if col == "temperature_c":
                    recommendations.append(
                        RuleRecommendation(
                            recommendation_id=rec_id,
                            rule_type=RuleType.VALUE_RANGE,
                            target_column="temperature_c",
                            description="Enforce operating temperature range safeguard [40.0°C, 95.0°C]",
                            rationale=(
                                f"Mutation '{spec.mutation_id}' injected an out-of-bounds temperature that escaped detection. "
                                "Operating temperature bounds identify thermal anomalies before machinery damage occurs."
                            ),
                            suggested_rule_config={"check_temperature_bounds": True},
                            code_snippet="(df['temperature_c'] >= 40.0) & (df['temperature_c'] <= 95.0)",
                            status=RecommendationStatus.SUGGESTED,
                        )
                    )
                else:
                    recommendations.append(
                        RuleRecommendation(
                            recommendation_id=rec_id,
                            rule_type=RuleType.VALUE_RANGE,
                            target_column=col,
                            description=f"Enforce non-negative physical measurement rule on '{col}'",
                            rationale=(
                                f"Mutation '{spec.mutation_id}' injected a negative value into '{col}' that escaped detection. "
                                "Physical sensor signals cannot be negative."
                            ),
                            suggested_rule_config={"check_non_negative_measurements": True},
                            code_snippet=f"(df['{col}'] >= 0.0).all()",
                            status=RecommendationStatus.SUGGESTED,
                        )
                    )

            elif mtype == MutationType.INVALID_PRODUCTION_VALUE:
                recommendations.append(
                    RuleRecommendation(
                        recommendation_id=rec_id,
                        rule_type=RuleType.CONSISTENCY,
                        target_column="defect_count",
                        description="Enforce production consistency rule: defect_count <= units_produced",
                        rationale=(
                            f"Mutation '{spec.mutation_id}' injected an invalid defect count exceeding produced units. "
                            "Production accounting rules must verify that defects never exceed total manufactured units."
                        ),
                        suggested_rule_config={"check_production_consistency": True},
                        code_snippet="(df['defect_count'] <= df['units_produced']).all()",
                        status=RecommendationStatus.SUGGESTED,
                    )
                )

            elif mtype in (MutationType.DROPPED_SENSOR_READING, MutationType.DROPPED_ROW):
                recommendations.append(
                    RuleRecommendation(
                        recommendation_id=rec_id,
                        rule_type=RuleType.VALUE_RANGE,
                        target_column="row_count",
                        description="Enforce sensor-stream expected reading count reconciliation",
                        rationale=(
                            f"Mutation '{spec.mutation_id}' dropped a sensor reading without triggering an alert. "
                            "Row count reconciliation identifies missing packet drops in telemetry streams."
                        ),
                        suggested_rule_config={"check_expected_record_count": True},
                        code_snippet="len(df) == expected_record_count",
                        status=RecommendationStatus.SUGGESTED,
                    )
                )

        return recommendations

    def is_finding_relevant_to_mutation(
        self,
        finding: ValidationFinding,
        mutation_meta: Dict[str, Any],
    ) -> bool:
        expected_rule = mutation_meta.get("expected_rule_code")
        alt_rules = mutation_meta.get("alternative_expected_rule_codes", [])

        if not expected_rule or (finding.rule_id != expected_rule and finding.rule_id not in alt_rules):
            return False

        target_rec = mutation_meta.get("target_record_id")
        target_col = mutation_meta.get("target_column")

        # Column match if applicable
        if target_col and finding.affected_column and finding.affected_column != target_col:
            # Allow machine_id match for composite duplicate
            if not (target_col == "reading_id" and finding.affected_column == "machine_id"):
                return False

        # Record ID match if applicable
        if target_rec and finding.affected_record_ids:
            if target_rec not in finding.affected_record_ids:
                return False

        return True
