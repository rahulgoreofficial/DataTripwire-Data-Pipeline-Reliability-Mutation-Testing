"""E-commerce Sales Domain Profile for DataTripwire.

Encapsulates schema rules, validation safeguards, mutations, and
monetary revenue metrics for transactional retail datasets.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from datatripwire.config import (
    PRIMARY_KEY_COLUMN,
    SALES_SCHEMA_COLUMNS,
)
from datatripwire.domain.enums import MutationType
from datatripwire.domain.models import (
    MutationEvaluation,
    MutationSpec,
    PipelineMetrics,
    RuleRecommendation,
    ValidationFinding,
)
from datatripwire.domains.base import BaseDomainProfile
from datatripwire.schemas import ValidationRuleConfig
from datatripwire.services.metrics import (
    calculate_metric_deltas as calc_sales_deltas,
    calculate_sales_metrics,
)
from datatripwire.services.mutation_engine import apply_mutation as apply_sales_mutation
from datatripwire.services.recommendations import generate_recommendations_for_surviving_mutations
from datatripwire.services.validators import run_validation as run_sales_validation


class SalesDomainProfile(BaseDomainProfile):
    """Adapter for e-commerce transactional sales data pipelines."""

    @property
    def domain_id(self) -> str:
        return "sales"

    @property
    def name(self) -> str:
        return "E-commerce Sales"

    @property
    def description(self) -> str:
        return "Transactional retail pipeline tracking orders, customer accounts, quantities, and sales revenue."

    @property
    def primary_key_column(self) -> Optional[str]:
        return PRIMARY_KEY_COLUMN

    @property
    def required_columns(self) -> List[str]:
        return list(SALES_SCHEMA_COLUMNS)

    @property
    def schema_columns(self) -> List[str]:
        return list(SALES_SCHEMA_COLUMNS)

    @property
    def supported_mutation_types(self) -> List[MutationType]:
        return [
            MutationType.DUPLICATE_ROW,
            MutationType.MISSING_REQUIRED_VALUE,
            MutationType.INVALID_QUANTITY,
            MutationType.INVALID_UNIT_PRICE,
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
        return run_sales_validation(
            df=df,
            config=config,
            reference_row_count=reference_row_count,
        )

    def apply_mutation(
        self,
        df: pd.DataFrame,
        spec: MutationSpec,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        return apply_sales_mutation(df=df, spec=spec)

    def calculate_metrics(self, df: pd.DataFrame) -> PipelineMetrics:
        metrics = calculate_sales_metrics(df)
        object.__setattr__(metrics, "domain", "sales")
        return metrics

    def calculate_metric_deltas(
        self,
        baseline: PipelineMetrics,
        mutated: PipelineMetrics,
    ) -> Dict[str, Any]:
        return calc_sales_deltas(baseline=baseline, mutated=mutated)

    def generate_recommendations(
        self,
        surviving_evaluations: List[MutationEvaluation],
    ) -> List[RuleRecommendation]:
        return generate_recommendations_for_surviving_mutations(surviving_evaluations)

    def is_finding_relevant_to_mutation(
        self,
        finding: ValidationFinding,
        mutation_meta: Dict[str, Any],
    ) -> bool:
        expected_rule = mutation_meta.get("expected_rule_code")
        if not expected_rule or finding.rule_id != expected_rule:
            return False

        target_rec = mutation_meta.get("target_record_id")
        target_col = mutation_meta.get("target_column")

        if target_col and finding.affected_column and finding.affected_column != target_col:
            return False

        if target_rec and finding.affected_record_ids:
            if target_rec not in finding.affected_record_ids:
                return False

        return True
