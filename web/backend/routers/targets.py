"""Target management API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status

from shared.models.target import (
    Target,
    TargetCreate,
    TargetUpdate,
    TargetTestResult,
    TargetType
)
from shared.storage.target_storage import target_storage

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("/", response_model=Target, status_code=status.HTTP_201_CREATED)
async def create_target(target_create: TargetCreate):
    """Create a new target."""
    try:
        target = target_storage.create(target_create)
        return target
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create target: {str(e)}"
        )


@router.get("/", response_model=List[Target])
async def list_targets(active_only: bool = True):
    """List all targets."""
    try:
        targets = target_storage.list(active_only=active_only)
        return targets
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list targets: {str(e)}"
        )


@router.get("/{target_id}", response_model=Target)
async def get_target(target_id: str):
    """Get a target by ID."""
    target = target_storage.get(target_id)
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target {target_id} not found"
        )
    
    return target


@router.put("/{target_id}", response_model=Target)
async def update_target(target_id: str, target_update: TargetUpdate):
    """Update a target."""
    target = target_storage.update(target_id, target_update)
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target {target_id} not found"
        )
    
    return target


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(target_id: str):
    """Delete a target."""
    success = target_storage.delete(target_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target {target_id} not found"
        )


@router.post("/{target_id}/test", response_model=TargetTestResult)
async def test_target(target_id: str):
    """Test a target connection."""
    target = target_storage.get(target_id)
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target {target_id} not found"
        )
    
    # Basic validation for now - will implement actual connection tests later
    try:
        if target.type == TargetType.DATABASE:
            # Validate required fields
            if not target.config.get("connection_string") or not target.config.get("table_name"):
                return TargetTestResult(
                    success=False,
                    message="Missing required fields: connection_string or table_name"
                )
        
        elif target.type == TargetType.SALESFORCE:
            if not target.config.get("instance_url") or not target.config.get("access_token"):
                return TargetTestResult(
                    success=False,
                    message="Missing required fields: instance_url or access_token"
                )
        
        elif target.type == TargetType.API:
            if not target.config.get("endpoint_url"):
                return TargetTestResult(
                    success=False,
                    message="Missing required field: endpoint_url"
                )
        
        elif target.type == TargetType.S3:
            if not target.config.get("bucket_name"):
                return TargetTestResult(
                    success=False,
                    message="Missing required field: bucket_name"
                )
        
        return TargetTestResult(
            success=True,
            message=f"Target configuration is valid",
            details={"type": target.type}
        )
    
    except Exception as e:
        return TargetTestResult(
            success=False,
            message=f"Test failed: {str(e)}"
        )
