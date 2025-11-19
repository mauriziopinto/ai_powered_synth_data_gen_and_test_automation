"""Workflow configuration and execution models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class TargetConfig:
    """Configuration for a target system."""
    name: str
    type: str  # 'database', 'salesforce', 'api', 'file'
    connection_string: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    load_strategy: str = 'truncate_insert'  # or 'upsert'
    table_mappings: Optional[Dict[str, List[str]]] = None
    respect_fk_order: bool = True


@dataclass
class WorkflowConfig:
    """Complete workflow configuration."""
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    
    # Data source
    production_data_path: Path
    
    # Generation parameters
    sdv_model: str = 'gaussian_copula'
    bedrock_model: str = 'anthropic.claude-3-sonnet-20240229-v1:0'
    num_synthetic_records: int = 1000
    preserve_edge_cases: bool = True
    edge_case_frequency: float = 0.05
    random_seed: Optional[int] = None
    
    # Target systems
    targets: List[TargetConfig] = field(default_factory=list)
    
    # Test configuration
    test_framework: str = 'robot'
    jira_test_tag: str = ''
    parallel_execution: bool = False
    
    # External integrations
    confluence_space: str = ''
    jira_project: str = ''
    
    # Flags
    demo_mode: bool = True
    enable_cost_tracking: bool = True
    
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """Workflow execution state."""
    id: str
    config_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    # Agent states
    current_agent: Optional[str] = None
    agent_progress: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    sensitivity_report_id: Optional[str] = None
    synthetic_dataset_id: Optional[str] = None
    distribution_report_id: Optional[str] = None
    test_results_id: Optional[str] = None
    
    # Costs
    total_cost_usd: float = 0.0
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
