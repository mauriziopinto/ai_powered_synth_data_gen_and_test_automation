"""Monitoring API endpoints.

Provides endpoints for:
- Real-time workflow monitoring
- Agent status
- System metrics

Validates Requirement 11.3
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentStatus(BaseModel):
    """Agent status model."""
    agent_id: str
    agent_type: str
    status: str
    current_operation: Optional[str] = None
    progress: float = 0.0
    message: Optional[str] = None


class SystemMetrics(BaseModel):
    """System metrics model."""
    timestamp: str
    active_workflows: int
    total_workflows: int
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    cost_today_usd: float = 0.0


@router.get("/agents/{workflow_id}", response_model=List[AgentStatus])
async def get_agent_status(workflow_id: str):
    """Get status of all agents in a workflow.
    
    Args:
        workflow_id: Workflow ID
    
    Returns:
        List of agent statuses
    """
    from web.backend.routers.workflow import workflow_states, _load_workflow_from_disk
    
    # Try to get workflow from memory or disk
    workflow = workflow_states.get(workflow_id)
    if not workflow:
        workflow = _load_workflow_from_disk(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Define all agents in the workflow pipeline
    all_agents = [
        {
            "agent_id": "data_processor",
            "agent_type": "Data Processor",
            "stage": "data_processing"
        },
        {
            "agent_id": "synthetic_data",
            "agent_type": "Synthetic Data",
            "stage": "synthetic_generation"
        },
        {
            "agent_id": "distribution",
            "agent_type": "Distribution",
            "stage": "data_distribution"
        },
        {
            "agent_id": "test_case",
            "agent_type": "Test Case",
            "stage": "test_case_creation"
        },
        {
            "agent_id": "test_execution",
            "agent_type": "Test Execution",
            "stage": "test_execution"
        }
    ]
    
    workflow_status = workflow.get('status', 'pending')
    current_stage = workflow.get('current_stage', '')
    stages_completed = workflow.get('stages_completed', [])
    
    agents_status = []
    
    for agent_info in all_agents:
        agent_id = agent_info["agent_id"]
        agent_type = agent_info["agent_type"]
        stage = agent_info["stage"]
        
        # Determine agent status based on workflow state
        if stage in stages_completed:
            status = "completed"
            progress = 100.0
            message = f"{agent_type} completed successfully"
        elif current_stage == stage:
            status = "running"
            progress = workflow.get('progress', 0.0)
            message = workflow.get('message', f"{agent_type} in progress")
        elif workflow_status == 'failed' and current_stage == stage:
            status = "failed"
            progress = workflow.get('progress', 0.0)
            message = workflow.get('error', f"{agent_type} failed")
        else:
            status = "idle"
            progress = 0.0
            message = f"{agent_type} pending"
        
        agents_status.append(
            AgentStatus(
                agent_id=agent_id,
                agent_type=agent_type,
                status=status,
                current_operation=message,
                progress=progress,
                message=message
            )
        )
    
    return agents_status


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get current system metrics.
    
    Returns:
        System metrics
    """
    # Mock data for now
    return SystemMetrics(
        timestamp=datetime.now().isoformat(),
        active_workflows=2,
        total_workflows=15,
        cpu_usage_percent=45.2,
        memory_usage_percent=62.8,
        cost_today_usd=2.45
    )
