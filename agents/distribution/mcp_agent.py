"""MCP-based Distribution Agent using Strands framework."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MCPDistributionResult:
    """Result of MCP-based distribution."""
    status: str  # 'success', 'failed', 'partial'
    records_processed: int
    records_succeeded: int
    records_failed: int
    duration: float
    agent_response: str
    errors: List[str]
    timestamp: datetime
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.records_processed == 0:
            return 0.0
        return (self.records_succeeded / self.records_processed) * 100


class MCPDistributionAgent:
    """
    Intelligent distribution agent that uses MCP tools to distribute data.
    
    This agent:
    1. Loads MCP configuration to discover available tools
    2. Accepts natural language instructions from users
    3. Plans distribution strategy based on available MCP tools
    4. Executes distribution using appropriate MCP tools
    5. Reports progress and results
    
    Example usage:
        agent = MCPDistributionAgent(mcp_config_path="data/mcp_config.json")
        result = await agent.distribute(
            dataset=df,
            instructions="Create a Jira issue for each record with name as summary"
        )
    """
    
    def __init__(self, mcp_config_path: str):
        """
        Initialize MCP distribution agent.
        
        Args:
            mcp_config_path: Path to MCP configuration JSON file
        """
        self.mcp_config_path = Path(mcp_config_path)
        self.mcp_config: Optional[Dict[str, Any]] = None
        self.available_servers: List[str] = []
        self.available_tools: Dict[str, List[str]] = {}
        
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
            
            # Extract available servers
            servers = self.mcp_config.get('mcpServers', {})
            self.available_servers = [
                name for name, config in servers.items()
                if not config.get('disabled', False)
            ]
            
            logger.info(f"Loaded MCP config with {len(self.available_servers)} active servers")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {str(e)}")
            self.mcp_config = {"mcpServers": {}}
            self.available_servers = []
    
    async def discover_tools(self) -> Dict[str, List[str]]:
        """
        Discover available MCP tools from configured servers.
        
        This is a placeholder that would integrate with actual MCP toolkit.
        In production, this would:
        1. Connect to each MCP server
        2. Query available tools
        3. Return tool metadata
        
        Returns:
            Dict mapping server name to list of available tools
        """
        # TODO: Integrate with actual MCP toolkit to discover tools
        # For now, return mock data based on server names
        
        tools = {}
        for server_name in self.available_servers:
            if 'jira' in server_name.lower():
                tools[server_name] = [
                    'create_issue',
                    'update_issue',
                    'search_issues',
                    'add_comment'
                ]
            elif 'salesforce' in server_name.lower():
                tools[server_name] = [
                    'create_lead',
                    'create_contact',
                    'create_account',
                    'update_record',
                    'query_records'
                ]
            elif 'postgres' in server_name.lower() or 'database' in server_name.lower():
                tools[server_name] = [
                    'execute_query',
                    'insert_record',
                    'update_record',
                    'create_table'
                ]
            elif 's3' in server_name.lower():
                tools[server_name] = [
                    'upload_file',
                    'download_file',
                    'list_objects',
                    'delete_object'
                ]
            else:
                tools[server_name] = ['generic_tool']
        
        self.available_tools = tools
        return tools
    
    def get_tools_summary(self) -> str:
        """
        Get a human-readable summary of available MCP tools.
        
        Returns:
            Formatted string describing available tools
        """
        if not self.available_tools:
            return "No MCP tools available. Please configure MCP servers first."
        
        summary_lines = ["Available MCP Tools:"]
        for server, tools in self.available_tools.items():
            summary_lines.append(f"\n{server}:")
            for tool in tools:
                summary_lines.append(f"  - {tool}")
        
        return "\n".join(summary_lines)
    
    async def plan_distribution(
        self,
        dataset: pd.DataFrame,
        instructions: str
    ) -> Dict[str, Any]:
        """
        Plan distribution strategy based on instructions and available tools.
        
        This analyzes the user's instructions and creates an execution plan.
        
        Args:
            dataset: DataFrame to distribute
            instructions: Natural language instructions
        
        Returns:
            Distribution plan with steps and tool calls
        """
        # Discover available tools
        await self.discover_tools()
        
        # Create planning prompt
        plan = {
            "dataset_info": {
                "columns": list(dataset.columns),
                "row_count": len(dataset),
                "sample_data": dataset.head(3).to_dict(orient='records')
            },
            "instructions": instructions,
            "available_tools": self.available_tools,
            "planned_steps": []
        }
        
        # TODO: Use Strands agent to create intelligent plan
        # For now, create a simple plan based on keywords
        
        if 'jira' in instructions.lower():
            plan["planned_steps"].append({
                "step": 1,
                "action": "create_jira_issues",
                "tool": "create_issue",
                "server": next((s for s in self.available_servers if 'jira' in s.lower()), None),
                "description": "Create Jira issues for each record"
            })
        
        if 'salesforce' in instructions.lower():
            plan["planned_steps"].append({
                "step": len(plan["planned_steps"]) + 1,
                "action": "create_salesforce_records",
                "tool": "create_lead" if 'lead' in instructions.lower() else "create_contact",
                "server": next((s for s in self.available_servers if 'salesforce' in s.lower()), None),
                "description": "Create Salesforce records for each record"
            })
        
        if 'database' in instructions.lower() or 'postgres' in instructions.lower():
            plan["planned_steps"].append({
                "step": len(plan["planned_steps"]) + 1,
                "action": "insert_database_records",
                "tool": "insert_record",
                "server": next((s for s in self.available_servers if 'postgres' in s.lower() or 'database' in s.lower()), None),
                "description": "Insert records into database"
            })
        
        return plan
    
    async def distribute(
        self,
        dataset: pd.DataFrame,
        instructions: str,
        progress_callback: Optional[callable] = None
    ) -> MCPDistributionResult:
        """
        Distribute dataset according to natural language instructions.
        
        This is the main entry point for MCP-based distribution.
        
        Args:
            dataset: DataFrame with data to distribute
            instructions: Natural language instructions for distribution
            progress_callback: Optional callback for progress updates
        
        Returns:
            MCPDistributionResult with operation details
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            if dataset.empty:
                raise ValueError("Cannot distribute empty dataset")
            
            if not instructions or not instructions.strip():
                raise ValueError("Distribution instructions are required")
            
            # Discover available tools
            await self.discover_tools()
            
            if not self.available_tools:
                raise ValueError(
                    "No MCP tools available. Please configure MCP servers in the MCP Config page."
                )
            
            # Create distribution plan
            plan = await self.plan_distribution(dataset, instructions)
            
            logger.info(f"Distribution plan created with {len(plan['planned_steps'])} steps")
            
            # Execute distribution
            result = await self._execute_distribution(
                dataset=dataset,
                plan=plan,
                progress_callback=progress_callback
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            result.duration = duration
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Distribution failed: {str(e)}")
            
            return MCPDistributionResult(
                status='failed',
                records_processed=0,
                records_succeeded=0,
                records_failed=0,
                duration=duration,
                agent_response=f"Distribution failed: {str(e)}",
                errors=[str(e)],
                timestamp=datetime.now()
            )
    
    async def _execute_distribution(
        self,
        dataset: pd.DataFrame,
        plan: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> MCPDistributionResult:
        """
        Execute the distribution plan.
        
        Args:
            dataset: DataFrame to distribute
            plan: Distribution plan from plan_distribution()
            progress_callback: Optional callback for progress updates
        
        Returns:
            MCPDistributionResult
        """
        records_processed = 0
        records_succeeded = 0
        records_failed = 0
        errors = []
        agent_responses = []
        
        total_records = len(dataset)
        
        # Execute each step in the plan
        for step in plan['planned_steps']:
            step_num = step['step']
            action = step['action']
            tool = step['tool']
            server = step['server']
            
            logger.info(f"Executing step {step_num}: {action}")
            
            if progress_callback:
                await progress_callback({
                    "step": step_num,
                    "total_steps": len(plan['planned_steps']),
                    "action": action,
                    "records_processed": records_processed,
                    "total_records": total_records
                })
            
            # Process each record
            for idx, row in dataset.iterrows():
                try:
                    # TODO: Call actual MCP tool here
                    # For now, simulate the call
                    success = await self._call_mcp_tool(
                        server=server,
                        tool=tool,
                        data=row.to_dict()
                    )
                    
                    if success:
                        records_succeeded += 1
                    else:
                        records_failed += 1
                        errors.append(f"Failed to process record {idx}")
                    
                    records_processed += 1
                    
                    # Update progress
                    if progress_callback and records_processed % 10 == 0:
                        await progress_callback({
                            "step": step_num,
                            "total_steps": len(plan['planned_steps']),
                            "action": action,
                            "records_processed": records_processed,
                            "total_records": total_records,
                            "records_succeeded": records_succeeded,
                            "records_failed": records_failed
                        })
                    
                except Exception as e:
                    records_failed += 1
                    errors.append(f"Error processing record {idx}: {str(e)}")
                    logger.error(f"Error processing record {idx}: {str(e)}")
            
            agent_responses.append(f"Step {step_num} ({action}): Processed {records_processed} records")
        
        # Determine overall status
        if records_failed == 0:
            status = 'success'
        elif records_succeeded == 0:
            status = 'failed'
        else:
            status = 'partial'
        
        return MCPDistributionResult(
            status=status,
            records_processed=records_processed,
            records_succeeded=records_succeeded,
            records_failed=records_failed,
            duration=0.0,  # Will be set by caller
            agent_response="\n".join(agent_responses),
            errors=errors[:100],  # Limit to first 100 errors
            timestamp=datetime.now()
        )
    
    async def _call_mcp_tool(
        self,
        server: str,
        tool: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Call an MCP tool with the given data.
        
        This is a placeholder for actual MCP tool integration.
        
        Args:
            server: MCP server name
            tool: Tool name to call
            data: Data to pass to the tool
        
        Returns:
            True if successful, False otherwise
        """
        # TODO: Integrate with actual MCP toolkit
        # For now, simulate a successful call with some delay
        await asyncio.sleep(0.01)  # Simulate network delay
        
        # Simulate 95% success rate
        import random
        return random.random() < 0.95
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Returns:
            Dict with agent status information
        """
        return {
            "mcp_config_loaded": self.mcp_config is not None,
            "available_servers": self.available_servers,
            "available_tools": self.available_tools,
            "config_path": str(self.mcp_config_path)
        }


# Example usage
async def example_usage():
    """Example of using the MCP distribution agent."""
    
    # Create sample dataset
    data = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com'],
        'phone': ['555-0001', '555-0002', '555-0003']
    })
    
    # Initialize agent
    agent = MCPDistributionAgent(mcp_config_path="data/mcp_config.json")
    
    # Define progress callback
    async def progress_callback(progress: Dict[str, Any]):
        print(f"Progress: {progress['records_processed']}/{progress['total_records']} records")
    
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
    
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(example_usage())
