"""Mock targets API for testing."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from shared.storage.target_storage import target_storage
from shared.models.target import Target, TargetCreate
from shared.connectors.mock_targets import get_mock_target_data, clear_mock_target

router = APIRouter(prefix="/mock-targets", tags=["mock-targets"])


@router.post("/seed", response_model=List[Target])
async def seed_mock_targets():
    """Create sample mock targets for testing."""
    
    mock_targets = [
        TargetCreate(
            name="Mock Production Database",
            type="database",
            config={
                "connection_string": "postgresql://mock:mock@localhost:5432/production",
                "table_name": "customers",
                "database_type": "postgresql"
            }
        ),
        TargetCreate(
            name="Mock Salesforce Prod",
            type="salesforce",
            config={
                "instance_url": "https://mock-company.salesforce.com",
                "access_token": "mock_token_12345",
                "object_type": "Lead"
            }
        ),
        TargetCreate(
            name="Mock CRM API",
            type="api",
            config={
                "endpoint_url": "https://api.mock-crm.com/v1/contacts",
                "method": "POST",
                "headers": {
                    "Authorization": "Bearer mock_api_key",
                    "Content-Type": "application/json"
                }
            }
        ),
        TargetCreate(
            name="Mock Data Lake S3",
            type="s3",
            config={
                "bucket_name": "mock-data-lake",
                "region": "us-east-1",
                "path_prefix": "synthetic-data/exports",
                "file_format": "json"
            }
        )
    ]
    
    created_targets = []
    for target_create in mock_targets:
        # Check if target with same name exists
        existing = [t for t in target_storage.list() if t.name == target_create.name]
        if not existing:
            target = target_storage.create(target_create)
            created_targets.append(target)
        else:
            created_targets.append(existing[0])
    
    return created_targets


@router.get("/{target_id}/data", response_model=Dict[str, Any])
async def get_mock_target_data_endpoint(target_id: str):
    """Get data that was sent to a mock target."""
    
    target = target_storage.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    data = get_mock_target_data(target_id)
    
    return {
        "target_id": target_id,
        "target_name": target.name,
        "target_type": target.type,
        "records_count": len(data),
        "records": data
    }


@router.delete("/{target_id}/data")
async def clear_mock_target_data_endpoint(target_id: str):
    """Clear data from a mock target."""
    
    target = target_storage.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    clear_mock_target(target_id)
    
    return {
        "target_id": target_id,
        "message": "Mock target data cleared"
    }
