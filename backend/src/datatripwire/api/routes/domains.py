"""Domain metadata and discovery endpoints for DataTripwire."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from datatripwire.api.dependencies import get_dataset_repository
from datatripwire.domains.registry import get_domain_registry
from datatripwire.repositories.dataset_repository import DatasetRepository

router = APIRouter(prefix="/api/v1/domains", tags=["Domains"])


@router.get("", response_model=List[Dict[str, Any]])
def list_supported_domains():
    """List all registered data domains and their capability metadata."""
    registry = get_domain_registry()
    return registry.list_domains()


@router.get("/{domain_id}", response_model=Dict[str, Any])
def get_domain_details(domain_id: str):
    """Retrieve metadata, schema requirements, and supported mutations for a domain."""
    registry = get_domain_registry()
    try:
        profile = registry.get(domain_id)
        return profile.to_metadata()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
