"""Workflow execution control API endpoints.

Provides endpoints for:
- Starting workflows
- Pausing workflows
- Resuming workflows
- Aborting workflows
- Getting workflow status

Validates Requirements 11.1, 11.2, 11.3
"""

import logging
import json
from typing import Optional
from datetime import datetime
import pandas as pd
import io
from pathlib import Path
import asyncio

from fastapi import APIRouter, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Import agents
from agents.data_processor.agent import DataProcessorAgent
from agents.synthetic_data.agent import SyntheticDataAgent
from shared.utils.bedrock_client import BedrockClient, BedrockConfig
from shared.utils.agent_logger import AgentLogger

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket manager reference (set by main.py)
_ws_manager = None


def set_websocket_manager(ws_manager):
    """Set the WebSocket manager for broadcasting agent logs.
    
    Args:
        ws_manager: WebSocketManager instance from main.py
    """
    global _ws_manager
    _ws_manager = ws_manager


async def broadcast_agent_log_entry(log_entry_dict: dict):
    """Broadcast an agent log entry via WebSocket.
    
    Args:
        log_entry_dict: Log entry as dictionary
    """
    if _ws_manager:
        try:
            await _ws_manager.broadcast_agent_log(log_entry_dict)
        except Exception as e:
            logger.error(f"Failed to broadcast agent log: {str(e)}")


def initialize_bedrock_client() -> tuple[Optional[BedrockClient], Optional[BedrockConfig], bool]:
    """Initialize Bedrock client from environment variables.
    
    Returns:
        Tuple of (bedrock_client, bedrock_config, bedrock_enabled)
    """
    bedrock_client = None
    bedrock_config = None
    bedrock_enabled = False
    
    try:
        import os
        from shared.utils.aws_config import AWSConfig
        
        # Debug logging
        has_access_key = bool(os.getenv('AWS_ACCESS_KEY_ID'))
        has_secret_key = bool(os.getenv('AWS_SECRET_ACCESS_KEY'))
        logger.info(f"Bedrock init check: AWS_ACCESS_KEY_ID={has_access_key}, AWS_SECRET_ACCESS_KEY={has_secret_key}")
        
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            bedrock_config = BedrockConfig(
                model_id=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
            )
            # Create AWS config and get bedrock runtime client
            aws_config = AWSConfig(
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            bedrock_runtime_client = aws_config.get_bedrock_client()
            bedrock_client = BedrockClient(bedrock_runtime_client, bedrock_config)
            bedrock_enabled = True
            logger.info("Bedrock client initialized successfully")
        else:
            logger.warning("AWS credentials not found in environment variables")
    except Exception as bedrock_error:
        logger.warning(f"Bedrock initialization failed: {bedrock_error}. Using fallback generation.")
        bedrock_config = None
    
    return bedrock_client, bedrock_config, bedrock_enabled


def create_synthetic_agent_with_logger(
    workflow_id: str,
    workflow_state: dict,
    bedrock_client: Optional[BedrockClient] = None,
    bedrock_config: Optional[BedrockConfig] = None
) -> SyntheticDataAgent:
    """Create a SyntheticDataAgent with AgentLogger configured.
    
    Args:
        workflow_id: Workflow ID
        workflow_state: Workflow state dictionary (used for storing logs)
        bedrock_client: Optional Bedrock client
        bedrock_config: Optional Bedrock configuration
        
    Returns:
        Configured SyntheticDataAgent instance
    """
    # Create AgentLogger with correct signature
    agent_logger = AgentLogger(
        workflow_id=workflow_id,
        agent_name="SyntheticDataAgent"
    )
    
    # Set up broadcast callback for WebSocket
    agent_logger.set_broadcast_callback(broadcast_agent_log_entry)
    
    # Store reference to workflow state so logs can be persisted
    agent_logger._workflow_state = workflow_state
    
    # If bedrock_client exists, set its agent_logger for prompt logging
    if bedrock_client:
        bedrock_client.agent_logger = agent_logger
    
    return SyntheticDataAgent(
        bedrock_client=bedrock_client,
        bedrock_config=bedrock_config,
        agent_logger=agent_logger
    )


def sanitize_for_json(data):
    """Sanitize data for JSON serialization by handling NaN, Infinity, and numpy types.
    
    Args:
        data: Data to sanitize (can be dict, list, or scalar)
    
    Returns:
        JSON-serializable data
    """
    import math
    import numpy as np
    
    if isinstance(data, dict):
        # Sanitize both keys and values
        return {sanitize_for_json(k): sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, tuple):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        # Convert numpy integer types to Python int
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32, np.float16)):
        # Convert numpy float types to Python float
        val = float(data)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(data, np.ndarray):
        # Convert numpy arrays to lists
        return sanitize_for_json(data.tolist())
    elif isinstance(data, np.bool_):
        # Convert numpy bool to Python bool
        return bool(data)
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif pd.isna(data):
        return None
    elif hasattr(data, 'item'):
        # Catch any other numpy scalar types
        try:
            val = data.item()
            return sanitize_for_json(val)
        except (ValueError, AttributeError):
            return str(data)
    else:
        return data

# Workflow persistence directory
WORKFLOW_STORAGE_DIR = Path("data/workflows")
WORKFLOW_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory workflow state cache
workflow_states = {}


