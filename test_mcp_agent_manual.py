"""Manual test script for MCP Distribution Agent."""

import asyncio
import pandas as pd
import json
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from agents.distribution.mcp_agent import MCPDistributionAgent


async def test_agent():
    """Test the MCP distribution agent."""
    
    print("=" * 60)
    print("MCP Distribution Agent - Manual Test")
    print("=" * 60)
    
    # Create sample dataset
    print("\n1. Creating sample dataset...")
    data = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 
                  'diana@example.com', 'eve@example.com'],
        'phone': ['555-0001', '555-0002', '555-0003', '555-0004', '555-0005']
    })
    print(f"   ✓ Created dataset with {len(data)} records")
    print(f"   Columns: {list(data.columns)}")
    
    # Initialize agent
    print("\n2. Initializing MCP agent...")
    mcp_config_path = "data/mcp_config.json"
    
    # Create sample MCP config if it doesn't exist
    if not Path(mcp_config_path).exists():
        print(f"   Creating sample MCP config at {mcp_config_path}...")
        Path(mcp_config_path).parent.mkdir(parents=True, exist_ok=True)
        
        sample_config = {
            "mcpServers": {
                "jira": {
                    "command": "uvx",
                    "args": ["mcp-server-jira"],
                    "env": {
                        "JIRA_URL": "https://company.atlassian.net",
                        "JIRA_TOKEN": "xxx"
                    },
                    "disabled": False
                },
                "salesforce": {
                    "command": "uvx",
                    "args": ["mcp-server-salesforce"],
                    "env": {
                        "SF_INSTANCE": "https://company.salesforce.com",
                        "SF_TOKEN": "xxx"
                    },
                    "disabled": False
                },
                "postgres": {
                    "command": "uvx",
                    "args": ["mcp-server-postgres"],
                    "env": {
                        "DB_URL": "postgresql://localhost:5432/db"
                    },
                    "disabled": False
                }
            }
        }
        
        with open(mcp_config_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        print(f"   ✓ Created sample config")
    
    agent = MCPDistributionAgent(mcp_config_path=mcp_config_path)
    print(f"   ✓ Agent initialized")
    print(f"   Available servers: {agent.available_servers}")
    
    # Test tool discovery
    print("\n3. Discovering MCP tools...")
    tools = await agent.discover_tools()
    print(f"   ✓ Discovered tools from {len(tools)} servers:")
    for server, tool_list in tools.items():
        print(f"     - {server}: {len(tool_list)} tools")
        for tool in tool_list[:3]:  # Show first 3 tools
            print(f"       • {tool}")
        if len(tool_list) > 3:
            print(f"       ... and {len(tool_list) - 3} more")
    
    # Test distribution planning
    print("\n4. Creating distribution plan...")
    instructions = "Create a Jira issue for each record with name as summary and email in description"
    plan = await agent.plan_distribution(
        dataset=data,
        instructions=instructions
    )
    print(f"   ✓ Plan created with {len(plan['planned_steps'])} steps:")
    for step in plan['planned_steps']:
        print(f"     Step {step['step']}: {step['description']}")
        print(f"       Tool: {step['tool']} on server {step['server']}")
    
    # Test distribution execution
    print("\n5. Executing distribution...")
    print(f"   Instructions: {instructions}")
    
    # Track progress
    progress_updates = []
    
    async def progress_callback(progress):
        progress_updates.append(progress)
        if progress['records_processed'] % 2 == 0:  # Print every 2 records
            print(f"   Progress: {progress['records_processed']}/{progress['total_records']} records")
    
    result = await agent.distribute(
        dataset=data,
        instructions=instructions,
        progress_callback=progress_callback
    )
    
    # Print results
    print("\n6. Distribution Results:")
    print(f"   Status: {result.status.upper()}")
    print(f"   Records Processed: {result.records_processed}")
    print(f"   Records Succeeded: {result.records_succeeded}")
    print(f"   Records Failed: {result.records_failed}")
    print(f"   Success Rate: {result.success_rate:.1f}%")
    print(f"   Duration: {result.duration:.2f}s")
    print(f"   Progress Updates: {len(progress_updates)}")
    
    if result.agent_response:
        print(f"\n   Agent Response:")
        for line in result.agent_response.split('\n'):
            print(f"     {line}")
    
    if result.errors:
        print(f"\n   Errors ({len(result.errors)}):")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"     - {error}")
        if len(result.errors) > 5:
            print(f"     ... and {len(result.errors) - 5} more errors")
    
    # Test agent status
    print("\n7. Agent Status:")
    status = agent.get_status()
    print(f"   MCP Config Loaded: {status['mcp_config_loaded']}")
    print(f"   Available Servers: {len(status['available_servers'])}")
    print(f"   Config Path: {status['config_path']}")
    
    # Test tools summary
    print("\n8. Tools Summary:")
    summary = agent.get_tools_summary()
    print(summary)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent())
