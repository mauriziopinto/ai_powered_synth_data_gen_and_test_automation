"""Unit tests for database schema definitions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from shared.database.schema import (
    Base, WorkflowConfig, WorkflowExecution, AgentLog,
    AuditLog, ResultsArchive, CostTracking,
    create_tables, drop_tables
)


@pytest.fixture
def in_memory_engine():
    """Create an in-memory SQLite database for testing.
    
    Note: This uses SQLite which doesn't support PostgreSQL-specific types like JSONB and ARRAY.
    For full schema testing, use a PostgreSQL database.
    """
    # Skip schema tests that require PostgreSQL-specific features
    pytest.skip("Schema tests require PostgreSQL for JSONB and ARRAY support")


@pytest.fixture
def session(in_memory_engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=in_memory_engine)
    session = Session()
    yield session
    session.close()


class TestWorkflowConfig:
    """Test WorkflowConfig model."""
    
    def test_create_workflow_config(self, session):
        """Test creating a workflow configuration."""
        config = WorkflowConfig(
            name="Test Workflow",
            description="Test description",
            config_json={"key": "value"},
            created_by="test_user",
            tags=["test", "demo"]
        )
        
        session.add(config)
        session.commit()
        
        assert config.id is not None
        assert isinstance(config.id, uuid.UUID)
        assert config.name == "Test Workflow"
        assert config.description == "Test description"
        assert config.config_json == {"key": "value"}
        assert config.created_by == "test_user"
        assert config.tags == ["test", "demo"]
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)
    
    def test_workflow_config_required_fields(self, session):
        """Test that required fields are enforced."""
        # Missing name should fail
        config = WorkflowConfig(
            config_json={"key": "value"},
            created_by="test_user"
        )
        
        session.add(config)
        with pytest.raises(Exception):  # SQLAlchemy will raise an exception
            session.commit()
    
    def test_workflow_config_relationships(self, session):
        """Test relationship with WorkflowExecution."""
        config = WorkflowConfig(
            name="Test Workflow",
            config_json={},
            created_by="test_user"
        )
        session.add(config)
        session.commit()
        
        execution = WorkflowExecution(
            config_id=config.id,
            status="running"
        )
        session.add(execution)
        session.commit()
        
        assert len(config.executions) == 1
        assert config.executions[0].id == execution.id


class TestWorkflowExecution:
    """Test WorkflowExecution model."""
    
    def test_create_workflow_execution(self, session):
        """Test creating a workflow execution."""
        config = WorkflowConfig(
            name="Test Workflow",
            config_json={},
            created_by="test_user"
        )
        session.add(config)
        session.commit()
        
        execution = WorkflowExecution(
            config_id=config.id,
            status="running",
            checkpoint_data={"step": 1}
        )
        session.add(execution)
        session.commit()
        
        assert execution.id is not None
        assert isinstance(execution.id, uuid.UUID)
        assert execution.config_id == config.id
        assert execution.status == "running"
        assert isinstance(execution.started_at, datetime)
        assert execution.completed_at is None
        assert execution.error is None
        assert execution.checkpoint_data == {"step": 1}
    
    def test_workflow_execution_completion(self, session):
        """Test updating execution to completed state."""
        config = WorkflowConfig(
            name="Test Workflow",
            config_json={},
            created_by="test_user"
        )
        session.add(config)
        session.commit()
        
        execution = WorkflowExecution(
            config_id=config.id,
            status="running"
        )
        session.add(execution)
        session.commit()
        
        # Update to completed
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        session.commit()
        
        assert execution.status == "completed"
        assert execution.completed_at is not None


class TestAgentLog:
    """Test AgentLog model."""
    
    def test_create_agent_log(self, session):
        """Test creating an agent log entry."""
        config = WorkflowConfig(
            name="Test Workflow",
            config_json={},
            created_by="test_user"
        )
        session.add(config)
        session.commit()
        
        execution = WorkflowExecution(
            config_id=config.id,
            status="running"
        )
        session.add(execution)
        session.commit()
        
        log = AgentLog(
            workflow_execution_id=execution.id,
            agent_name="DataProcessorAgent",
            log_level="INFO",
            message="Processing started",
            log_metadata={"fields": 50}
        )
        session.add(log)
        session.commit()
        
        assert log.id is not None
        assert log.workflow_execution_id == execution.id
        assert log.agent_name == "DataProcessorAgent"
        assert log.log_level == "INFO"
        assert log.message == "Processing started"
        assert log.log_metadata == {"fields": 50}
        assert isinstance(log.timestamp, datetime)


class TestAuditLog:
    """Test AuditLog model."""
    
    def test_create_audit_log(self, session):
        """Test creating an audit log entry."""
        log = AuditLog(
            user_id="test_user",
            action="workflow_started",
            agent="DataProcessorAgent",
            workflow_id=uuid.uuid4(),
            details={"config": "test"},
            cost_usd=0.05
        )
        session.add(log)
        session.commit()
        
        assert log.id is not None
        assert log.user_id == "test_user"
        assert log.action == "workflow_started"
        assert log.agent == "DataProcessorAgent"
        assert isinstance(log.workflow_id, uuid.UUID)
        assert log.details == {"config": "test"}
        assert float(log.cost_usd) == 0.05
        assert isinstance(log.timestamp, datetime)


class TestResultsArchive:
    """Test ResultsArchive model."""
    
    def test_create_results_archive(self, session):
        """Test creating a results archive entry."""
        config = WorkflowConfig(
            name="Test Workflow",
            config_json={},
            created_by="test_user"
        )
        session.add(config)
        session.commit()
        
        execution = WorkflowExecution(
            config_id=config.id,
            status="completed"
        )
        session.add(execution)
        session.commit()
        
        result = ResultsArchive(
            workflow_execution_id=execution.id,
            result_type="synthetic_data",
            storage_path="s3://bucket/path/to/data.csv",
            result_metadata={"rows": 1000}
        )
        session.add(result)
        session.commit()
        
        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)
        assert result.workflow_execution_id == execution.id
        assert result.result_type == "synthetic_data"
        assert result.storage_path == "s3://bucket/path/to/data.csv"
        assert result.result_metadata == {"rows": 1000}
        assert isinstance(result.created_at, datetime)


class TestCostTracking:
    """Test CostTracking model."""
    
    def test_create_cost_tracking(self, session):
        """Test creating a cost tracking entry."""
        config = WorkflowConfig(
            name="Test Workflow",
            config_json={},
            created_by="test_user"
        )
        session.add(config)
        session.commit()
        
        execution = WorkflowExecution(
            config_id=config.id,
            status="running"
        )
        session.add(execution)
        session.commit()
        
        cost = CostTracking(
            workflow_execution_id=execution.id,
            service="bedrock",
            operation="invoke_model",
            quantity=100,
            unit="tokens",
            cost_usd=0.015
        )
        session.add(cost)
        session.commit()
        
        assert cost.id is not None
        assert cost.workflow_execution_id == execution.id
        assert cost.service == "bedrock"
        assert cost.operation == "invoke_model"
        assert float(cost.quantity) == 100
        assert cost.unit == "tokens"
        assert float(cost.cost_usd) == 0.015
        assert isinstance(cost.timestamp, datetime)


class TestSchemaOperations:
    """Test schema creation and deletion operations."""
    
    def test_create_tables(self):
        """Test creating all tables."""
        engine = create_engine('sqlite:///:memory:')
        
        # Tables should not exist initially
        assert not engine.dialect.has_table(engine.connect(), 'workflow_configs')
        
        # Create tables
        create_tables(engine)
        
        # Verify tables exist
        assert engine.dialect.has_table(engine.connect(), 'workflow_configs')
        assert engine.dialect.has_table(engine.connect(), 'workflow_executions')
        assert engine.dialect.has_table(engine.connect(), 'agent_logs')
        assert engine.dialect.has_table(engine.connect(), 'audit_log')
        assert engine.dialect.has_table(engine.connect(), 'results_archive')
        assert engine.dialect.has_table(engine.connect(), 'cost_tracking')
    
    def test_drop_tables(self):
        """Test dropping all tables."""
        engine = create_engine('sqlite:///:memory:')
        
        # Create tables first
        create_tables(engine)
        assert engine.dialect.has_table(engine.connect(), 'workflow_configs')
        
        # Drop tables
        drop_tables(engine)
        
        # Verify tables are gone
        assert not engine.dialect.has_table(engine.connect(), 'workflow_configs')
        assert not engine.dialect.has_table(engine.connect(), 'workflow_executions')


@pytest.mark.unit
class TestSchemaRelationships:
    """Test relationships between models."""
    
    def test_cascade_relationships(self, session):
        """Test that relationships are properly configured."""
        config = WorkflowConfig(
            name="Test Workflow",
            config_json={},
            created_by="test_user"
        )
        session.add(config)
        session.commit()
        
        execution = WorkflowExecution(
            config_id=config.id,
            status="running"
        )
        session.add(execution)
        session.commit()
        
        # Add related records
        log = AgentLog(
            workflow_execution_id=execution.id,
            agent_name="TestAgent",
            log_level="INFO",
            message="Test"
        )
        session.add(log)
        
        result = ResultsArchive(
            workflow_execution_id=execution.id,
            result_type="test",
            storage_path="/path"
        )
        session.add(result)
        
        cost = CostTracking(
            workflow_execution_id=execution.id,
            service="test",
            operation="test",
            quantity=1,
            unit="test",
            cost_usd=0.01
        )
        session.add(cost)
        session.commit()
        
        # Verify relationships
        assert len(execution.logs) == 1
        assert len(execution.results) == 1
        assert len(execution.costs) == 1
        assert execution.config.id == config.id
