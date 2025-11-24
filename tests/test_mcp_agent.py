"""Tests for MCP Distribution Agent."""

import asyncio
import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile

from agents.distribution.mcp_agent import (
    MCPDistributionAgent,
    MCPDistributionResult
)


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com'],
        'phone': ['555-0001', '555-0002', '555-0003']
    })


@pytest.fixture
def mcp_config_file():
    """Create a temporary MCP config file."""
    config = {
        "mcpServers": {
            "jira": {
                "command": "uvx",
                "args": ["mcp-server-jira"],
                "env": {
                    "JIRA_URL": "https://test.atlassian.net",
                    "JIRA_TOKEN": "test-token"
                },
                "disabled": False
            },
            "salesforce": {
                "command": "uvx",
                "args": ["mcp-server-salesforce"],
                "env": {
                    "SF_INSTANCE": "https://test.salesforce.com",
                    "SF_TOKEN": "test-token"
                },
                "disabled": False
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        return f.name


class TestMCPDistributionAgent:
    """Test suite for MCP Distribution Agent."""
    
    def test_agent_initialization(self, mcp_config_file):
        """Test agent initializes correctly."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        assert agent.mcp_config is not None
        assert len(agent.available_servers) == 2
        assert 'jira' in agent.available_servers
        assert 'salesforce' in agent.available_servers
    
    def test_agent_initialization_missing_config(self):
        """Test agent handles missing config gracefully."""
        agent = MCPDistributionAgent(mcp_config_path="nonexistent.json")
        
        assert agent.mcp_config == {"mcpServers": {}}
        assert len(agent.available_servers) == 0
    
    @pytest.mark.asyncio
    async def test_tool_discovery(self, mcp_config_file):
        """Test tool discovery from MCP servers."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        tools = await agent.discover_tools()
        
        assert 'jira' in tools
        assert 'salesforce' in tools
        assert 'create_issue' in tools['jira']
        assert 'create_lead' in tools['salesforce']
    
    @pytest.mark.asyncio
    async def test_distribution_planning(self, mcp_config_file, sample_dataset):
        """Test distribution plan creation."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        plan = await agent.plan_distribution(
            dataset=sample_dataset,
            instructions="Create Jira issues for each record"
        )
        
        assert 'dataset_info' in plan
        assert 'instructions' in plan
        assert 'available_tools' in plan
        assert 'planned_steps' in plan
        
        assert plan['dataset_info']['row_count'] == 3
        assert len(plan['dataset_info']['columns']) == 3
        assert len(plan['planned_steps']) > 0
    
    @pytest.mark.asyncio
    async def test_distribution_execution(self, mcp_config_file, sample_dataset):
        """Test full distribution execution."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        # Track progress updates
        progress_updates = []
        
        async def progress_callback(progress):
            progress_updates.append(progress)
        
        result = await agent.distribute(
            dataset=sample_dataset,
            instructions="Create Jira issues for each record",
            progress_callback=progress_callback
        )
        
        # Verify result
        assert isinstance(result, MCPDistributionResult)
        assert result.status in ['success', 'partial', 'failed']
        assert result.records_processed == 3
        assert result.duration > 0
        
        # Verify progress updates were called
        assert len(progress_updates) > 0
    
    @pytest.mark.asyncio
    async def test_distribution_empty_dataset(self, mcp_config_file):
        """Test distribution with empty dataset."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        empty_df = pd.DataFrame()
        
        result = await agent.distribute(
            dataset=empty_df,
            instructions="Create Jira issues"
        )
        
        assert result.status == 'failed'
        assert 'empty dataset' in result.agent_response.lower()
    
    @pytest.mark.asyncio
    async def test_distribution_no_instructions(self, mcp_config_file, sample_dataset):
        """Test distribution with no instructions."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        result = await agent.distribute(
            dataset=sample_dataset,
            instructions=""
        )
        
        assert result.status == 'failed'
        assert 'instructions' in result.agent_response.lower()
    
    @pytest.mark.asyncio
    async def test_distribution_no_tools(self, sample_dataset):
        """Test distribution with no MCP tools configured."""
        # Create empty config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"mcpServers": {}}, f)
            config_path = f.name
        
        agent = MCPDistributionAgent(mcp_config_path=config_path)
        
        result = await agent.distribute(
            dataset=sample_dataset,
            instructions="Create Jira issues"
        )
        
        assert result.status == 'failed'
        assert 'no mcp tools' in result.agent_response.lower()
    
    def test_tools_summary(self, mcp_config_file):
        """Test tools summary generation."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        # Manually set tools for testing
        agent.available_tools = {
            'jira': ['create_issue', 'update_issue'],
            'salesforce': ['create_lead']
        }
        
        summary = agent.get_tools_summary()
        
        assert 'jira' in summary
        assert 'salesforce' in summary
        assert 'create_issue' in summary
        assert 'create_lead' in summary
    
    def test_agent_status(self, mcp_config_file):
        """Test agent status reporting."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        status = agent.get_status()
        
        assert status['mcp_config_loaded'] is True
        assert len(status['available_servers']) == 2
        assert 'config_path' in status
    
    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, mcp_config_file, sample_dataset):
        """Test success rate calculation in results."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        result = await agent.distribute(
            dataset=sample_dataset,
            instructions="Create Jira issues"
        )
        
        # Success rate should be between 0 and 100
        assert 0 <= result.success_rate <= 100
        
        # If all succeeded, should be 100%
        if result.records_failed == 0:
            assert result.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_multi_step_distribution(self, mcp_config_file, sample_dataset):
        """Test distribution with multiple steps."""
        agent = MCPDistributionAgent(mcp_config_path=mcp_config_file)
        
        result = await agent.distribute(
            dataset=sample_dataset,
            instructions="Create Jira issues and Salesforce leads for each record"
        )
        
        # Should process records for both steps
        assert result.records_processed >= 3
        assert result.status in ['success', 'partial']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
