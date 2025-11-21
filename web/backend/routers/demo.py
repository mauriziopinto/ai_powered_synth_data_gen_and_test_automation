"""
Demo mode API endpoints
Provides pre-configured scenarios and demo state management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoScenario(BaseModel):
    """Demo scenario configuration"""
    id: str
    name: str
    description: str
    industry: str
    config: Dict[str, Any]
    steps: List[Dict[str, Any]]
    estimated_duration: int
    highlights: List[str]


class DemoState(BaseModel):
    """Current demo state"""
    scenario_id: str
    current_step_index: int
    is_playing: bool
    is_paused: bool
    playback_speed: float
    started_at: Optional[str] = None
    completed_steps: List[str] = []
    annotations: List[Dict[str, Any]] = []


class DemoProgress(BaseModel):
    """Demo progress information"""
    current_step: int
    total_steps: int
    elapsed_time: float
    estimated_time_remaining: float


# In-memory storage for demo states (in production, use database)
demo_states: Dict[str, DemoState] = {}


@router.get("/scenarios", response_model=List[DemoScenario])
async def list_demo_scenarios():
    """
    Get list of available demo scenarios
    
    Returns pre-configured scenarios for telecom, finance, and healthcare
    """
    # Load scenarios from file or database
    # For now, return a simplified version
    scenarios = [
        {
            "id": "telecom-demo",
            "name": "Telecommunications Data Testing",
            "description": "Demonstrate synthetic data generation for telecom customer records",
            "industry": "telecom",
            "config": {
                "name": "Telecom Demo Workflow",
                "schema_fields": [],
                "generation_params": {"num_records": 1000},
                "sdv_model": "gaussian_copula",
                "edge_case_frequency": 0.05,
                "target_systems": []
            },
            "steps": [],
            "estimated_duration": 300,
            "highlights": [
                "Automatic PII detection",
                "Statistical distribution matching",
                "Test automation integration"
            ]
        },
        {
            "id": "finance-demo",
            "name": "Financial Services Data Testing",
            "description": "Generate synthetic financial transaction data",
            "industry": "finance",
            "config": {
                "name": "Finance Demo Workflow",
                "schema_fields": [],
                "generation_params": {"num_records": 5000},
                "sdv_model": "ctgan",
                "edge_case_frequency": 0.02,
                "target_systems": []
            },
            "steps": [],
            "estimated_duration": 280,
            "highlights": [
                "Credit card number masking",
                "Fraud pattern preservation",
                "PCI-DSS compliance"
            ]
        },
        {
            "id": "healthcare-demo",
            "name": "Healthcare Data Testing",
            "description": "Generate HIPAA-compliant synthetic patient records",
            "industry": "healthcare",
            "config": {
                "name": "Healthcare Demo Workflow",
                "schema_fields": [],
                "generation_params": {"num_records": 2000},
                "sdv_model": "gaussian_copula",
                "edge_case_frequency": 0.03,
                "target_systems": []
            },
            "steps": [],
            "estimated_duration": 320,
            "highlights": [
                "HIPAA compliance",
                "Medical record generation",
                "Temporal event sequencing"
            ]
        }
    ]
    
    return scenarios


@router.get("/scenarios/{scenario_id}", response_model=DemoScenario)
async def get_demo_scenario(scenario_id: str):
    """
    Get detailed information about a specific demo scenario
    
    Args:
        scenario_id: ID of the demo scenario
        
    Returns:
        Complete scenario configuration with all steps
    """
    # In production, load from database or file
    scenarios = await list_demo_scenarios()
    scenario = next((s for s in scenarios if s["id"] == scenario_id), None)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Demo scenario not found")
    
    return scenario


@router.post("/state", response_model=DemoState)
async def save_demo_state(state: DemoState):
    """
    Save current demo state
    
    Args:
        state: Current demo state to save
        
    Returns:
        Saved demo state
    """
    demo_states[state.scenario_id] = state
    return state


@router.get("/state/{scenario_id}", response_model=DemoState)
async def get_demo_state(scenario_id: str):
    """
    Get saved demo state for a scenario
    
    Args:
        scenario_id: ID of the demo scenario
        
    Returns:
        Saved demo state or new state if none exists
    """
    if scenario_id in demo_states:
        return demo_states[scenario_id]
    
    # Return default state
    return DemoState(
        scenario_id=scenario_id,
        current_step_index=0,
        is_playing=False,
        is_paused=False,
        playback_speed=1.0,
        completed_steps=[],
        annotations=[]
    )


@router.delete("/state/{scenario_id}")
async def delete_demo_state(scenario_id: str):
    """
    Delete saved demo state
    
    Args:
        scenario_id: ID of the demo scenario
        
    Returns:
        Success message
    """
    if scenario_id in demo_states:
        del demo_states[scenario_id]
    
    return {"message": "Demo state deleted successfully"}


@router.post("/state/{scenario_id}/annotation")
async def add_demo_annotation(
    scenario_id: str,
    annotation: Dict[str, Any]
):
    """
    Add annotation to demo state
    
    Args:
        scenario_id: ID of the demo scenario
        annotation: Annotation data
        
    Returns:
        Updated demo state
    """
    if scenario_id not in demo_states:
        raise HTTPException(status_code=404, detail="Demo state not found")
    
    state = demo_states[scenario_id]
    state.annotations.append({
        **annotation,
        "timestamp": datetime.now().isoformat()
    })
    
    return state


@router.get("/progress/{scenario_id}", response_model=DemoProgress)
async def get_demo_progress(scenario_id: str):
    """
    Get current demo progress
    
    Args:
        scenario_id: ID of the demo scenario
        
    Returns:
        Progress information
    """
    if scenario_id not in demo_states:
        raise HTTPException(status_code=404, detail="Demo state not found")
    
    state = demo_states[scenario_id]
    scenario = await get_demo_scenario(scenario_id)
    
    total_steps = len(scenario.steps)
    current_step = state.current_step_index + 1
    
    # Calculate elapsed time
    elapsed_time = 0.0
    if state.started_at:
        start = datetime.fromisoformat(state.started_at)
        elapsed_time = (datetime.now() - start).total_seconds()
    
    # Estimate remaining time
    estimated_time_remaining = scenario.estimated_duration - elapsed_time
    if estimated_time_remaining < 0:
        estimated_time_remaining = 0
    
    return DemoProgress(
        current_step=current_step,
        total_steps=total_steps,
        elapsed_time=elapsed_time,
        estimated_time_remaining=estimated_time_remaining
    )


@router.post("/scenarios/{scenario_id}/start")
async def start_demo_workflow(scenario_id: str):
    """
    Start a demo workflow execution
    
    This creates a mock workflow execution that simulates the real workflow
    but uses pre-configured data and mock services.
    
    Args:
        scenario_id: ID of the demo scenario
        
    Returns:
        Workflow execution ID and status
    """
    scenario = await get_demo_scenario(scenario_id)
    
    # In production, this would start an actual workflow with demo mode enabled
    workflow_id = f"demo-{scenario_id}-{datetime.now().timestamp()}"
    
    return {
        "workflow_id": workflow_id,
        "scenario_id": scenario_id,
        "status": "running",
        "demo_mode": True,
        "started_at": datetime.now().isoformat()
    }
