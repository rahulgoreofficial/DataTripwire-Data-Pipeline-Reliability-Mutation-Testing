"""Synthetic mutation engine for DataTripwire.

Applies controlled synthetic data faults to immutable copies of DataFrames:
- Duplicate transaction row
- Missing required value
- Invalid quantity (<= 0)
- Invalid unit price (< 0)
- Dropped row

All operations execute strictly on deep copies of the input DataFrame.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from datatripwire.domain.enums import MutationType
from datatripwire.domain.models import MutationSpec
from datatripwire.services.validators import (
    RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH,
    RULE_CODE_INVALID_TRANSACTION_DATE,
    RULE_CODE_QUANTITY_NOT_POSITIVE,
    RULE_CODE_REQUIRED_VALUE_MISSING,
    RULE_CODE_TRANSACTION_ID_DUPLICATE,
    RULE_CODE_UNIT_PRICE_NEGATIVE,
)


def _resolve_target_index(
    df: pd.DataFrame,
    target_record_id: Optional[str] = None,
    row_index: Optional[int] = None,
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """Resolve a target record ID or row index to a DataFrame integer location.
    
    Returns:
        (resolved_int_idx, record_id, error_message)
    """
    if len(df) == 0:
        return None, None, "Dataset is empty; no target record can be selected"

    if target_record_id is not None:
        clean_id = target_record_id.strip()
        if "transaction_id" not in df.columns:
            return None, None, "Dataset lacks 'transaction_id' column required to locate target record"

        matching = df[df["transaction_id"].astype(str).str.strip() == clean_id]
        if len(matching) == 0:
            return None, None, f"Target record with transaction_id '{clean_id}' was not found in dataset"
        if len(matching) > 1:
            return None, None, f"Ambiguous target: multiple records found with transaction_id '{clean_id}'"

        int_idx = df.index.get_loc(matching.index[0])
        return int_idx, clean_id, None

    if row_index is not None:
        if row_index < 0 or row_index >= len(df):
            return None, None, f"Row index {row_index} is out of bounds (0 to {len(df) - 1})"
        rec_id = str(df.iloc[row_index].get("transaction_id", f"row_{row_index}"))
        return row_index, rec_id, None

    # Default to the first available row
    rec_id = str(df.iloc[0].get("transaction_id", "row_0"))
    return 0, rec_id, None


def apply_mutation(
    df: pd.DataFrame,
    spec: MutationSpec,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Apply a synthetic mutation specification to an independent copy of a DataFrame.
    
    Args:
        df: Pristine source DataFrame (will NOT be modified).
        spec: Mutation specification.
        
    Returns:
        Tuple of (mutated_dataframe_copy, mutation_metadata).
        If mutation cannot be applied, the returned DataFrame is an unchanged copy,
        and mutation_metadata contains applied=False and a failure_reason.
    """
    # Guarantee immutability by operating exclusively on a deep copy
    mutated_df = df.copy(deep=True)
    mtype = spec.mutation_type

    target_txn_id = spec.target_record_id or spec.params.get("target_transaction_id")
    target_row_idx = spec.params.get("row_index")

    # A. DUPLICATE_ROW
    if mtype == MutationType.DUPLICATE_ROW:
        idx, rec_id, err = _resolve_target_index(mutated_df, target_txn_id, target_row_idx)
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
            "target_column": "transaction_id",
            "affected_record_ids": [rec_id],
            "affected_row_indices": [idx, new_row_idx],
            "old_row_count": len(df),
            "new_row_count": len(mutated_df),
            "expected_rule_code": RULE_CODE_TRANSACTION_ID_DUPLICATE,
        }
        return mutated_df, metadata

    # B. MISSING_REQUIRED_VALUE
    if mtype == MutationType.MISSING_REQUIRED_VALUE:
        target_col = spec.target_column or spec.params.get("target_column") or "quantity"
        if target_col not in mutated_df.columns:
            return mutated_df, {
                "applied": False,
                "failure_reason": f"Target column '{target_col}' not found in dataset",
            }

        idx, rec_id, err = _resolve_target_index(mutated_df, target_txn_id, target_row_idx)
        if err:
            return mutated_df, {"applied": False, "failure_reason": err}

        current_val = mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)]
        if pd.isna(current_val):
            return mutated_df, {
                "applied": False,
                "failure_reason": f"Target cell ({rec_id}, {target_col}) is already missing/null; mutation would be a no-op",
            }

        # Inject missing value
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
            "expected_rule_code": RULE_CODE_REQUIRED_VALUE_MISSING,
        }
        return mutated_df, metadata

    # C. INVALID_QUANTITY
    if mtype == MutationType.INVALID_QUANTITY:
        target_col = "quantity"
        if target_col not in mutated_df.columns:
            return mutated_df, {
                "applied": False,
                "failure_reason": "Dataset lacks required 'quantity' column",
            }

        idx, rec_id, err = _resolve_target_index(mutated_df, target_txn_id, target_row_idx)
        if err:
            return mutated_df, {"applied": False, "failure_reason": err}

        current_val = mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)]
        injected_val = spec.params.get("value", 0)

        # Check if already non-positive
        try:
            if not pd.isna(current_val) and float(current_val) <= 0 and float(injected_val) <= 0:
                return mutated_df, {
                    "applied": False,
                    "failure_reason": f"Target record {rec_id} already has non-positive quantity '{current_val}'; no-op",
                }
        except Exception:
            pass

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
            "expected_rule_code": RULE_CODE_QUANTITY_NOT_POSITIVE,
        }
        return mutated_df, metadata

    # D. INVALID_UNIT_PRICE
    if mtype == MutationType.INVALID_UNIT_PRICE:
        target_col = "unit_price"
        if target_col not in mutated_df.columns:
            return mutated_df, {
                "applied": False,
                "failure_reason": "Dataset lacks required 'unit_price' column",
            }

        idx, rec_id, err = _resolve_target_index(mutated_df, target_txn_id, target_row_idx)
        if err:
            return mutated_df, {"applied": False, "failure_reason": err}

        current_val = mutated_df.iat[idx, mutated_df.columns.get_loc(target_col)]
        injected_val = spec.params.get("value", -100.0)

        # Check if already negative
        try:
            if not pd.isna(current_val) and float(current_val) < 0 and float(injected_val) < 0:
                return mutated_df, {
                    "applied": False,
                    "failure_reason": f"Target record {rec_id} already has negative price '{current_val}'; no-op",
                }
        except Exception:
            pass

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
            "expected_rule_code": RULE_CODE_UNIT_PRICE_NEGATIVE,
        }
        return mutated_df, metadata

    # E. DROPPED_ROW
    if mtype == MutationType.DROPPED_ROW:
        idx, rec_id, err = _resolve_target_index(mutated_df, target_txn_id, target_row_idx)
        if err:
            return mutated_df, {"applied": False, "failure_reason": err}

        dropped_row_dict = mutated_df.iloc[idx].to_dict()
        mutated_df = mutated_df.drop(mutated_df.index[idx]).reset_index(drop=True)

        metadata = {
            "applied": True,
            "mutation_id": spec.mutation_id,
            "mutation_type": mtype.value,
            "target_record_id": rec_id,
            "target_column": None,
            "affected_record_ids": [rec_id],
            "affected_row_indices": [idx],
            "dropped_record": {k: str(v) for k, v in dropped_row_dict.items()},
            "old_row_count": len(df),
            "new_row_count": len(mutated_df),
            "expected_rule_code": RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH,
        }
        return mutated_df, metadata

    return mutated_df, {
        "applied": False,
        "failure_reason": f"Unsupported mutation type '{mtype}'",
    }
