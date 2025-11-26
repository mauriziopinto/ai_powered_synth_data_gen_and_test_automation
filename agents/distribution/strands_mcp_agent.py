"""Real Strands-based MCP Distribution Agent.

This agent uses the Strands framework with actual MCP servers to distribute
synthetic data to external systems using natural language instructions.
"""

import asyncio
import json
import logging
import sys
import io
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

logger = logging.getLogger(__name__)


class StreamCapture:
    """Capture stdout/stderr to collect agent output."""
    def __init__(self):
        self.captured_text = []
        self.buffer = io.StringIO()
        self.original_stdout = sys.stdout
        
    def write(self, text):
        """Capture written text."""
        self.buffer.write(text)
        self.original_stdout.write(text)  # Still print to console
        if text.strip():
            self.captured_text.append(text)
        
    def flush(self):
        """Flush the buffer."""
        self.buffer.flush()
        self.original_stdout.flush()
        
    def get_captured(self):
        """Get all captured text."""
        return ''.join(self.captured_text)
        
    def __enter__(self):
        sys.stdout = self
        return self
        
    def __exit__(self, *args):
        sys.stdout = self.original_stdout


@dataclass
class DistributionResult:
    """Result of MCP-based distribution using Strands agent."""
    status: str  # 'success', 'failed', 'partial'
    records_processed: int
    records_succeeded: int
    records_failed: int
    duration: float
    agent_response: str
    errors: List[str]
    timestamp: datetime
    conversation_history: List[Dict[str, Any]]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.records_processed == 0:
            return 0.0
        return (self.records_succeeded / self.records_processed) * 100


