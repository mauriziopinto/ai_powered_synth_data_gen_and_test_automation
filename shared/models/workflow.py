"""Workflow configuration and execution models."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path
import json


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TargetConfig':
        """Create from dictionary."""
        return cls(**data)


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert Path to string
        data['production_data_path'] = str(self.production_data_path)
        # Convert datetime to ISO format
        data['created_at'] = self.created_at.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowConfig':
        """Create from dictionary."""
        # Convert string to Path
        if isinstance(data.get('production_data_path'), str):
            data['production_data_path'] = Path(data['production_data_path'])
        
        # Convert ISO string to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Convert target dicts to TargetConfig objects
        if 'targets' in data:
            data['targets'] = [
                TargetConfig.from_dict(t) if isinstance(t, dict) else t
                for t in data['targets']
            ]
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WorkflowConfig':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enum to string
        data['status'] = self.status.value
        # Convert datetimes to ISO format
        data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowExecution':
        """Create from dictionary."""
        # Convert string to enum
        if isinstance(data.get('status'), str):
            data['status'] = WorkflowStatus(data['status'])
        
        # Convert ISO strings to datetime
        if isinstance(data.get('started_at'), str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at') and isinstance(data['completed_at'], str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WorkflowExecution':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
