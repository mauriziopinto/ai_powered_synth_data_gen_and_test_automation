"""Configuration management API endpoints.

Provides endpoints for:
- Saving configurations
- Loading configurations
- Listing available configurations
- Deleting configurations
- Validating configurations

Validates Requirements 11.1, 11.2
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from shared.config.manager import ConfigurationManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize configuration manager
config_manager = ConfigurationManager()


class SchemaField(BaseModel):
    """Schema field definition."""
    name: str
    type: str
    constraints: Optional[dict] = None


class WorkflowConfigRequest(BaseModel):
    """Workflow configuration request model."""
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    schema_fields: List[SchemaField] = Field(..., description="Schema definition")
    generation_params: dict = Field(..., description="Generation parameters")
    sdv_model: str = Field(default="GaussianCopula", description="SDV model type")
    bedrock_model: Optional[str] = Field(None, description="Bedrock model ID")
    edge_case_frequency: float = Field(default=0.05, description="Edge case frequency")
    target_systems: List[dict] = Field(default_factory=list, description="Target systems")
    project_id: Optional[str] = None
    team_id: Optional[str] = None


class WorkflowConfigResponse(BaseModel):
    """Workflow configuration response model."""
    config_id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str
    schema_fields: List[SchemaField]
    generation_params: dict
    sdv_model: str
    bedrock_model: Optional[str]
    edge_case_frequency: float
    target_systems: List[dict]
    project_id: Optional[str]
    team_id: Optional[str]


class ConfigListItem(BaseModel):
    """Configuration list item."""
    config_id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str


class ValidationError(BaseModel):
    """Validation error detail."""
    field: str
    message: str


class ValidationResponse(BaseModel):
    """Configuration validation response."""
    valid: bool
    errors: List[ValidationError] = Field(default_factory=list)


@router.post("/", response_model=WorkflowConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_configuration(config: WorkflowConfigRequest):
    """Create a new workflow configuration.
    
    Validates Requirement 11.1: Enable complete configuration without requiring code.
    
    Args:
        config: Configuration request
    
    Returns:
        Created configuration with ID
    """
    try:
        # Convert to internal format
        config_data = {
            'name': config.name,
            'description': config.description,
            'schema': {
                'fields': [field.dict() for field in config.schema_fields]
            },
            'generation_params': config.generation_params,
            'sdv_model': config.sdv_model,
            'bedrock_model': config.bedrock_model,
            'edge_case_frequency': config.edge_case_frequency,
            'target_systems': config.target_systems,
            'project_id': config.project_id,
            'team_id': config.team_id
        }
        
        # Save configuration
        config_id = config_manager.save_configuration(config_data)
        
        # Load and return
        saved_config = config_manager.load_configuration(config_id)
        
        return WorkflowConfigResponse(
            config_id=config_id,
            name=saved_config['name'],
            description=saved_config.get('description'),
            created_at=saved_config.get('created_at', datetime.now().isoformat()),
            updated_at=saved_config.get('updated_at', datetime.now().isoformat()),
            schema_fields=[SchemaField(**f) for f in saved_config['schema']['fields']],
            generation_params=saved_config['generation_params'],
            sdv_model=saved_config.get('sdv_model', 'GaussianCopula'),
            bedrock_model=saved_config.get('bedrock_model'),
            edge_case_frequency=saved_config.get('edge_case_frequency', 0.05),
            target_systems=saved_config.get('target_systems', []),
            project_id=saved_config.get('project_id'),
            team_id=saved_config.get('team_id')
        )
        
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )


@router.get("/", response_model=List[ConfigListItem])
async def list_configurations(
    project_id: Optional[str] = None,
    team_id: Optional[str] = None
):
    """List all available configurations.
    
    Args:
        project_id: Optional project filter
        team_id: Optional team filter
    
    Returns:
        List of configuration summaries
    """
    try:
        configs = config_manager.list_configurations()
        
        # Filter if needed
        if project_id:
            configs = [c for c in configs if c.get('project_id') == project_id]
        if team_id:
            configs = [c for c in configs if c.get('team_id') == team_id]
        
        return [
            ConfigListItem(
                config_id=c['config_id'],
                name=c['name'],
                description=c.get('description'),
                created_at=c.get('created_at', datetime.now().isoformat()),
                updated_at=c.get('updated_at', datetime.now().isoformat())
            )
            for c in configs
        ]
        
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}"
        )


@router.get("/{config_id}", response_model=WorkflowConfigResponse)
async def get_configuration(config_id: str):
    """Get a specific configuration by ID.
    
    Args:
        config_id: Configuration ID
    
    Returns:
        Configuration details
    """
    try:
        config = config_manager.load_configuration(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )
        
        return WorkflowConfigResponse(
            config_id=config_id,
            name=config['name'],
            description=config.get('description'),
            created_at=config.get('created_at', datetime.now().isoformat()),
            updated_at=config.get('updated_at', datetime.now().isoformat()),
            schema_fields=[SchemaField(**f) for f in config['schema']['fields']],
            generation_params=config['generation_params'],
            sdv_model=config.get('sdv_model', 'GaussianCopula'),
            bedrock_model=config.get('bedrock_model'),
            edge_case_frequency=config.get('edge_case_frequency', 0.05),
            target_systems=config.get('target_systems', []),
            project_id=config.get('project_id'),
            team_id=config.get('team_id')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.put("/{config_id}", response_model=WorkflowConfigResponse)
async def update_configuration(config_id: str, config: WorkflowConfigRequest):
    """Update an existing configuration.
    
    Args:
        config_id: Configuration ID
        config: Updated configuration
    
    Returns:
        Updated configuration
    """
    try:
        # Check if exists
        existing = config_manager.load_configuration(config_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )
        
        # Update configuration
        config_data = {
            'config_id': config_id,
            'name': config.name,
            'description': config.description,
            'schema': {
                'fields': [field.dict() for field in config.schema_fields]
            },
            'generation_params': config.generation_params,
            'sdv_model': config.sdv_model,
            'bedrock_model': config.bedrock_model,
            'edge_case_frequency': config.edge_case_frequency,
            'target_systems': config.target_systems,
            'project_id': config.project_id,
            'team_id': config.team_id,
            'updated_at': datetime.now().isoformat()
        }
        
        config_manager.save_configuration(config_data, config_id=config_id)
        
        # Return updated config
        return await get_configuration(config_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_configuration(config_id: str):
    """Delete a configuration.
    
    Args:
        config_id: Configuration ID
    """
    try:
        # Check if exists
        existing = config_manager.load_configuration(config_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )
        
        config_manager.delete_configuration(config_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )


@router.post("/validate", response_model=ValidationResponse)
async def validate_configuration(config: WorkflowConfigRequest):
    """Validate a configuration without saving.
    
    Validates Requirement 11.2: Provide real-time validation feedback.
    
    Args:
        config: Configuration to validate
    
    Returns:
        Validation result with errors if any
    """
    errors = []
    
    # Validate schema fields
    if not config.schema_fields:
        errors.append(ValidationError(
            field="schema_fields",
            message="At least one schema field is required"
        ))
    
    # Validate field names
    field_names = set()
    for field in config.schema_fields:
        if not field.name:
            errors.append(ValidationError(
                field=f"schema_fields.{field.name}",
                message="Field name is required"
            ))
        if field.name in field_names:
            errors.append(ValidationError(
                field=f"schema_fields.{field.name}",
                message=f"Duplicate field name: {field.name}"
            ))
        field_names.add(field.name)
    
    # Validate edge case frequency
    if not (0 <= config.edge_case_frequency <= 1):
        errors.append(ValidationError(
            field="edge_case_frequency",
            message="Edge case frequency must be between 0 and 1"
        ))
    
    # Validate generation params
    if not config.generation_params:
        errors.append(ValidationError(
            field="generation_params",
            message="Generation parameters are required"
        ))
    
    return ValidationResponse(
        valid=len(errors) == 0,
        errors=errors
    )