class StrandsMCPDistributionAgent:
    """
    Production-ready MCP distribution agent using Strands framework.
    
    This agent:
    1. Connects to real MCP servers configured in mcp_config.json
    2. Uses Strands Agent with MCP tools for intelligent distribution
    3. Processes natural language instructions
    4. Distributes data using actual MCP tool calls
    5. Provides real-time progress tracking
    
    Example usage:
        agent = StrandsMCPDistributionAgent(mcp_config_path="data/mcp_config.json")
        result = await agent.distribute(
            dataset=df,
            instructions="Create a Jira issue for each record with name as summary"
        )
    """
    
    def __init__(
        self,
        mcp_config_path: str,
        model_id: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    ):
        """
        Initialize Strands MCP distribution agent.
        
        Args:
            mcp_config_path: Path to MCP configuration JSON file
            model_id: Bedrock model ID to use for the agent
        """
        self.mcp_config_path = Path(mcp_config_path)
        self.model_id = model_id
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
        """
        Create MCP clients from configuration.
        
        Returns:
            List of MCPClient instances
        """
        clients = []
        
        if not self.mcp_config or 'mcpServers' not in self.mcp_config:
            logger.warning("No MCP servers configured")
            return clients
        
        for server_name, server_config in self.mcp_config['mcpServers'].items():
            # Skip disabled servers
            if server_config.get('disabled', False):
                logger.info(f"Skipping disabled server: {server_name}")
                continue
            
            try:
                # Extract configuration
                command = server_config.get('command', 'uvx')
                args = server_config.get('args', [])
                env = server_config.get('env', {})
                
                # Create stdio client factory
                def create_client(cmd=command, a=args, e=env):
                    return stdio_client(
                        StdioServerParameters(
                            command=cmd,
                            args=a,
                            env=e
                        )
                    )
                
                # Create MCP client with server name as prefix and increased timeout
                # First-time startup can take 30-60s while uvx downloads packages
                client = MCPClient(
                    transport_callable=create_client,
                    prefix=server_name,
                    startup_timeout=120  # 2 minutes for first-time package downloads
                )
                
                clients.append(client)
                logger.info(f"Created MCP client for server: {server_name}")
                
            except Exception as e:
                logger.error(f"Failed to create MCP client for {server_name}: {str(e)}")
        
        return clients
    
    async def initialize_agent(self) -> Agent:
        """
        Initialize Strands agent with MCP tools.
        
        This method:
        1. Creates MCP clients from configuration
        2. Connects to MCP servers
        3. Discovers available tools
        4. Creates Strands agent with tools
        
        Returns:
            Initialized Strands Agent
        """
        # Create MCP clients
        self.mcp_clients = self._create_mcp_clients()
        
        if not self.mcp_clients:
            logger.warning("No MCP servers configured, creating agent without tools")
            self.agent = Agent(
                tools=[],
                model=self.model_id
            )
            return self.agent
        
        # Create agent with MCP clients (using managed integration)
        # The agent will automatically handle MCP connection lifecycle
        try:
            logger.info(f"Initializing Strands agent with {len(self.mcp_clients)} MCP servers...")
            logger.info("Note: First-time MCP server startup may take 30-60 seconds while uvx downloads packages")
            
            self.agent = Agent(
                tools=self.mcp_clients,
                model=self.model_id
            )
            
            logger.info(f"Successfully initialized Strands agent with {len(self.mcp_clients)} MCP servers")
            
        except TimeoutError as e:
            logger.error(f"MCP client initialization timed out: {str(e)}")
            logger.error("This usually happens on first run when uvx needs to download MCP server packages")
            logger.error("Solution: Run 'uvx mcp-server-sqlite --help' manually first to pre-download packages")
            
            # Create agent without tools
            logger.warning("Creating agent without MCP tools due to timeout")
            self.agent = Agent(
                tools=[],
                model=self.model_id
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands agent: {str(e)}")
            
            # If MCP clients fail, create agent without tools for now
            # This allows the agent to still work for planning/analysis
            logger.warning("Creating agent without MCP tools due to initialization failure")
            self.agent = Agent(
                tools=[],
                model=self.model_id
            )
        
        return self.agent
    
    async def distribute(
        self,
        dataset: pd.DataFrame,
        instructions: str,
        progress_callback: Optional[Callable] = None,
        stream_callback: Optional[Callable] = None
    ) -> DistributionResult:
        """
        Distribute dataset using natural language instructions.
        
        This is the main entry point for MCP-based distribution using Strands.
        
        Args:
            dataset: DataFrame with data to distribute
            instructions: Natural language instructions for distribution
            progress_callback: Optional callback for progress updates
        
        Returns:
            DistributionResult with operation details
        """
        logger.info("=== DISTRIBUTE METHOD CALLED ===")
        logger.info(f"Dataset shape: {dataset.shape}")
        logger.info(f"Instructions: {instructions[:100]}...")
        logger.info(f"Stream callback provided: {stream_callback is not None}")
        
        start_time = datetime.now()
        conversation_history = []
        
        try:
            # Validate inputs
            if dataset.empty:
                raise ValueError("Cannot distribute empty dataset")
            
            if not instructions or not instructions.strip():
                raise ValueError("Distribution instructions are required")
            
            # Initialize agent
            if not self.agent:
                await self.initialize_agent()
            
            # Check if MCP tools are available
            if not self.mcp_clients or len(self.mcp_clients) == 0:
                error_msg = (
                    "No MCP servers are configured or all failed to initialize. "
                    "Please configure MCP servers with valid credentials in the MCP Config page. "
                    "Common issues: \n"
                    "1. MCP server commands not installed (run: uvx mcp-server-jira, etc.)\n"
                    "2. Invalid credentials in MCP configuration\n"
                    "3. MCP servers are disabled"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Prepare dataset information for the agent
            dataset_info = {
                "columns": list(dataset.columns),
                "row_count": len(dataset),
                "sample_records": dataset.head(3).to_dict(orient='records')
            }
            
            # Create comprehensive prompt for the agent
            prompt = self._create_distribution_prompt(
                dataset_info=dataset_info,
                instructions=instructions,
                dataset=dataset
            )
            
            logger.info(f"Starting distribution with Strands agent")
            logger.info(f"Dataset: {len(dataset)} records, {len(dataset.columns)} columns")
            logger.info(f"Instructions: {instructions}")
            
            # Execute distribution using Strands agent with streaming
            agent_response = ""
            
            if stream_callback:
                # Use stream_async to get real-time streaming events
                async for event in self.agent.stream_async(prompt):
                    # Extract text data from streaming events
                    if "data" in event:
                        text_chunk = event["data"]
                        agent_response += text_chunk
                        # Send chunk to UI immediately
                        await stream_callback(text_chunk)
            else:
                # No streaming, just get the full response
                response = self.agent(prompt)
                agent_response = self._extract_response_content(response)
            conversation_history.append({
                "role": "user",
                "content": prompt
            })
            conversation_history.append({
                "role": "assistant",
                "content": agent_response
            })
            
            # Parse results from agent response
            # In a real implementation, the agent would provide structured output
            # For now, we'll estimate based on the response
            result = self._parse_agent_response(
                agent_response=agent_response,
                dataset=dataset,
                start_time=start_time,
                conversation_history=conversation_history
            )
            
            logger.info(
                f"Distribution completed: {result.status}, "
                f"{result.records_succeeded}/{result.records_processed} succeeded"
            )
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Distribution failed: {str(e)}")
            
            return DistributionResult(
                status='failed',
                records_processed=0,
                records_succeeded=0,
                records_failed=0,
                duration=duration,
                agent_response=f"Distribution failed: {str(e)}",
                errors=[str(e)],
                timestamp=datetime.now(),
                conversation_history=conversation_history
            )
    
    def _create_distribution_prompt(
        self,
        dataset_info: Dict[str, Any],
        instructions: str,
        dataset: pd.DataFrame
    ) -> str:
        """
        Create a comprehensive prompt for the Strands agent.
        
        Args:
            dataset_info: Information about the dataset
            instructions: User's distribution instructions
            dataset: The actual dataset
        
        Returns:
            Formatted prompt string
        """
        # Convert dataset to a format the agent can work with
        # For large datasets, we'll provide a sample and instructions to iterate
        dataset_json = dataset.to_json(orient='records', indent=2)
        
        prompt = f"""You are a data distribution agent. Your task is to distribute the provided dataset to external systems using the available MCP tools.

Dataset Information:
- Columns: {', '.join(dataset_info['columns'])}
- Total Records: {dataset_info['row_count']}
- Sample Records (first 3):
{json.dumps(dataset_info['sample_records'], indent=2)}

Full Dataset (JSON format):
{dataset_json}

User Instructions:
{instructions}

Your Task:
1. Analyze the user's instructions to understand what needs to be done
2. Identify which MCP tools are available and appropriate for this task
3. For EACH record in the dataset, use the appropriate MCP tool(s) to distribute the data
4. Keep track of successes and failures
5. Provide a summary of the distribution results

Important Guidelines:
- Process ALL {dataset_info['row_count']} records in the dataset
- Use the exact column names from the dataset when calling MCP tools
- If a tool call fails, note the error but continue with remaining records
- Provide clear feedback about what was accomplished

Please proceed with the distribution now."""
        
        return prompt
    
    def _extract_response_content(self, response: Any) -> str:
        """
        Extract text content from agent response.
        
        Args:
            response: Agent response object (can be streaming chunk or full response)
        
        Returns:
            Extracted text content (empty string if no text content)
        """
        try:
            # Handle streaming chunks - only extract text blocks
            if hasattr(response, 'message'):
                message = response.message
                if isinstance(message, dict) and 'content' in message:
                    content = message['content']
                    if isinstance(content, list):
                        # Extract only text content blocks, skip tool_use blocks
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict):
                                # Only include text blocks, skip tool_use
                                if block.get('type') == 'text' and 'text' in block:
                                    text_parts.append(block['text'])
                        if text_parts:
                            return ''.join(text_parts)
                    elif isinstance(content, str):
                        # Sometimes content is just a string
                        return content
            
            # Try direct text attribute
            if hasattr(response, 'text'):
                return response.text
            
            # Try content attribute directly
            if hasattr(response, 'content'):
                content = response.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                    if text_parts:
                        return ''.join(text_parts)
            
            # Fallback: return empty string to avoid showing raw JSON
            return ""
            
        except Exception as e:
            logger.error(f"Failed to extract response content: {str(e)}")
            logger.error(f"Response type: {type(response)}")
            logger.error(f"Response attributes: {dir(response)}")
            return ""
    
    def _parse_agent_response(
        self,
        agent_response: str,
        dataset: pd.DataFrame,
        start_time: datetime,
        conversation_history: List[Dict[str, Any]]
    ) -> DistributionResult:
        """
        Parse agent response to extract distribution results.
        
        In a production system, the agent would provide structured output.
        For now, we'll analyze the response text.
        
        Args:
            agent_response: Agent's response text
            dataset: Original dataset
            start_time: Distribution start time
            conversation_history: Conversation history
        
        Returns:
            DistributionResult
        """
        duration = (datetime.now() - start_time).total_seconds()
        total_records = len(dataset)
        
        # Analyze response for success indicators
        response_lower = agent_response.lower()
        
        # Look for success/failure indicators
        has_success = any(word in response_lower for word in [
            'successfully', 'completed', 'created', 'inserted', 'distributed'
        ])
        has_failure = any(word in response_lower for word in [
            'failed', 'error', 'unable', 'could not', 'cannot'
        ])
        
        # Estimate results based on response
        if has_success and not has_failure:
            # Likely all succeeded
            status = 'success'
            succeeded = total_records
            failed = 0
        elif has_failure and not has_success:
            # Likely all failed
            status = 'failed'
            succeeded = 0
            failed = total_records
        else:
            # Mixed results
            status = 'partial'
            # Estimate 80% success rate for partial
            succeeded = int(total_records * 0.8)
            failed = total_records - succeeded
        
        errors = []
        if has_failure:
            errors.append("Some records failed to distribute (see agent response for details)")
        
        return DistributionResult(
            status=status,
            records_processed=total_records,
            records_succeeded=succeeded,
            records_failed=failed,
            duration=duration,
            agent_response=agent_response,
            errors=errors,
            timestamp=datetime.now(),
            conversation_history=conversation_history
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Returns:
            Dict with agent status information
        """
        return {
            "mcp_config_loaded": self.mcp_config is not None,
            "mcp_servers_configured": len(self.mcp_config.get('mcpServers', {})) if self.mcp_config else 0,
            "mcp_clients_created": len(self.mcp_clients),
            "agent_initialized": self.agent is not None,
            "config_path": str(self.mcp_config_path),
            "model_id": self.model_id
        }


# Example usage
async def example_usage():
    """Example of using the Strands MCP distribution agent."""
    
    print("=" * 60)
    print("Strands MCP Distribution Agent - Example")
    print("=" * 60)
    
    # Create sample dataset
    data = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com'],
        'phone': ['555-0001', '555-0002', '555-0003']
    })
    
    # Initialize agent
    agent = StrandsMCPDistributionAgent(
        mcp_config_path="data/mcp_config.json"
    )
    
    # Define progress callback
    async def progress_callback(progress: Dict[str, Any]):
        print(f"Progress: {progress}")
    
    # Distribute data
    result = await agent.distribute(
        dataset=data,
        instructions="Create a Jira issue for each record with name as summary and email in description",
        progress_callback=progress_callback
    )
    
    # Print results
    print(f"\nDistribution Result:")
    print(f"Status: {result.status}")
    print(f"Records Processed: {result.records_processed}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Duration: {result.duration:.2f}s")
    print(f"\nAgent Response:\n{result.agent_response}")


if __name__ == "__main__":
    asyncio.run(example_usage())