def validate_agent_results(agent_id: str, results: dict) -> tuple[bool, str]:
    """Validate agent results structure before returning to frontend.
    
    Args:
        agent_id: Agent identifier (data_processor or synthetic_data)
        results: Agent results dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not results:
        return False, "Results dictionary is empty"
    
    # Common required fields
    required_fields = ['agent_type', 'status']
    
    # Agent-specific required fields
    if agent_id == 'data_processor':
        required_fields.extend(['columns', 'sample_data', 'total_rows', 'total_columns'])
    elif agent_id == 'synthetic_data':
        required_fields.extend(['columns', 'sample_data', 'total_records_generated', 'quality_metrics'])
    
    # Check for required fields
    missing_fields = [field for field in required_fields if field not in results]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate columns is a list
    if not isinstance(results.get('columns'), list):
        return False, "columns field must be a list"
    
    # Validate sample_data is a list
    if not isinstance(results.get('sample_data'), list):
        return False, "sample_data field must be a list"
    
    return True, ""


def _save_workflow_to_disk(workflow_id: str, workflow_data: dict) -> None:
    """Save workflow state to disk for persistence.
    
    Args:
        workflow_id: Workflow ID
        workflow_data: Workflow state dictionary
    """
    try:
        workflow_file = WORKFLOW_STORAGE_DIR / f"{workflow_id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_data, f, indent=2, default=str)
        logger.debug(f"Saved workflow {workflow_id} to disk")
    except Exception as e:
        logger.error(f"Failed to save workflow {workflow_id} to disk: {str(e)}")


def _load_workflow_from_disk(workflow_id: str) -> Optional[dict]:
    """Load workflow state from disk.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Workflow state dictionary or None if not found
    """
    try:
        workflow_file = WORKFLOW_STORAGE_DIR / f"{workflow_id}.json"
        if workflow_file.exists():
            with open(workflow_file, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Failed to load workflow {workflow_id} from disk: {str(e)}")
        return None


def _load_all_workflows_from_disk() -> None:
    """Load all workflows from disk into memory cache on startup."""
    try:
        for workflow_file in WORKFLOW_STORAGE_DIR.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    workflow_data = json.load(f)
                    workflow_id = workflow_data.get('workflow_id')
                    if workflow_id:
                        workflow_states[workflow_id] = workflow_data
                        logger.debug(f"Loaded workflow {workflow_id} from disk")
            except Exception as e:
                logger.error(f"Failed to load workflow from {workflow_file}: {str(e)}")
        logger.info(f"Loaded {len(workflow_states)} workflows from disk")
    except Exception as e:
        logger.error(f"Failed to load workflows from disk: {str(e)}")


def _get_workflow(workflow_id: str) -> Optional[dict]:
    """Get workflow from cache or load from disk if not in cache.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Workflow state dictionary or None if not found
    """
    # Check cache first
    if workflow_id in workflow_states:
        return workflow_states[workflow_id]
    
    # Try loading from disk
    workflow_data = _load_workflow_from_disk(workflow_id)
    if workflow_data:
        workflow_states[workflow_id] = workflow_data
        return workflow_data
    
    return None


# Load existing workflows on module import
_load_all_workflows_from_disk()


class WorkflowStartRequest(BaseModel):
    """Workflow start request."""
    config_id: str = Field(..., description="Configuration ID to use")
    num_records: int = Field(..., gt=0, description="Number of records to generate")
    project_id: Optional[str] = None
    workflow_name: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Workflow response model."""
    workflow_id: str
    status: str
    config_id: str
    num_records: int
    started_at: str
    updated_at: str
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    current_stage: Optional[str] = None
    message: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Detailed workflow status response."""
    workflow_id: str
    status: str
    config_id: str
    num_records: int
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None
    progress: float
    current_stage: Optional[str]
    stages_completed: list = Field(default_factory=list)
    error: Optional[str] = None
    cost_usd: float = 0.0
    analysis_results: Optional[dict] = None
    agent_logs: list = Field(default_factory=list)


class FieldStrategy(BaseModel):
    """Strategy configuration for a specific field."""
    field_name: str
    strategy: str  # 'bedrock_llm', 'sdv_preserve_distribution', 'sdv_gaussian_copula'
    custom_params: Optional[dict] = None


class StrategySelectionRequest(BaseModel):
    """Request to set synthesis strategies for workflow fields."""
    field_strategies: list[FieldStrategy]
    sdv_model: Optional[str] = 'gaussian_copula'  # SDV model type
    sdv_params: Optional[dict] = None  # SDV model parameters (epochs, batch_size, etc.)


class StrategySelectionResponse(BaseModel):
    """Response after setting synthesis strategies."""
    workflow_id: str
    status: str
    message: str
    strategies_applied: int


@router.post("/start", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def start_workflow(request: WorkflowStartRequest):
    """Start a new workflow execution.
    
    Validates Requirement 11.1: Enable workflow execution through web interface.
    
    Args:
        request: Workflow start request
    
    Returns:
        Workflow execution details
    """
    try:
        # Generate workflow ID
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize workflow state
        workflow_state = {
            'workflow_id': workflow_id,
            'status': 'running',
            'config_id': request.config_id,
            'num_records': request.num_records,
            'started_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'progress': 0.0,
            'current_stage': 'initializing',
            'stages_completed': [],
            'project_id': request.project_id,
            'workflow_name': request.workflow_name,
            'agent_logs': []  # Store agent activity logs
        }
        
        workflow_states[workflow_id] = workflow_state
        _save_workflow_to_disk(workflow_id, workflow_state)
        
        logger.info(f"Started workflow {workflow_id} with config {request.config_id}")
        
        # TODO: Actually start the workflow execution
        # This would integrate with the orchestration layer
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status='running',
            config_id=request.config_id,
            num_records=request.num_records,
            started_at=workflow_state['started_at'],
            updated_at=workflow_state['updated_at'],
            progress=0.0,
            current_stage='initializing',
            message='Workflow started successfully'
        )
        
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.post("/{workflow_id}/pause", response_model=WorkflowResponse)
async def pause_workflow(workflow_id: str):
    """Pause a running workflow.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Updated workflow status
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        if workflow['status'] != 'running':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot pause workflow in status: {workflow['status']}"
            )
        
        workflow['status'] = 'paused'
        workflow['updated_at'] = datetime.now().isoformat()
        _save_workflow_to_disk(workflow_id, workflow)
        
        logger.info(f"Paused workflow {workflow_id}")
        
        # TODO: Actually pause the workflow execution
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status='paused',
            config_id=workflow['config_id'],
            num_records=workflow['num_records'],
            started_at=workflow['started_at'],
            updated_at=workflow['updated_at'],
            progress=workflow['progress'],
            current_stage=workflow.get('current_stage'),
            message='Workflow paused successfully'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause workflow: {str(e)}"
        )


@router.post("/{workflow_id}/resume", response_model=WorkflowResponse)
async def resume_workflow(workflow_id: str):
    """Resume a paused workflow.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Updated workflow status
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        if workflow['status'] != 'paused':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resume workflow in status: {workflow['status']}"
            )
        
        workflow['status'] = 'running'
        workflow['updated_at'] = datetime.now().isoformat()
        _save_workflow_to_disk(workflow_id, workflow)
        
        logger.info(f"Resumed workflow {workflow_id}")
        
        # TODO: Actually resume the workflow execution
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status='running',
            config_id=workflow['config_id'],
            num_records=workflow['num_records'],
            started_at=workflow['started_at'],
            updated_at=workflow['updated_at'],
            progress=workflow['progress'],
            current_stage=workflow.get('current_stage'),
            message='Workflow resumed successfully'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume workflow: {str(e)}"
        )


@router.post("/{workflow_id}/abort", response_model=WorkflowResponse)
async def abort_workflow(workflow_id: str):
    """Abort a running or paused workflow.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Updated workflow status
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        if workflow['status'] in ['completed', 'failed', 'aborted']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot abort workflow in status: {workflow['status']}"
            )
        
        workflow['status'] = 'aborted'
        workflow['updated_at'] = datetime.now().isoformat()
        workflow['completed_at'] = datetime.now().isoformat()
        _save_workflow_to_disk(workflow_id, workflow)
        
        logger.info(f"Aborted workflow {workflow_id}")
        
        # TODO: Actually abort the workflow execution
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status='aborted',
            config_id=workflow['config_id'],
            num_records=workflow['num_records'],
            started_at=workflow['started_at'],
            updated_at=workflow['updated_at'],
            progress=workflow['progress'],
            current_stage=workflow.get('current_stage'),
            message='Workflow aborted successfully'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aborting workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to abort workflow: {str(e)}"
        )


