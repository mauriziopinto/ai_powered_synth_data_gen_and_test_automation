"""Storage for MCP configuration."""

import json
from pathlib import Path
from typing import Optional

from shared.models.mcp_config import MCPConfig


class MCPConfigStorage:
    """Manages MCP configuration persistence."""
    
    def __init__(self, config_path: str = "data/mcp_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, config: MCPConfig) -> None:
        """Save MCP configuration."""
        with open(self.config_path, 'w') as f:
            json.dump(config.model_dump(), f, indent=2)
    
    def load(self) -> Optional[MCPConfig]:
        """Load MCP configuration."""
        if not self.config_path.exists():
            return None
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            return MCPConfig(**data)
    
    def exists(self) -> bool:
        """Check if configuration exists."""
        return self.config_path.exists()
    
    def delete(self) -> bool:
        """Delete MCP configuration."""
        if self.config_path.exists():
            self.config_path.unlink()
            return True
        return False


# Global instance
mcp_storage = MCPConfigStorage()
