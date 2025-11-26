"""Advanced Strands MCP Agent with retry logic, conditional distribution, and transformations.

This agent extends the base Strands agent with:
- Automatic retry logic for failed records
- Conditional distribution based on data values
- Data transformations before distribution
- Structured output with per-record results
- Batch operations for performance
- Parallel processing support
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

logger = logging.getLogger(__name__)


class RecordStatus(Enum):
    """Status of individual record distribution."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class RecordResult:
    """Result for a single record distribution."""
    record_id: int
    status: RecordStatus
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    retry_count: int = 0
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "status": self.status.value,
            "tool_calls": self.tool_calls,
            "error": self.error,
            "retry_count": self.retry_count,
            "duration": self.duration
        }


@dataclass
class AdvancedDistributionResult:
    """Enhanced result with per-record details."""
    status: str  # 'success', 'failed', 'partial'
    records_processed: int
    records_succeeded: int
    records_failed: int
    records_skipped: int
    duration: float
    agent_response: str
    record_results: List[RecordResult]
    errors: List[str]
    timestamp: datetime
    conversation_history: List[Dict[str, Any]]
    retry_stats: Dict[str, int]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.records_processed == 0:
            return 0.0
        return (self.records_succeeded / self.records_processed) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "status": self.status,
            "records_processed": self.records_processed,
            "records_succeeded": self.records_succeeded,
            "records_failed": self.records_failed,
            "records_skipped": self.records_skipped,
            "duration": self.duration,
            "agent_response": self.agent_response,
            "record_results": [r.to_dict() for r in self.record_results],
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
            "retry_stats": self.retry_stats,
            "success_rate": self.success_rate
        }


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    enabled: bool = True
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on_errors: List[str] = field(default_factory=lambda: [
        "timeout", "connection", "rate_limit", "temporary"
    ])


@dataclass
class BatchConfig:
    """Configuration for batch operations."""
    enabled: bool = False
    batch_size: int = 10
    parallel: bool = False
    max_workers: int = 3


@dataclass
class AdvancedConfig:
    """Advanced configuration for distribution."""
    retry: RetryConfig = field(default_factory=RetryConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    enable_transformations: bool = True
    enable_conditional_logic: bool = True
    structured_output: bool = True


class AdvancedStrandsMCPAgent:
    """
    Advanced MCP distribution agent with retry, conditional logic, and transformations.
    
    Features:
    - Automatic retry with exponential backoff
    - Conditional distribution based on data values
    - Data transformations (split names, format phones, etc.)
    - Structured output with per-record results
    - Batch operations for performance
    - Parallel processing support
    
    Example usage:
        config = AdvancedConfig(
            retry=RetryConfig(enabled=True, max_retries=3),
            batch=BatchConfig(enabled=True, batch_size=10)
        )
        
        agent = AdvancedStrandsMCPAgent(
            mcp_config_path="data/mcp_config.json",
            advanced_config=config
        )
        
        result = await agent.distribute(
            dataset=df,
            instructions="Create Jira issues with retry on failure"
        )
    """
    
    def __init__(
        self,
        mcp_config_path: str,
        model_id: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        advanced_config: Optional[AdvancedConfig] = None
    ):
        """
        Initialize advanced Strands MCP agent.
        
        Args:
            mcp_config_path: Path to MCP configuration JSON
            model_id: Bedrock model ID
            advanced_config: Advanced feature configuration
        """
        self.mcp_config_path = Path(mcp_config_path)
        self.model_id = model_id
        self.config = advanced_config or AdvancedConfig()
        self.mcp_config: Optional[Dict[str, Any]] = None
        self.mcp_clients: List[MCPClient] = []
        self.agent: Optional[Agent] = None
        
        # Load MCP configuration
        self._load_mcp_config()
    
    def _load_mcp_config(self):
        """Load and parse MCP configuration."""
        try:
            if not self.mcp_config_path.exists():
                logger.warning(f"MCP config not found at {self.mcp_config_path}")
                self.mcp_config = {"mcpServers": {}}
                return
            
            with open(self.mcp_config_path, 'r') as f:
                self.mcp_config = json.load(f)
            
            logger.info(f"Loaded MCP config from {self.mcp_config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {str(e)}")
            self.mcp_config = {"mcpServers": {}}
    
    def _create_mcp_clients(self) -> List[MCPClient]:
        """Create MCP clients from configuration."""
        clients = []
        
        if not self.mcp_config or 'mcpServers' not in self.mcp_config:
            logger.warning("No MCP servers configured")
            return clients
        
        for server_name, server_config in self.mcp_config['mcpServers'].items():
            if server_config.get('disabled', False):
                continue
            
            try:
                command = server_config.get('command', 'uvx')
                args = server_config.get('args', [])
                env = server_config.get('env', {})
                
                def create_client(cmd=command, a=args, e=env):
                    return stdio_client(
                        StdioServerParameters(
                            command=cmd,
                            args=a,
                            env=e
                        )
                    )
                
                client = MCPClient(
                    transport_callable=create_client,
                    prefix=server_name
                )
                
                clients.append(client)
                logger.info(f"Created MCP client for server: {server_name}")
                
            except Exception as e:
                logger.error(f"Failed to create MCP client for {server_name}: {str(e)}")
        
        return clients
    
    async def initialize_agent(self) -> Agent:
        """Initialize Strands agent with MCP tools."""
        self.mcp_clients = self._create_mcp_clients()
        
        if not self.mcp_clients:
            raise ValueError(
                "No MCP servers available. Please configure MCP servers."
            )
        
        self.agent = Agent(
            tools=self.mcp_clients,
            model_id=self.model_id
        )
        
        logger.info(f"Initialized advanced Strands agent with {len(self.mcp_clients)} MCP servers")
        
        return self.agent
    
    async def distribute(
        self,
        dataset: pd.DataFrame,
        instructions: str,
        progress_callback: Optional[Callable] = None
    ) -> AdvancedDistributionResult:
        """
        Distribute dataset with advanced features.
        
        Args:
            dataset: DataFrame to distribute
            instructions: Natural language instructions
            progress_callback: Optional progress callback
        
        Returns:
            AdvancedDistributionResult with detailed per-record results
        """
        start_time = datetime.now()
        conversation_history = []
        record_results: List[RecordResult] = []
        retry_stats = {"total_retries": 0, "successful_retries": 0, "failed_retries": 0}
        
        try:
            # Validate inputs
    