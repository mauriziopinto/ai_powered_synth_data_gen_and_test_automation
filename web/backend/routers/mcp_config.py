"""MCP configuration API endpoints."""

import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from shared.models.mcp_config import MCPConfig, MCPConfigUpdate
from shared.storage.mcp_storage import mcp_storage

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/config")
async def get_mcp_config():
    """Get current MCP configuration."""
    config = mcp_storage.load()
    
    if not config:
        # Return empty config if none exists
        return {"mcpServers": {}}
    
    return config.model_dump()


@router.post("/config")
async def save_mcp_config(config_update: MCPConfigUpdate):
    """Save MCP configuration."""
    try:
        # Parse JSON string
        config_dict = json.loads(config_update.config)
        
        # Validate structure
        config = MCPConfig(**config_dict)
        
        # Save to disk
        mcp_storage.save(config)
        
        return {
            "success": True,
            "message": "MCP configuration saved successfully",
            "servers_count": len(config.mcpServers)
        }
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}"
        )


@router.delete("/config")
async def delete_mcp_config():
    """Delete MCP configuration."""
    success = mcp_storage.delete()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MCP configuration found"
        )
    
    return {
        "success": True,
        "message": "MCP configuration deleted"
    }


@router.post("/validate")
async def validate_mcp_config(config_update: MCPConfigUpdate):
    """Validate MCP configuration without saving."""
    try:
        # Parse JSON string
        config_dict = json.loads(config_update.config)
        
        # Validate structure
        config = MCPConfig(**config_dict)
        
        return {
            "valid": True,
            "servers_count": len(config.mcpServers),
            "servers": list(config.mcpServers.keys())
        }
    
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Invalid configuration: {str(e)}"
        }


@router.get("/servers")
async def list_mcp_servers():
    """List configured MCP servers."""
    config = mcp_storage.load()
    
    if not config:
        return {"servers": []}
    
    servers = []
    for name, server_config in config.mcpServers.items():
        servers.append({
            "name": name,
            "command": server_config.command,
            "disabled": server_config.disabled,
            "has_env": len(server_config.env) > 0
        })
    
    return {"servers": servers}
