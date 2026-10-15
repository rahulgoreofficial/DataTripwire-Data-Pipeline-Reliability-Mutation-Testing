"""Domain Registry for DataTripwire.

Manages domain adapters, automatic schema detection, and domain selection.
"""

from typing import Dict, List, Optional
import pandas as pd

from datatripwire.domains.base import BaseDomainProfile
from datatripwire.domains.general import GeneralDomainProfile
from datatripwire.domains.manufacturing import ManufacturingDomainProfile
from datatripwire.domains.sales import SalesDomainProfile


class DomainRegistry:
    """Central registry and detector for supported data domains."""

    def __init__(self):
        self._profiles: Dict[str, BaseDomainProfile] = {}
        self._register_default_profiles()

    def _register_default_profiles(self):
        self.register(SalesDomainProfile())
        self.register(ManufacturingDomainProfile())
        self.register(GeneralDomainProfile())

    def register(self, profile: BaseDomainProfile) -> None:
        """Register a new domain profile."""
        self._profiles[profile.domain_id] = profile

    def get(self, domain_id: str) -> BaseDomainProfile:
        """Retrieve a domain profile by ID, falling back to GeneralDomainProfile if unrecognized."""
        if domain_id in self._profiles:
            return self._profiles[domain_id]
        raise ValueError(
            f"Unknown domain '{domain_id}'. Available domains: {list(self._profiles.keys())}"
        )

    def detect_domain(self, df: pd.DataFrame) -> BaseDomainProfile:
        """Automatically detect the best matching domain profile based on DataFrame columns."""
        # Check Manufacturing first if manufacturing primary/telemetry columns exist
        mfg = self.get("manufacturing")
        mfg_compat, _ = mfg.is_compatible(df)
        if mfg_compat:
            return mfg

        # Check Sales
        sales = self.get("sales")
        sales_compat, _ = sales.is_compatible(df)
        if sales_compat:
            return sales

        # Fallback to General CSV Profiling
        return self.get("general")

    def list_domains(self, df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        """List all supported domains with compatibility metadata if DataFrame is provided."""
        results = []
        # Return in clean order: sales, manufacturing, general
        order = ["sales", "manufacturing", "general"]
        for domain_id in order:
            if domain_id in self._profiles:
                results.append(self._profiles[domain_id].to_metadata(df))
        return results


# Global singleton registry instance
_GLOBAL_REGISTRY: Optional[DomainRegistry] = None


def get_domain_registry() -> DomainRegistry:
    """Get or create the global domain registry singleton."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = DomainRegistry()
    return _GLOBAL_REGISTRY
