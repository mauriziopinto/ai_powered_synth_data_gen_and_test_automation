"""ORM mapper utilities for converting between dataclass models and SQLAlchemy models."""

from typing import Optional, List
from datetime import datetime
import uuid

from shared.models.workflow import WorkflowConfig as WorkflowConfigModel
from shared.models.workflow import WorkflowExecution as WorkflowExecutionModel
from shared.models.workflow import WorkflowStatus
from shared.database.schema import (
    WorkflowConfig as WorkflowConfigORM,
    WorkflowExecution as WorkflowExecutionORM
)


class ORMMapper:
    """Mapper for converting between dataclass models and SQLAlchemy ORM models."""
    
    @staticmethod
    def workflow_config_to_orm(config: WorkflowConfigModel) -> WorkflowConfigORM:
        """Convert WorkflowConfig dataclass to ORM model.
        
        Args:
            config: WorkflowConfig dataclass instance
            
        Returns:
            WorkflowConfigORM instance
        """
        return WorkflowConfigORM(
            id=uuid.UUID(config.id) if isinstance(config.id, str) else config.id,
            name=config.name,
            description=config.description,
            config_json=config.to_dict(),
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=datetime.utcnow(),
            tags=config.tags
        )
    
    @staticmethod
    def workflow_config_from_orm(orm_config: WorkflowConfigORM) -> WorkflowConfigModel:
        """Convert WorkflowConfig ORM model to dataclass.
        
        Args:
            orm_config: WorkflowConfigORM instance
            
        Returns:
            WorkflowConfig dataclass instance
        """
        return WorkflowConfigModel.from_dict(orm_config.config_json)
    
    @staticmethod
    def workflow_execution_to_orm(execution: WorkflowExecutionModel) -> WorkflowExecutionORM:
        """Convert WorkflowExecution dataclass to ORM model.
        
        Args:
            execution: WorkflowExecution dataclass instance
            
        Returns:
            WorkflowExecutionORM instance
        """
        checkpoint_data = {
            'current_agent': execution.current_agent,
            'agent_progress': execution.agent_progress,
            'sensitivity_report_id': execution.sensitivity_report_id,
            'synthetic_dataset_id': execution.synthetic_dataset_id,
            'distribution_report_id': execution.distribution_report_id,
            'test_results_id': execution.test_results_id,
            'total_cost_usd': execution.total_cost_usd,
            'cost_breakdown': execution.cost_breakdown
        }
        
        return WorkflowExecutionORM(
            id=uuid.UUID(execution.id) if isinstance(execution.id, str) else execution.id,
            config_id=uuid.UUID(execution.config_id) if isinstance(execution.config_id, str) else execution.config_id,
            status=execution.status.value,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error=execution.error,
            checkpoint_data=checkpoint_data
        )
    
    @staticmethod
    def workflow_execution_from_orm(orm_execution: WorkflowExecutionORM) -> WorkflowExecutionModel:
        """Convert WorkflowExecution ORM model to dataclass.
        
        Args:
            orm_execution: WorkflowExecutionORM instance
            
        Returns:
            WorkflowExecution dataclass instance
        """
        checkpoint = orm_execution.checkpoint_data or {}
        
        return WorkflowExecutionModel(
            id=str(orm_execution.id),
            config_id=str(orm_execution.config_id),
            status=WorkflowStatus(orm_execution.status),
            started_at=orm_execution.started_at,
            completed_at=orm_execution.completed_at,
            error=orm_execution.error,
            current_agent=checkpoint.get('current_agent'),
            agent_progress=checkpoint.get('agent_progress', {}),
            sensitivity_report_id=checkpoint.get('sensitivity_report_id'),
            synthetic_dataset_id=checkpoint.get('synthetic_dataset_id'),
            distribution_report_id=checkpoint.get('distribution_report_id'),
            test_results_id=checkpoint.get('test_results_id'),
            total_cost_usd=checkpoint.get('total_cost_usd', 0.0),
            cost_breakdown=checkpoint.get('cost_breakdown', {})
        )
