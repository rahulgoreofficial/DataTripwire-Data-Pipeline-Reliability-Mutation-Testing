"""Base domain profile abstraction for DataTripwire.

Defines the contract for domain-specific schemas, validation engines,
mutation operators, business metrics, and rule recommendations.
"""

from abc import ABC, abstractmethod
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
from datatripwire.schemas import ValidationRuleConfig


class BaseDomainProfile(ABC):
    """Abstract base class for domain-specific reliability testing adapters."""

    @property
    @abstractmethod
    def domain_id(self) -> str:
        """Machine-readable domain identifier (e.g., 'sales', 'manufacturing', 'general')."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable display name for the domain."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Summary explanation of what this data domain represents."""
        ...

    @property
    @abstractmethod
    def primary_key_column(self) -> Optional[str]:
        """Primary record identifier column name, if applicable."""
        ...

    @property
    @abstractmethod
    def required_columns(self) -> List[str]:
        """Essential columns required to enable mutation testing in this domain."""
        ...

    @property
    @abstractmethod
    def schema_columns(self) -> List[str]:
        """Full canonical schema column specifications for this domain."""
        ...

    @property
    @abstractmethod
    def supported_mutation_types(self) -> List[MutationType]:
        """List of synthetic mutation operators supported by this domain."""
        ...

    @abstractmethod
    def is_compatible(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Check whether a DataFrame conforms to this domain's requirements.
        
        Returns:
            Tuple of (is_compatible: bool, missing_required_columns: List[str])
        """
        ...

    @abstractmethod
    def validate(
        self,
        df: pd.DataFrame,
        config: Optional[ValidationRuleConfig] = None,
        reference_row_count: Optional[int] = None,
    ) -> List[ValidationFinding]:
        """Run domain validation rules against a dataset DataFrame."""
        ...

    @abstractmethod
    def apply_mutation(
        self,
        df: pd.DataFrame,
        spec: MutationSpec,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply a domain-specific synthetic mutation to a deep copy of the DataFrame."""
        ...

    @abstractmethod
    def calculate_metrics(self, df: pd.DataFrame) -> PipelineMetrics:
        """Calculate real domain baseline or mutated metrics from tabular data."""
        ...

    @abstractmethod
    def calculate_metric_deltas(
        self,
        baseline: PipelineMetrics,
        mutated: PipelineMetrics,
    ) -> Dict[str, Any]:
        """Quantify differences between clean baseline and mutated metrics."""
        ...

    @abstractmethod
    def generate_recommendations(
        self,
        surviving_evaluations: List[MutationEvaluation],
    ) -> List[RuleRecommendation]:
        """Generate targeted rule recommendations for surviving faults in this domain."""
        ...

    @abstractmethod
    def is_finding_relevant_to_mutation(
        self,
        finding: ValidationFinding,
        mutation_meta: Dict[str, Any],
    ) -> bool:
        """Determine whether a validation finding directly trapped the injected fault."""
        ...

    def to_metadata(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Serialize domain metadata for API responses and UI configuration."""
        meta: Dict[str, Any] = {
            "domain_id": self.domain_id,
            "name": self.name,
            "description": self.description,
            "primary_key": self.primary_key_column,
            "required_columns": self.required_columns,
            "schema_columns": self.schema_columns,
            "supported_mutation_types": [m.value for m in self.supported_mutation_types],
        }
        if df is not None:
            compatible, missing = self.is_compatible(df)
            meta["is_compatible"] = compatible
            meta["missing_columns"] = missing
        return meta