@router.get("/{workflow_id}/analysis")
async def get_workflow_analysis(workflow_id: str):
    """Get detailed analysis results from Data Processor Agent.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Analysis results including field classifications
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        if 'analysis_results' not in workflow:
            return {
                "workflow_id": workflow_id,
                "status": workflow['status'],
                "message": "Analysis not yet available"
            }
        
        return {
            "workflow_id": workflow_id,
            "status": workflow['status'],
            "analysis": workflow['analysis_results']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow analysis: {str(e)}"
        )


@router.get("/{workflow_id}/agent/{agent_id}/results")
async def get_agent_results(workflow_id: str, agent_id: str, limit: int = 10):
    """Get agent execution results including sample data.
    
    Args:
        workflow_id: Workflow ID
        agent_id: Agent ID (e.g., 'data_processor', 'synthetic_data')
        limit: Maximum number of sample rows to return
    
    Returns:
        Agent results with sample data
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Get agent-specific results with backward compatibility
        if agent_id == 'data_processor':
            # Check both old and new data formats
            agent_results = workflow.get('data_processor_results') or workflow.get('analysis_results')
            if not agent_results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent results not found for {agent_id}"
                )
            
            # Handle both old and new data formats
            if 'field_details' in agent_results:  # New format
                sample_data = agent_results.get('sample_data', [])
                field_classifications = agent_results.get('field_details', [])
                total_rows = agent_results.get('total_rows', 0)
                total_columns = agent_results.get('total_columns', 0)
            else:  # Old format
                sample_data = agent_results.get('sample_data', [])
                field_classifications = agent_results.get('field_classifications', [])
                total_rows = agent_results.get('total_rows', 0)
                total_columns = agent_results.get('total_columns', 0)
            
            # Ensure columns field exists (backward compatibility)
            if 'columns' not in agent_results:
                # Extract columns from field_classifications or sample_data
                if field_classifications:
                    agent_results['columns'] = [f.get('name') or f.get('field_name') for f in field_classifications]
                elif sample_data and len(sample_data) > 0:
                    agent_results['columns'] = list(sample_data[0].keys())
                else:
                    agent_results['columns'] = []
            
            # If no sample data stored, try to load from original file
            if not sample_data and 'source_file' in workflow:
                try:
                    from pathlib import Path
                    import pandas as pd
                    source_file = Path(workflow['source_file'])
                    if source_file.exists():
                        df = pd.read_csv(source_file)
                        sample_data = df.head(limit).to_dict('records')
                        # Sanitize data for JSON serialization
                        sample_data = sanitize_for_json(sample_data)
                        logger.info(f"Loaded {len(sample_data)} sample rows from source file")
                except Exception as e:
                    logger.warning(f"Could not load sample data from source file: {str(e)}")
                    sample_data = []
            
            # Sanitize all data for JSON serialization
            field_classifications = sanitize_for_json(field_classifications)
            sample_data = sanitize_for_json(sample_data)
            
            # Return data processor results with sample data
            return {
                'agent_id': agent_id,
                'workflow_id': workflow_id,
                'results': {
                    'total_rows': total_rows,
                    'total_columns': total_columns,
                    'field_classifications': field_classifications,
                    'sample_data': sample_data[:limit]
                },
                'sample_data': sample_data[:limit],
                'metadata': {
                    'total_rows': total_rows,
                    'total_columns': total_columns,
                    'sensitive_fields': len([f for f in field_classifications if f.get('is_sensitive')]),
                    'generated_at': workflow.get('updated_at')
                }
            }
            
        elif agent_id == 'synthetic_data':
            agent_results = workflow.get('synthetic_data_results')
            if not agent_results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent results not found for {agent_id}. The synthetic data generation may not have completed yet."
                )
            
            # Sanitize data for JSON serialization
            agent_results = sanitize_for_json(agent_results)
            
            # Validate results structure
            is_valid, error_msg = validate_agent_results(agent_id, agent_results)
            if not is_valid:
                logger.error(f"Invalid agent results structure for {agent_id}: {error_msg}")
                logger.error(f"Results keys: {list(agent_results.keys())}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid results structure: {error_msg}"
                )
            
            # Return synthetic data results with sample data
            return {
                'agent_id': agent_id,
                'workflow_id': workflow_id,
                'results': agent_results,
                'sample_data': agent_results.get('sample_data', [])[:limit],
                'metadata': {
                    'total_generated': agent_results.get('total_records_generated', 0),
                    'generation_method': agent_results.get('generation_method', 'unknown'),
                    'privacy_level': agent_results.get('privacy_level', 'medium'),
                    'generated_at': workflow.get('updated_at')
                }
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown agent_id: {agent_id}. Supported agents: data_processor, synthetic_data"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent results: {str(e)}"
        )


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get detailed workflow status.
    
    Validates Requirement 11.3: Real-time workflow monitoring.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        Detailed workflow status
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=workflow['status'],
            config_id=workflow['config_id'],
            num_records=workflow['num_records'],
            started_at=workflow['started_at'],
            updated_at=workflow['updated_at'],
            completed_at=workflow.get('completed_at'),
            progress=workflow['progress'],
            current_stage=workflow.get('current_stage'),
            stages_completed=workflow.get('stages_completed', []),
            error=workflow.get('error'),
            cost_usd=workflow.get('estimated_cost_usd', workflow.get('cost_usd', 0.0)),
            analysis_results=workflow.get('analysis_results'),
            agent_logs=workflow.get('agent_logs', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get("/{workflow_id}/download")
async def download_synthetic_data(workflow_id: str):
    """Download the full synthetic dataset as CSV.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        CSV file with synthetic data
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check if synthetic data file exists
        synthetic_data_file = workflow.get('synthetic_data_file')
        if not synthetic_data_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Synthetic data not yet generated for this workflow"
            )
        
        file_path = Path(synthetic_data_file)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Synthetic data file not found: {synthetic_data_file}"
            )
        
        # Return file for download
        return FileResponse(
            path=str(file_path),
            media_type='text/csv',
            filename=f"{workflow_id}_synthetic_data.csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading synthetic data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download synthetic data: {str(e)}"
        )


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str):
    """Delete a workflow and its associated files.
    
    Args:
        workflow_id: Workflow ID to delete
    
    Returns:
        No content on success
    """
    try:
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Remove from memory cache
        if workflow_id in workflow_states:
            del workflow_states[workflow_id]
        
        # Delete workflow file from disk
        workflow_file = WORKFLOW_STORAGE_DIR / f"{workflow_id}.json"
        if workflow_file.exists():
            workflow_file.unlink()
            logger.info(f"Deleted workflow file: {workflow_file}")
        
        logger.info(f"Deleted workflow {workflow_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workflow: {str(e)}"
        )


@router.get("/", response_model=list[WorkflowStatusResponse])
async def list_workflows(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 50
):
    """List workflows with optional filtering.
    
    Args:
        status: Optional status filter
        project_id: Optional project filter
        limit: Maximum number of results
    
    Returns:
        List of workflows
    """
    try:
        workflows = list(workflow_states.values())
        
        # Apply filters
        if status:
            workflows = [w for w in workflows if w['status'] == status]
        if project_id:
            workflows = [w for w in workflows if w.get('project_id') == project_id]
        
        # Sort by started_at descending
        workflows.sort(key=lambda w: w['started_at'], reverse=True)
        
        # Limit results
        workflows = workflows[:limit]
        
        return [
            WorkflowStatusResponse(
                workflow_id=w['workflow_id'],
                status=w['status'],
                config_id=w['config_id'],
                num_records=w['num_records'],
                started_at=w['started_at'],
                updated_at=w['updated_at'],
                completed_at=w.get('completed_at'),
                progress=w['progress'],
                current_stage=w.get('current_stage'),
                stages_completed=w.get('stages_completed', []),
                error=w.get('error'),
                cost_usd=w.get('estimated_cost_usd', w.get('cost_usd', 0.0)),
                analysis_results=w.get('analysis_results')
            )
            for w in workflows
        ]
        
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


async def resume_csv_workflow_after_strategy_selection(workflow_id: str):
    """Resume CSV workflow after user has selected synthesis strategies.
    
    Args:
        workflow_id: Workflow ID to resume
    """
    try:
        logger.info(f"Resuming CSV workflow {workflow_id} after strategy selection")
        
        workflow = _get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        if workflow['status'] != 'awaiting_strategy_selection':
            logger.error(f"Cannot resume workflow {workflow_id} - status is {workflow['status']}")
            return
        
        # Get required data from workflow state
        csv_path = Path(workflow['source_file'])
        num_records = workflow['num_records']
        sensitivity_report_data = workflow.get('analysis_results')
        
        if not csv_path.exists():
            logger.error(f"Source file not found: {csv_path}")
            workflow['status'] = 'failed'
            workflow['error'] = f"Source file not found: {csv_path}"
            workflow['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow)
            return
        
        # Update status to running
        workflow['status'] = 'running'
        workflow['current_stage'] = 'synthetic_generation'
        workflow['progress'] = 50.0
        workflow['updated_at'] = datetime.now().isoformat()
        _save_workflow_to_disk(workflow_id, workflow)
        
        # Read CSV data
        df = pd.read_csv(csv_path)
        
        # Reconstruct sensitivity report from stored data
        from agents.data_processor.agent import SensitivityReport, FieldClassification
        
        field_classifications = {}
        for field_detail in sensitivity_report_data.get('field_details', []):
            field_classifications[field_detail['name']] = FieldClassification(
                field_name=field_detail['name'],
                is_sensitive=field_detail['is_sensitive'],
                sensitivity_type=field_detail.get('sensitivity_type'),
                confidence=field_detail['confidence'],
                recommended_strategy=field_detail.get('strategy', 'sdv'),
                reasoning=field_detail.get('reasoning', '')
            )
        
        sensitivity_report = SensitivityReport(
            total_fields=sensitivity_report_data['total_fields'],
            sensitive_fields=sensitivity_report_data['sensitive_fields'],
            classifications=field_classifications
        )
        
        # Continue with synthetic data generation (same as before)
        logger.info(f"Starting synthetic data generation for {num_records} records")
        
        try:
            # Initialize Bedrock client (optional - will use fallback if not configured)
            bedrock_client, bedrock_config, bedrock_enabled = initialize_bedrock_client()
            
            # Initialize Synthetic Data Agent with logger
            synthetic_agent = create_synthetic_agent_with_logger(
                workflow_id=workflow_id,
                workflow_state=workflow,
                bedrock_client=bedrock_client,
                bedrock_config=bedrock_config if bedrock_enabled else None
            )
            
            # Load strategy selections from workflow state if available
            field_strategies = workflow.get('strategy_selections', {})
            sdv_model = workflow.get('sdv_model', 'gaussian_copula')
            sdv_params = workflow.get('sdv_params', {})
            
            # Generate synthetic data using the agent
            synthetic_dataset = await asyncio.to_thread(
                synthetic_agent.generate_synthetic_data,
                data=df,
                sensitivity_report=sensitivity_report,
                num_rows=num_records,
                sdv_model=sdv_model,
                seed=42,
                field_strategies=field_strategies,
                **sdv_params
            )
            
            # Get sample data for display (ensure JSON serializable)
            synthetic_sample_df = synthetic_dataset.data.head(5)
            synthetic_sample = []
            for _, row in synthetic_sample_df.iterrows():
                sample_row = {}
                for col, val in row.items():
                    # Convert numpy types to Python types for JSON serialization
                    if hasattr(val, 'item'):  # numpy scalar
                        sample_row[col] = val.item()
                    elif pd.isna(val):  # handle NaN values
                        sample_row[col] = None
                    else:
                        sample_row[col] = val
                synthetic_sample.append(sample_row)
            
            # Extract generation metadata
            generation_metadata = synthetic_dataset.generation_metadata
            sensitive_fields = generation_metadata.get('sensitive_fields', [])
            non_sensitive_fields = generation_metadata.get('non_sensitive_fields', [])
            
            # Determine which fields used Bedrock vs SDV
            bedrock_fields = []
            sdv_fields = non_sensitive_fields.copy()
            
            if bedrock_enabled and bedrock_client and sensitive_fields:
                # Bedrock was used for sensitive text fields
                text_types = ['name', 'first_name', 'last_name', 'email', 'address', 
                             'street_address', 'city', 'company', 'job', 'description']
                for field in sensitive_fields:
                    classification = sensitivity_report.classifications.get(field)
                    if classification and classification.sensitivity_type in text_types:
                        bedrock_fields.append(field)
                    else:
                        sdv_fields.append(field)
            else:
                # All fields used SDV (Bedrock not available)
                sdv_fields.extend(sensitive_fields)
            
            workflow['current_stage'] = 'synthetic_generation_complete'
            workflow['progress'] = 80.0
            workflow['updated_at'] = datetime.now().isoformat()
            workflow['stages_completed'].append('synthetic_generation')
            
            # Store Synthetic Data results with detailed information (JSON-serializable)
            workflow['synthetic_data_results'] = {
                'agent_type': 'synthetic_data',
                'status': 'completed',
                'total_records_generated': len(synthetic_dataset.data),
                'columns': list(synthetic_dataset.data.columns),
                'sample_data': synthetic_sample,
                'generation_method': {
                    'sdv_model': 'GaussianCopula',
                    'bedrock_enabled': bedrock_enabled,
                    'bedrock_model': bedrock_config.model_id if bedrock_enabled and bedrock_config else None
                },
                'field_generation': {
                    'bedrock_fields': bedrock_fields,
                    'sdv_fields': sdv_fields,
                    'total_fields': len(df.columns)
                },
                'quality_metrics': {
                    'sdv_quality_score': float(synthetic_dataset.quality_metrics.sdv_quality_score),
                    'column_shapes_score': float(synthetic_dataset.quality_metrics.column_shapes_score),
                    'column_pair_trends_score': float(synthetic_dataset.quality_metrics.column_pair_trends_score),
                    'correlation_preservation': float(synthetic_dataset.quality_metrics.correlation_preservation)
                },
                'generation_metadata': {
                    'sdv_model': generation_metadata.get('sdv_model', 'gaussian_copula'),
                    'source_rows': int(generation_metadata.get('source_rows', len(df))),
                    'generated_rows': int(generation_metadata.get('generated_rows', len(synthetic_dataset.data))),
                    'sensitive_fields': list(generation_metadata.get('sensitive_fields', [])),
                    'non_sensitive_fields': list(generation_metadata.get('non_sensitive_fields', []))
                },
                'privacy_level': 'High' if bedrock_enabled else 'Medium'
            }
            _save_workflow_to_disk(workflow_id, workflow)
            
            logger.info(f"Synthetic data generation complete: {len(synthetic_dataset.data)} rows, "
                       f"Bedrock fields: {len(bedrock_fields)}, SDV fields: {len(sdv_fields)}")
            
        except Exception as e:
            import traceback
            logger.error(f"Error in synthetic data generation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            workflow['status'] = 'failed'
            workflow['error'] = f"Synthetic data generation failed: {str(e)}"
            workflow['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow)
            return
        
        # Complete workflow
        await asyncio.sleep(1)
        workflow['status'] = 'completed'
        workflow['current_stage'] = 'completed'
        workflow['progress'] = 100.0
        workflow['completed_at'] = datetime.now().isoformat()
        workflow['updated_at'] = datetime.now().isoformat()
        workflow['cost_usd'] = round(0.25 + (num_records * 0.001), 2)
        _save_workflow_to_disk(workflow_id, workflow)
        
        logger.info(f"CSV workflow {workflow_id} completed successfully after strategy selection")
        
    except Exception as e:
        logger.error(f"Error resuming CSV workflow {workflow_id}: {str(e)}")
        workflow = _get_workflow(workflow_id)
        if workflow:
            workflow['status'] = 'failed'
            workflow['error'] = str(e)
            workflow['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow)


async def execute_csv_workflow(workflow_id: str, csv_path: Path, num_records: int):
    """Execute CSV-based workflow in background."""
    try:
        logger.info(f"Starting CSV workflow execution for {workflow_id}")
        
        # Update workflow status
        if workflow_id in workflow_states:
            workflow_states[workflow_id]['current_stage'] = 'data_processing'
            workflow_states[workflow_id]['progress'] = 10.0
            workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
        
        # Step 1: Data Processor Agent - Analyze CSV
        logger.info(f"Running Data Processor Agent on {csv_path}")
        data_processor = DataProcessorAgent()
        
        # Read the CSV to get sample data
        df = pd.read_csv(csv_path)
        sample_rows = df.head(5).to_dict('records')  # Get first 5 rows as sample
        
        try:
            # Use async version directly since we're already in an async context
            sensitivity_report = await data_processor.process_async(csv_path)
            
            # Update workflow with results
            if workflow_id in workflow_states:
                workflow_states[workflow_id]['current_stage'] = 'analysis_complete'
                workflow_states[workflow_id]['progress'] = 30.0
                workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
                workflow_states[workflow_id]['stages_completed'].append('data_processing')
                
                # Extract field classifications from the report
                field_list = list(sensitivity_report.classifications.values())
                
                workflow_states[workflow_id]['analysis_results'] = {
                    'total_fields': len(field_list),
                    'sensitive_fields': sum(1 for f in field_list if f.is_sensitive),
                    'field_details': [
                        {
                            'name': f.field_name,
                            'is_sensitive': f.is_sensitive,
                            'sensitivity_type': f.sensitivity_type,
                            'confidence': f.confidence,
                            'strategy': f.recommended_strategy,
                            'reasoning': f.reasoning
                        }
                        for f in field_list
                    ],
                    'sample_data': sample_rows  # Include sample data for strategy selection
                }
                
                # Store Data Processor results with sample data
                workflow_states[workflow_id]['data_processor_results'] = {
                    'agent_type': 'data_processor',
                    'status': 'completed',
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'columns': list(df.columns),
                    'sample_data': sample_rows,
                    'field_classifications': workflow_states[workflow_id]['analysis_results']['field_details']
                }
                _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
            
            logger.info(f"Data processing complete: {len(sensitivity_report.classifications)} fields analyzed")
            
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            if workflow_id in workflow_states:
                workflow_states[workflow_id]['status'] = 'failed'
                workflow_states[workflow_id]['error'] = f"Data processing failed: {str(e)}"
                workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
                _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
            return
        
        # Step 2: Pause for Strategy Selection
        logger.info(f"Pausing workflow for strategy selection")
        
        if workflow_id in workflow_states:
            workflow_states[workflow_id]['status'] = 'awaiting_strategy_selection'
            workflow_states[workflow_id]['current_stage'] = 'strategy_selection'
            workflow_states[workflow_id]['progress'] = 40.0
            workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
            workflow_states[workflow_id]['stages_completed'].append('analysis_complete')
            _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
        
        logger.info(f"Workflow {workflow_id} paused for strategy selection")
        return  # Exit here - workflow will resume when user submits strategy selections
        
        # Step 3: Synthetic Data Generation (will be executed after strategy selection)
        logger.info(f"Starting synthetic data generation for {num_records} records")
        
        if workflow_id in workflow_states:
            workflow_states[workflow_id]['current_stage'] = 'synthetic_generation'
            workflow_states[workflow_id]['progress'] = 50.0
            workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
        
        try:
            # Initialize Bedrock client (optional - will use fallback if not configured)
            bedrock_client, bedrock_config, bedrock_enabled = initialize_bedrock_client()
            
            # Initialize Synthetic Data Agent with logger
            synthetic_agent = create_synthetic_agent_with_logger(
                workflow_id=workflow_id,
                workflow_state=workflow,
                bedrock_client=bedrock_client,
                bedrock_config=bedrock_config if bedrock_enabled else None
            )
            
            # Generate synthetic data using the agent
            synthetic_dataset = await asyncio.to_thread(
                synthetic_agent.generate_synthetic_data,
                data=df,
                sensitivity_report=sensitivity_report,
                num_rows=num_records,
                sdv_model='gaussian_copula',
                seed=42
            )
            
            # Get sample data for display (ensure JSON serializable)
            synthetic_sample_df = synthetic_dataset.data.head(5)
            synthetic_sample = []
            for _, row in synthetic_sample_df.iterrows():
                sample_row = {}
                for col, val in row.items():
                    # Convert numpy types to Python types for JSON serialization
                    if hasattr(val, 'item'):  # numpy scalar
                        sample_row[col] = val.item()
                    elif pd.isna(val):  # handle NaN values
                        sample_row[col] = None
                    else:
                        sample_row[col] = val
                synthetic_sample.append(sample_row)
            
            # Extract generation metadata
            generation_metadata = synthetic_dataset.generation_metadata
            sensitive_fields = generation_metadata.get('sensitive_fields', [])
            non_sensitive_fields = generation_metadata.get('non_sensitive_fields', [])
            
            # Determine which fields used Bedrock vs SDV
            bedrock_fields = []
            sdv_fields = non_sensitive_fields.copy()
            
            if bedrock_enabled and bedrock_client and sensitive_fields:
                # Bedrock was used for sensitive text fields
                text_types = ['name', 'first_name', 'last_name', 'email', 'address', 
                             'street_address', 'city', 'company', 'job', 'description']
                for field in sensitive_fields:
                    classification = sensitivity_report.classifications.get(field)
                    if classification and classification.sensitivity_type in text_types:
                        bedrock_fields.append(field)
                    else:
                        sdv_fields.append(field)
            else:
                # All fields used SDV (Bedrock not available)
                sdv_fields.extend(sensitive_fields)
            
            if workflow_id in workflow_states:
                workflow_states[workflow_id]['current_stage'] = 'synthetic_generation_complete'
                workflow_states[workflow_id]['progress'] = 80.0
                workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
                workflow_states[workflow_id]['stages_completed'].append('synthetic_generation')
                
                # Store Synthetic Data results with detailed information (JSON-serializable)
                workflow_states[workflow_id]['synthetic_data_results'] = {
                    'agent_type': 'synthetic_data',
                    'status': 'completed',
                    'total_records_generated': len(synthetic_dataset.data),
                    'columns': list(synthetic_dataset.data.columns),
                    'sample_data': synthetic_sample,
                    'generation_method': {
                        'sdv_model': 'GaussianCopula',
                        'bedrock_enabled': bedrock_enabled,
                        'bedrock_model': bedrock_config.model_id if bedrock_enabled and bedrock_config else None
                    },
                    'field_generation': {
                        'bedrock_fields': bedrock_fields,
                        'sdv_fields': sdv_fields,
                        'total_fields': len(df.columns)
                    },
                    'quality_metrics': {
                        'sdv_quality_score': float(synthetic_dataset.quality_metrics.sdv_quality_score),
                        'column_shapes_score': float(synthetic_dataset.quality_metrics.column_shapes_score),
                        'column_pair_trends_score': float(synthetic_dataset.quality_metrics.column_pair_trends_score),
                        'correlation_preservation': float(synthetic_dataset.quality_metrics.correlation_preservation)
                    },
                    'generation_metadata': {
                        'sdv_model': generation_metadata.get('sdv_model', 'gaussian_copula'),
                        'source_rows': int(generation_metadata.get('source_rows', len(df))),
                        'generated_rows': int(generation_metadata.get('generated_rows', len(synthetic_dataset.data))),
                        'sensitive_fields': list(generation_metadata.get('sensitive_fields', [])),
                        'non_sensitive_fields': list(generation_metadata.get('non_sensitive_fields', []))
                    },
                    'privacy_level': 'High' if bedrock_enabled else 'Medium'
                }
                _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
            
            logger.info(f"Synthetic data generation complete: {len(synthetic_dataset.data)} rows, "
                       f"Bedrock fields: {len(bedrock_fields)}, SDV fields: {len(sdv_fields)}")
            
        except Exception as e:
            import traceback
            logger.error(f"Error in synthetic data generation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if workflow_id in workflow_states:
                workflow_states[workflow_id]['status'] = 'failed'
                workflow_states[workflow_id]['error'] = f"Synthetic data generation failed: {str(e)}"
                workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
                _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
            return
        
        # Step 4: Complete
        await asyncio.sleep(1)
        if workflow_id in workflow_states:
            workflow_states[workflow_id]['status'] = 'completed'
            workflow_states[workflow_id]['current_stage'] = 'completed'
            workflow_states[workflow_id]['progress'] = 100.0
            workflow_states[workflow_id]['completed_at'] = datetime.now().isoformat()
            workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
            workflow_states[workflow_id]['cost_usd'] = round(0.25 + (num_records * 0.001), 2)
            _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
        
        logger.info(f"CSV workflow {workflow_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error executing CSV workflow {workflow_id}: {str(e)}")
        if workflow_id in workflow_states:
            workflow_states[workflow_id]['status'] = 'failed'
            workflow_states[workflow_id]['error'] = str(e)
            workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])


@router.post("/upload-csv", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv_and_start_workflow(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    num_records: int = 100,
    workflow_name: Optional[str] = None
):
    """Upload a CSV file and start a synthetic data generation workflow.
    
    This endpoint:
    1. Accepts a CSV file upload
    2. Analyzes the schema and data patterns
    3. Creates a configuration based on the CSV
    4. Starts a workflow to generate synthetic data matching the CSV structure
    
    Args:
        file: CSV file to upload
        num_records: Number of synthetic records to generate (default: 100)
        workflow_name: Optional name for the workflow
    
    Returns:
        Workflow execution details
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are supported"
            )
        
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate CSV has data
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty"
            )
        
        logger.info(f"Uploaded CSV: {file.filename}, Shape: {df.shape}")
        
        # Save uploaded file to data directory
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{file.filename}"
        saved_path = upload_dir / saved_filename
        
        with open(saved_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"Saved uploaded file to: {saved_path}")
        
        # Analyze CSV schema
        schema_info = {
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'row_count': len(df),
            'sample_data': df.head(3).to_dict('records')
        }
        
        # Generate workflow ID
        workflow_id = f"wf_csv_{timestamp}"
        
        # Create config ID based on filename
        config_id = f"csv_{file.filename.replace('.csv', '')}_{timestamp}"
        
        # Initialize workflow state
        workflow_state = {
            'workflow_id': workflow_id,
            'status': 'running',
            'config_id': config_id,
            'num_records': num_records,
            'started_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'progress': 0.0,
            'current_stage': 'analyzing_csv',
            'stages_completed': [],
            'workflow_name': workflow_name or f"CSV Upload: {file.filename}",
            'source_file': str(saved_path),
            'schema_info': schema_info,
            'agent_logs': []  # Store agent activity logs
        }
        
        workflow_states[workflow_id] = workflow_state
        _save_workflow_to_disk(workflow_id, workflow_state)
        
        logger.info(f"Started CSV-based workflow {workflow_id}")
        
        # Start background workflow execution
        background_tasks.add_task(execute_csv_workflow, workflow_id, saved_path, num_records)
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status='running',
            config_id=config_id,
            num_records=num_records,
            started_at=workflow_state['started_at'],
            updated_at=workflow_state['updated_at'],
            progress=0.0,
            current_stage='analyzing_csv',
            message=f'CSV uploaded successfully. Analyzing {len(df)} rows with {len(df.columns)} columns.'
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or invalid"
        )
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing CSV upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV upload: {str(e)}"
        )


