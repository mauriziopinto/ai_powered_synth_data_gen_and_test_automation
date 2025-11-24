"""MCP configuration models."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MCPServer(BaseModel):
    """MCP server configuration."""
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    disabled: bool = False


class MCPConfig(BaseModel):
    """Complete MCP configuration."""
    mcpServers: Dict[str, MCPServer] = Field(default_factory=dict)


class MCPConfigUpdate(BaseModel):
    """Request to update MCP configuration."""
    config: str  # JSON string of the config
