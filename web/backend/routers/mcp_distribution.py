"""API endpoints for MCP-based distribution."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import pandas as pd

from agents.distribution.mcp_agent import MCPDistributionAgent, MCPDistributionResult
from agents.distribution.strands_mcp_agent import StrandsMCPDistributionAgent, DistributionResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp-distribution", tags=["mcp-distribution"])


# Helper function to load dataset from workflow
def load_dataset_from_workflow(workflow_id: str) -> pd.DataFrame:
    """Load synthetic dataset from workflow JSON file."""
    import json
    
    workflow_path = Path(f"data/workflows/{workflow_id}.json")
    
    if not workflow_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {workflow_id}"
        )
    
    # Read workflow data
    with open(workflow_path, 'r') as f:
        workflow_data = json.load(f)
    
    # Check if synthetic data exists
    if 'synthetic_data_results' not in workflow_data or 'sample_data' not in workflow_data['synthetic_data_results']:
        raise HTTPException(
            status_code=404,
            detail=f"No synthetic data found for workflow {workflow_id}"
        )
    
    # Convert synthetic data to DataFrame
    synthetic_data = workflow_data['synthetic_data_results']['sample_data']
    return pd.DataFrame(synthetic_data)


# Request/Response Models
class DistributionRequest(BaseModel):
    """Request to distribute data using MCP."""
    workflow_id: str = Field(..., description="Workflow ID containing the dataset")
    instructions: str = Field(..., description="Natural language distribution instructions")
    mcp_config_path: str = Field(default="data/mcp_config.json", description="Path to MCP config")


class DistributionPlanRequest(BaseModel):
    """Request to create a distribution plan."""
    workflow_id: str = Field(..., description="Workflow ID containing the dataset")
    instructions: str = Field(..., description="Natural language distribution instructions")
    mcp_config_path: str = Field(default="data/mcp_config.json", description="Path to MCP config")


class DistributionStatus(BaseModel):
    """Status of a distribution operation."""
    status: str  # 'pending', 'running', 'completed', 'failed'
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    progress_percentage: float = 0.0
    current_step: Optional[str] = None
    error: Optional[str] = None
    agent_stream: list[str] = []  # Real-time agent responses


class DistributionResponse(BaseModel):
    """Response from distribution operation."""
    distribution_id: str
    status: str
    message: str


class ToolsResponse(BaseModel):
    """Response with available MCP tools."""
    servers: Dict[str, Any]
    tools_summary: str


# In-memory storage for distribution status
# In production, use Redis or database
distribution_status: Dict[str, DistributionStatus] = {}


@router.post("/distribute", response_model=DistributionResponse)
async def distribute_data(
    request: DistributionRequest,
    background_tasks: BackgroundTasks
):
    """
    Distribute data using MCP tools based on natural language instructions.
    
    This endpoint:
    1. Loads the synthetic dataset from the workflow
    2. Initializes the MCP distribution agent
    3. Starts distribution in the background
    4. Returns immediately with a distribution ID
    
    Use the /status/{distribution_id} endpoint to check progress.
    """
    try:
        # Load dataset from workflow
        dataset = load_dataset_from_workflow(request.workflow_id)
        
        # Generate distribution ID
        import uuid
        distribution_id = str(uuid.uuid4())
        
        # Initialize status
        distribution_status[distribution_id] = DistributionStatus(
            status='pending',
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            progress_percentage=0.0
        )
        
        # Start distribution in background
        background_tasks.add_task(
            _run_distribution,
            distribution_id=distribution_id,
            dataset=dataset,
            instructions=request.instructions,
            mcp_config_path=request.mcp_config_path
        )
        
        return DistributionResponse(
            distribution_id=distribution_id,
            status='pending',
            message="Distribution started. Use /status endpoint to check progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to start distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{distribution_id}", response_model=DistributionStatus)
async def get_distribution_status(distribution_id: str):
    """
    Get the status of a distribution operation.
    
    Returns real-time progress information including:
    - Current status (pending, running, completed, failed)
    - Records processed, succeeded, and failed
    - Progress percentage
    - Current step being executed
    - Any errors encountered
    """
    if distribution_id not in distribution_status:
        raise HTTPException(
            status_code=404,
            detail=f"Distribution {distribution_id} not found"
        )
    
    return distribution_status[distribution_id]


@router.post("/plan", response_model=Dict[str, Any])
async def create_distribution_plan(request: DistributionPlanRequest):
    """
    Create a distribution plan without executing it.
    
    This endpoint analyzes the instructions and available MCP tools
    to create an execution plan. Useful for previewing what will happen
    before actually running the distribution.
    
    Returns:
    - Dataset information (columns, row count, sample data)
    - Available MCP tools
    - Planned execution steps
    """
    try:
        # Load dataset from workflow
        dataset = load_dataset_from_workflow(request.workflow_id)
        
        # Initialize agent
        agent = MCPDistributionAgent(mcp_config_path=request.mcp_config_path)
        
        # Create plan
        plan = await agent.plan_distribution(
            dataset=dataset,
            instructions=request.instructions
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Failed to create distribution plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools", response_model=ToolsResponse)
async def get_available_tools(mcp_config_path: str = "data/mcp_config.json"):
    """
    Get available MCP tools from configured servers.
    
    Returns information about:
    - Configured MCP servers
    - Available tools for each server
    - Tool capabilities and parameters
    
    This helps users understand what distribution operations are possible.
    """
    try:
        # Initialize agent
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_path)
        
        # Discover tools
        tools = await agent.discover_tools()
        
        # Get summary
        summary = agent.get_tools_summary()
        
        return ToolsResponse(
            servers=tools,
            tools_summary=summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get available tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dataset/{workflow_id}", response_model=Dict[str, Any])
async def get_dataset_preview(workflow_id: str, limit: int = 5):
    """
    Get a preview of the synthetic dataset for a workflow.
    
    Returns:
    - Column names
    - Total row count
    - First N rows of data
    """
    try:
        import json
        
        # Load workflow JSON file
        workflow_path = Path(f"data/workflows/{workflow_id}.json")
        
        if not workflow_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}"
            )
        
        # Read workflow data
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        
        # Check if synthetic data exists
        if 'synthetic_data_results' not in workflow_data or 'sample_data' not in workflow_data['synthetic_data_results']:
            raise HTTPException(
                status_code=404,
                detail=f"No synthetic data found for workflow {workflow_id}"
            )
        
        # Get synthetic data
        synthetic_results = workflow_data['synthetic_data_results']
        all_data = synthetic_results.get('sample_data', [])
        columns = synthetic_results.get('columns', [])
        total_records = synthetic_results.get('total_records_generated', len(all_data))
        
        # Get preview (first N records)
        preview_data = all_data[:limit]
        
        return {
            "columns": columns,
            "row_count": total_records,
            "preview": preview_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-status", response_model=Dict[str, Any])
async def get_agent_status(mcp_config_path: str = "data/mcp_config.json"):
    """
    Get the current status of the MCP distribution agent.
    
    Returns:
    - Whether MCP config is loaded
    - Available MCP servers
    - Available tools
    - Configuration path
    """
    try:
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_path)
        return agent.get_status()
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/distribute-strands", response_model=DistributionResponse)
async def distribute_data_with_strands(
    request: DistributionRequest,
    background_tasks: BackgroundTasks
):
    """
    Distribute data using Strands-based MCP agent (PRODUCTION VERSION).
    
    This endpoint uses the real Strands framework with actual MCP servers
    to distribute data based on natural language instructions.
    
    Features:
    - Real Strands Agent with MCP tool integration
    - Actual MCP server connections
    - Intelligent natural language processing
    - Real-time tool execution
    
    Use the /status/{distribution_id} endpoint to check progress.
    """
    logger.info(f"=== ENDPOINT /distribute-strands CALLED ===")
    logger.info(f"Workflow ID: {request.workflow_id}")
    logger.info(f"Instructions: {request.instructions}")
    
    try:
        # Load dataset from workflow
        dataset = load_dataset_from_workflow(request.workflow_id)
        
        # Generate distribution ID
        import uuid
        distribution_id = str(uuid.uuid4())
        
        # Initialize status
        distribution_status[distribution_id] = DistributionStatus(
            status='pending',
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            progress_percentage=0.0
        )
        
        # Start distribution in background
        background_tasks.add_task(
            _run_strands_distribution,
            distribution_id=distribution_id,
            dataset=dataset,
            instructions=request.instructions,
            mcp_config_path=request.mcp_config_path
        )
        
        return DistributionResponse(
            distribution_id=distribution_id,
            status='pending',
            message="Strands-based distribution started. Use /status endpoint to check progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to start Strands distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_distribution(
    distribution_id: str,
    dataset: pd.DataFrame,
    instructions: str,
    mcp_config_path: str
):
    """
    Background task to run distribution.
    
    This function:
    1. Updates status to 'running'
    2. Executes distribution with progress callbacks
    3. Updates status with results
    4. Handles errors
    """
    try:
        # Update status to running
        distribution_status[distribution_id].status = 'running'
        
        # Initialize agent
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_path)
        
        # Define progress callback
        async def progress_callback(progress: Dict[str, Any]):
            """Update distribution status with progress."""
            status = distribution_status[distribution_id]
            status.records_processed = progress.get('records_processed', 0)
            status.records_succeeded = progress.get('records_succeeded', 0)
            status.records_failed = progress.get('records_failed', 0)
            status.current_step = progress.get('action', '')
            
            # Calculate progress percentage
            total = progress.get('total_records', 1)
            processed = progress.get('records_processed', 0)
            status.progress_percentage = (processed / total) * 100 if total > 0 else 0
        
        # Run distribution
        result = await agent.distribute(
            dataset=dataset,
            instructions=instructions,
            progress_callback=progress_callback
        )
        
        # Update final status
        status = distribution_status[distribution_id]
        status.status = 'completed' if result.status == 'success' else 'failed'
        status.records_processed = result.records_processed
        status.records_succeeded = result.records_succeeded
        status.records_failed = result.records_failed
        status.progress_percentage = 100.0
        
        if result.status == 'failed':
            status.error = result.agent_response
        
        logger.info(
            f"Distribution {distribution_id} completed: "
            f"{result.records_succeeded}/{result.records_processed} succeeded"
        )
        
    except Exception as e:
        logger.error(f"Distribution {distribution_id} failed: {str(e)}")
        
        # Update status with error
        status = distribution_status[distribution_id]
        status.status = 'failed'
        status.error = str(e)


async def _run_strands_distribution(
    distribution_id: str,
    dataset: pd.DataFrame,
    instructions: str,
    mcp_config_path: str
):
    """
    Background task to run Strands-based distribution.
    
    This uses the real Strands framework with actual MCP servers.
    """
    logger.info(f"=== _run_strands_distribution STARTED for {distribution_id} ===")
    logger.info(f"Dataset shape: {dataset.shape}")
    logger.info(f"Instructions: {instructions}")
    
    try:
        # Update status to running
        distribution_status[distribution_id].status = 'running'
        distribution_status[distribution_id].current_step = 'Initializing Strands agent...'
        
        logger.info("Creating StrandsMCPDistributionAgent...")
        # Initialize Strands agent
        agent = StrandsMCPDistributionAgent(mcp_config_path=mcp_config_path)
        logger.info("Agent created successfully")
        
        distribution_status[distribution_id].current_step = 'Connecting to MCP servers...'
        
        # Define progress callback
        async def progress_callback(progress: Dict[str, Any]):
            """Update distribution status with progress."""
            status = distribution_status[distribution_id]
            status.records_processed = progress.get('records_processed', 0)
            status.records_succeeded = progress.get('records_succeeded', 0)
            status.records_failed = progress.get('records_failed', 0)
            status.current_step = progress.get('action', 'Processing...')
            
            # Calculate progress percentage
            total = progress.get('total_records', 1)
            processed = progress.get('records_processed', 0)
            status.progress_percentage = (processed / total) * 100 if total > 0 else 0
        
        distribution_status[distribution_id].current_step = 'Distributing data...'
        
        # Define stream callback to capture agent responses
        async def stream_callback(chunk: str):
            """Capture streaming agent responses."""
            logger.info(f"Stream callback received {len(chunk)} chars: {chunk[:100]}...")
            status = distribution_status[distribution_id]
            status.agent_stream.append(chunk)
            logger.info(f"Agent stream now has {len(status.agent_stream)} chunks")
        
        # Run distribution with Strands agent
        logger.info("About to call agent.distribute()...")
        result = await agent.distribute(
            dataset=dataset,
            instructions=instructions,
            progress_callback=progress_callback,
            stream_callback=stream_callback
        )
        logger.info(f"agent.distribute() returned: {result.status}")
        
        # Update final status
        status = distribution_status[distribution_id]
        status.status = 'completed' if result.status == 'success' else 'failed'
        status.records_processed = result.records_processed
        status.records_succeeded = result.records_succeeded
        status.records_failed = result.records_failed
        status.progress_percentage = 100.0
        status.current_step = 'Completed'
        
        # Add the agent's response to the stream
        if result.agent_response:
            logger.info(f"Adding agent response to stream: {len(result.agent_response)} chars")
            status.agent_stream.append(result.agent_response)
        
        if result.status == 'failed':
            status.error = result.agent_response
        
        logger.info(
            f"Strands distribution {distribution_id} completed: "
            f"{result.records_succeeded}/{result.records_processed} succeeded"
        )
        
    except Exception as e:
        logger.error(f"Strands distribution {distribution_id} failed: {str(e)}")
        
        # Update status with error
        status = distribution_status[distribution_id]
        status.status = 'failed'
        status.error = str(e)
        status.current_step = 'Failed'
