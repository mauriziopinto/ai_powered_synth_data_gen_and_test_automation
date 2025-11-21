"""Agent activity logger for real-time workflow monitoring."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LogEntry(BaseModel):
    """A single log entry from an agent."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    workflow_id: str
    agent_name: str
    level: str = "info"  # "info", "warning", "error"
    message: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentLogger:
    """Structured logger for agent activities with WebSocket broadcasting."""
    
    def __init__(self, workflow_id: str, agent_name: str):
        """Initialize agent logger.
        
        Args:
            workflow_id: ID of the workflow this agent belongs to
            agent_name: Name of the agent (e.g., "SyntheticDataAgent")
        """
        self.workflow_id = workflow_id
        self.agent_name = agent_name
        self.logs: List[LogEntry] = []
        self._broadcast_callback = None
        self._workflow_state = None  # Will be set by create_synthetic_agent_with_logger
        
        logger.info(f"Initialized AgentLogger for {agent_name} in workflow {workflow_id}")
    
    def set_broadcast_callback(self, callback):
        """Set callback function for broadcasting logs via WebSocket.
        
        Args:
            callback: Async function that broadcasts log entries
        """
        self._broadcast_callback = callback
    
    def log(self, message: str, level: str = "info", metadata: Optional[Dict[str, Any]] = None):
        """Emit a log entry.
        
        Args:
            message: Log message
            level: Severity level ("info", "warning", "error")
            metadata: Optional metadata dictionary
        """
        # Validate level
        if level not in ["info", "warning", "error"]:
            logger.warning(f"Invalid log level '{level}', defaulting to 'info'")
            level = "info"
        
        # Create log entry
        entry = LogEntry(
            workflow_id=self.workflow_id,
            agent_name=self.agent_name,
            level=level,
            message=message,
            metadata=metadata
        )
        
        # Store in memory
        self.logs.append(entry)
        
        # Store in workflow state if available
        if self._workflow_state is not None:
            if 'agent_logs' not in self._workflow_state:
                self._workflow_state['agent_logs'] = []
            self._workflow_state['agent_logs'].append(entry.dict())
        
        # Log to system logger
        log_func = getattr(logger, level, logger.info)
        log_func(f"[{self.agent_name}] {message}")
        
        # Broadcast via WebSocket if callback is set
        if self._broadcast_callback:
            try:
                import asyncio
                # Try to get the running event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Schedule the coroutine
                    asyncio.create_task(self._broadcast_callback(entry))
                except RuntimeError:
                    # No running loop, skip broadcast
                    logger.debug("No running event loop, skipping WebSocket broadcast")
            except Exception as e:
                logger.error(f"Failed to broadcast log entry: {str(e)}")
    
    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an info message."""
        self.log(message, level="info", metadata=metadata)
    
    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a warning message."""
        self.log(message, level="warning", metadata=metadata)
    
    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an error message."""
        self.log(message, level="error", metadata=metadata)
    
    def get_logs(self) -> List[LogEntry]:
        """Retrieve all log entries.
        
        Returns:
            List of log entries in chronological order
        """
        return self.logs.copy()
    
    def get_logs_dict(self) -> List[Dict[str, Any]]:
        """Retrieve all log entries as dictionaries.
        
        Returns:
            List of log entry dictionaries
        """
        return [entry.dict() for entry in self.logs]
    
    def clear_logs(self):
        """Clear all stored log entries."""
        self.logs.clear()
        logger.debug(f"Cleared logs for {self.agent_name}")