@router.post("/{workflow_id}/strategy-selection", response_model=StrategySelectionResponse)
async def set_strategy_selection(
    workflow_id: str,
    request: StrategySelectionRequest
):
    """Set synthesis strategies for workflow fields and resume execution.
    
    Args:
        workflow_id: Workflow ID
        request: Strategy selection request with field strategies
    
    Returns:
        StrategySelectionResponse with status
    """
    try:
        logger.info(f"Setting strategy selection for workflow {workflow_id}")
        
        # Get workflow
        workflow = _get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Validate workflow is in correct state
        if workflow['status'] != 'awaiting_strategy_selection':
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot set strategies for workflow in status: {workflow['status']}"
            )
        
        # Validate all fields have strategies
        analysis_results = workflow.get('analysis_results')
        if not analysis_results or not analysis_results.get('field_details'):
            raise HTTPException(status_code=400, detail="No field analysis found")
        
        field_names = {field['name'] for field in analysis_results['field_details']}
        strategy_field_names = {strategy.field_name for strategy in request.field_strategies}
        
        missing_fields = field_names - strategy_field_names
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing strategies for fields: {', '.join(missing_fields)}"
            )
        
        # Store strategy selections in workflow
        strategy_dict = {
            strategy.field_name: {
                'strategy': strategy.strategy,
                'custom_params': strategy.custom_params or {}
            }
            for strategy in request.field_strategies
        }
        
        # Calculate estimated cost for Bedrock fields
        bedrock_fields = [
            field_name for field_name, strategy_info in strategy_dict.items()
            if strategy_info['strategy'] in ['bedrock_llm', 'bedrock_examples']
        ]
        
        estimated_cost = 0.0
        if bedrock_fields:
            # Get field examples for cost calculation
            field_examples = {}
            for field_name in bedrock_fields:
                strategy_info = strategy_dict[field_name]
                if strategy_info['strategy'] == 'bedrock_examples':
                    examples = strategy_info.get('custom_params', {}).get('examples', '')
                    if examples:
                        field_examples[field_name] = examples.split('\n') if isinstance(examples, str) else examples
            
            # Call cost estimation endpoint
            try:
                from web.backend.routers.cost_estimation import estimate_tokens_per_field, BEDROCK_PRICING
                
                model_id = "anthropic.claude-3-haiku-20240307-v1:0"  # Default model
                pricing = BEDROCK_PRICING[model_id]
                
                total_input_tokens = 0
                total_output_tokens = 0
                
                for field in bedrock_fields:
                    has_examples = field in field_examples and len(field_examples[field]) > 0
                    input_tokens, output_tokens = estimate_tokens_per_field(field, has_examples)
                    total_input_tokens += input_tokens * workflow['num_records']
                    total_output_tokens += output_tokens * workflow['num_records']
                
                input_cost = (total_input_tokens / 1000) * pricing["input_per_1k"]
                output_cost = (total_output_tokens / 1000) * pricing["output_per_1k"]
                estimated_cost = input_cost + output_cost
                
                logger.info(f"Estimated Bedrock cost for workflow {workflow_id}: ${estimated_cost:.4f}")
            except Exception as e:
                logger.warning(f"Failed to calculate cost estimate: {e}")
        
        workflow['strategy_selections'] = strategy_dict
        workflow['sdv_model'] = request.sdv_model or 'gaussian_copula'
        workflow['sdv_params'] = request.sdv_params or {}
        workflow['estimated_cost_usd'] = estimated_cost
        workflow['status'] = 'running'
        workflow['updated_at'] = datetime.now().isoformat()
        _save_workflow_to_disk(workflow_id, workflow)
        
        logger.info(f"Strategies set for {len(request.field_strategies)} fields in workflow {workflow_id}")
        
        # Resume workflow execution in background
        # Get the CSV path and num_records from workflow
        csv_path = Path(workflow['source_file'])
        num_records = workflow['num_records']
        
        # Continue from where we left off - synthetic data generation
        asyncio.create_task(resume_csv_workflow_after_strategy_selection(workflow_id, csv_path, num_records))
        
        return StrategySelectionResponse(
            workflow_id=workflow_id,
            status="resuming",
            message="Strategies applied successfully. Workflow is resuming.",
            strategies_applied=len(request.field_strategies)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting strategy selection for workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def resume_csv_workflow_after_strategy_selection(workflow_id: str, csv_path: Path, num_records: int):
    """Resume CSV workflow execution after strategy selection."""
    try:
        logger.info(f"Resuming CSV workflow {workflow_id} after strategy selection")
        
        # Get workflow to access strategy selections
        workflow = _get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        strategy_selections = workflow.get('strategy_selections', {})
        
        # Step 3: Synthetic Data Generation
        logger.info(f"Starting synthetic data generation for {num_records} records")
        
        if workflow_id in workflow_states:
            workflow_states[workflow_id]['current_stage'] = 'synthetic_generation'
            workflow_states[workflow_id]['progress'] = 50.0
            workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
        
        try:
            # Initialize Bedrock client (optional - will use fallback if not configured)
            bedrock_client, bedrock_config, bedrock_enabled = initialize_bedrock_client()
            
            # Initialize Synthetic Data Agent with logger
            synthetic_agent = create_synthetic_agent_with_logger(
                workflow_id=workflow_id,
                workflow_state=workflow,
                bedrock_client=bedrock_client,
                bedrock_config=bedrock_config if bedrock_enabled else None
            )
            
            # Read the CSV
            df = pd.read_csv(csv_path)
            
            # Apply strategy selections to field configurations
            # This would be used by the synthetic agent to determine which strategy to use for each field
            logger.info(f"Using strategy selections: {strategy_selections}")
            
            # Reconstruct sensitivity report from stored data
            sensitivity_report_data = workflow.get('analysis_results')
            if not sensitivity_report_data:
                raise ValueError("No sensitivity analysis results found in workflow")
            
            # Reconstruct SensitivityReport object
            from shared.models.sensitivity import SensitivityReport, FieldClassification
            classifications = {}
            for field_detail in sensitivity_report_data.get('field_details', []):
                classifications[field_detail['name']] = FieldClassification(
                    field_name=field_detail['name'],
                    is_sensitive=field_detail['is_sensitive'],
                    sensitivity_type=field_detail.get('sensitivity_type', 'unknown'),
                    confidence=field_detail['confidence'],
                    recommended_strategy=field_detail.get('strategy', 'sdv'),
                    reasoning=field_detail.get('reasoning', '')
                )
            
            sensitivity_report = SensitivityReport(
                classifications=classifications,
                data_profile={},  # Empty profile for reconstructed report
                timestamp=datetime.now(),
                total_fields=sensitivity_report_data['total_fields'],
                sensitive_fields=sensitivity_report_data['sensitive_fields'],
                confidence_distribution={}  # Empty distribution for reconstructed report
            )
            
            # Load strategy selections from workflow state if available
            field_strategies = workflow.get('strategy_selections', {})
            sdv_model = workflow.get('sdv_model', 'gaussian_copula')
            sdv_params = workflow.get('sdv_params', {})
            
            # Generate synthetic data using the synchronous method with asyncio.to_thread
            synthetic_dataset = await asyncio.to_thread(
                synthetic_agent.generate_synthetic_data,
                data=df,
                sensitivity_report=sensitivity_report,
                num_rows=num_records,
                sdv_model=sdv_model,
                seed=42,
                field_strategies=field_strategies,
                **sdv_params
            )
            
            # Get sample data for display (ensure JSON serializable)
            synthetic_sample_df = synthetic_dataset.data.head(5)
            synthetic_sample = []
            for _, row in synthetic_sample_df.iterrows():
                sample_row = {}
                for col, val in row.items():
                    # Convert numpy types to Python types for JSON serialization
                    if hasattr(val, 'item'):  # numpy scalar
                        sample_row[col] = val.item()
                    elif pd.isna(val):  # handle NaN values
                        sample_row[col] = None
                    else:
                        sample_row[col] = val
                synthetic_sample.append(sample_row)
            
            # Update workflow with results
            if workflow_id in workflow_states:
                workflow_states[workflow_id]['current_stage'] = 'synthetic_generation_complete'
                workflow_states[workflow_id]['progress'] = 80.0
                workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
                workflow_states[workflow_id]['stages_completed'].append('synthetic_generation')
                
                # Store synthetic data results
                workflow_states[workflow_id]['synthetic_data_results'] = {
                    'agent_type': 'synthetic_data',
                    'status': 'completed',
                    'columns': list(synthetic_dataset.data.columns),  # CRITICAL: Must include columns
                    'total_records_generated': len(synthetic_dataset.data),
                    'sample_data': synthetic_sample,
                    'quality_metrics': sanitize_for_json(synthetic_dataset.quality_metrics.__dict__),
                    'generation_metadata': sanitize_for_json(synthetic_dataset.generation_metadata)
                }
                
                # Save synthetic data to file
                output_dir = Path("data/synthetic")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"{workflow_id}_synthetic.csv"
                
                # Log column order before export
                logger.info(f"Exporting CSV with column order: {list(synthetic_dataset.data.columns)}")
                
                synthetic_dataset.data.to_csv(output_file, index=False)
                workflow_states[workflow_id]['synthetic_data_file'] = str(output_file)
                
                # Verify column order after export by reading back
                df_read = pd.read_csv(output_file)
                if list(df_read.columns) != list(synthetic_dataset.data.columns):
                    logger.warning(
                        f"Column order mismatch after CSV export. "
                        f"Expected: {list(synthetic_dataset.data.columns)}, "
                        f"Got: {list(df_read.columns)}"
                    )
                else:
                    logger.info("CSV export column order verified successfully")
                
                _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
            
            logger.info(f"Synthetic data generation complete: {len(synthetic_dataset.data)} records")
            
        except Exception as e:
            import traceback
            logger.error(f"Error in synthetic data generation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if workflow_id in workflow_states:
                workflow_states[workflow_id]['status'] = 'failed'
                workflow_states[workflow_id]['error'] = f"Synthetic data generation failed: {str(e)}"
                workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
                _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
            return
        
        # Mark workflow as complete
        if workflow_id in workflow_states:
            workflow_states[workflow_id]['status'] = 'completed'
            workflow_states[workflow_id]['current_stage'] = 'completed'
            workflow_states[workflow_id]['progress'] = 100.0
            workflow_states[workflow_id]['completed_at'] = datetime.now().isoformat()
            workflow_states[workflow_id]['updated_at'] = datetime.now().isoformat()
            workflow_states[workflow_id]['stages_completed'].append('completed')
            _save_workflow_to_disk(workflow_id, workflow_states[workflow_id])
        
        logger.info(f"CSV workflow {workflow_id} completed successfully after strategy selection")
        
    except Exception as e:
        logger.error(f"Error resuming CSV workflow {workflow_id}: {str(e)}")
        workflow = _get_workflow(workflow_id)
        if workflow:
            workflow['status'] = 'failed'
            workflow['error'] = str(e)
            workflow['updated_at'] = datetime.now().isoformat()
            _save_workflow_to_disk(workflow_id, workflow)
