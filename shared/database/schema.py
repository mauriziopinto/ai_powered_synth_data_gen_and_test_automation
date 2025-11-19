"""Database schema definitions."""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean,
    ForeignKey, ARRAY, JSON, DECIMAL, create_engine
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class WorkflowConfig(Base):
    """Workflow configuration storage."""
    __tablename__ = 'workflow_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config_json = Column(JSONB, nullable=False)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(ARRAY(Text))
    
    executions = relationship("WorkflowExecution", back_populates="config")


class WorkflowExecution(Base):
    """Workflow execution tracking."""
    __tablename__ = 'workflow_executions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey('workflow_configs.id'))
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error = Column(Text)
    checkpoint_data = Column(JSONB)
    
    config = relationship("WorkflowConfig", back_populates="executions")
    logs = relationship("AgentLog", back_populates="execution")
    results = relationship("ResultsArchive", back_populates="execution")
    costs = relationship("CostTracking", back_populates="execution")


class AgentLog(Base):
    """Agent execution logs."""
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey('workflow_executions.id'))
    agent_name = Column(String(100), nullable=False)
    log_level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    metadata = Column(JSONB)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    execution = relationship("WorkflowExecution", back_populates="logs")


class AuditLog(Base):
    """Audit trail for compliance."""
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    agent = Column(String(100))
    workflow_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    cost_usd = Column(DECIMAL(10, 4))


class ResultsArchive(Base):
    """Results storage references."""
    __tablename__ = 'results_archive'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey('workflow_executions.id'))
    result_type = Column(String(50), nullable=False)
    storage_path = Column(String(500), nullable=False)
    metadata = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    execution = relationship("WorkflowExecution", back_populates="results")


class CostTracking(Base):
    """AWS cost tracking."""
    __tablename__ = 'cost_tracking'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey('workflow_executions.id'))
    service = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    quantity = Column(DECIMAL(15, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    cost_usd = Column(DECIMAL(10, 4), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    execution = relationship("WorkflowExecution", back_populates="costs")


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Drop all tables from the database."""
    Base.metadata.drop_all(engine)
