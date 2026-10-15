"""General CSV Profiling Domain Profile for DataTripwire.

Allows arbitrary tabular CSV datasets to be ingested, profiled, and inspected
without domain-specific mutation testing restrictions.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

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


class GeneralDomainProfile(BaseDomainProfile):
    """Fallback profile for general tabular datasets lacking a specialized domain adapter."""

    @property
    def domain_id(self) -> str:
        return "general"

    @property
    def name(self) -> str:
        return "General CSV Profiling"

    @property
    def description(self) -> str:
        return "Standard tabular profiling. Ingest and inspect data distributions across arbitrary CSV structures."

    @property
    def primary_key_column(self) -> Optional[str]:
        return None

    @property
    def required_columns(self) -> List[str]:
        return []

    @property
    def schema_columns(self) -> List[str]:
        return []

    @property
    def supported_mutation_types(self) -> List[MutationType]:
        return []

    def is_compatible(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []

    def validate(
        self,
        df: pd.DataFrame,
        config: Optional[ValidationRuleConfig] = None,
        reference_row_count: Optional[int] = None,
    ) -> List[ValidationFinding]:
        return []

    def apply_mutation(
        self,
        df: pd.DataFrame,
        spec: MutationSpec,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        return df, {
            "applied": False,
            "failure_reason": (
                "Domain-specific mutation testing is not available for General CSV Profiling. "
                "Select a compatible domain profile (such as E-commerce Sales or Manufacturing IoT) "
                "to execute mutation reliability evaluations."
            ),
        }

    def calculate_metrics(self, df: pd.DataFrame) -> PipelineMetrics:
        return PipelineMetrics(
            domain="general",
            additional_metrics={
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
            },
        )

    def calculate_metric_deltas(
        self,
        baseline: PipelineMetrics,
        mutated: PipelineMetrics,
    ) -> Dict[str, Any]:
        return {}

    def generate_recommendations(
        self,
        surviving_evaluations: List[MutationEvaluation],
    ) -> List[RuleRecommendation]:
        return []

    def is_finding_relevant_to_mutation(
        self,
        finding: ValidationFinding,
        mutation_meta: Dict[str, Any],
    ) -> bool:
        return False
