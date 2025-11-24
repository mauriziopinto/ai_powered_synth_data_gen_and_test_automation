"""File-based storage for targets."""

import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from shared.models.target import Target, TargetCreate, TargetUpdate


class TargetStorage:
    """Manages target persistence to disk."""
    
    def __init__(self, storage_dir: str = "data/targets"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_target_path(self, target_id: str) -> Path:
        """Get file path for a target."""
        return self.storage_dir / f"{target_id}.json"
    
    def create(self, target_create: TargetCreate) -> Target:
        """Create a new target."""
        target = Target(
            id=str(uuid.uuid4()),
            name=target_create.name,
            type=target_create.type,
            config=target_create.config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to disk
        target_path = self._get_target_path(target.id)
        with open(target_path, 'w') as f:
            json.dump(target.model_dump(mode='json'), f, indent=2, default=str)
        
        return target
    
    def get(self, target_id: str) -> Optional[Target]:
        """Get a target by ID."""
        target_path = self._get_target_path(target_id)
        
        if not target_path.exists():
            return None
        
        with open(target_path, 'r') as f:
            data = json.load(f)
            return Target(**data)
    
    def list(self, active_only: bool = True) -> List[Target]:
        """List all targets."""
        targets = []
        
        for target_file in self.storage_dir.glob("*.json"):
            with open(target_file, 'r') as f:
                data = json.load(f)
                target = Target(**data)
                
                if not active_only or target.is_active:
                    targets.append(target)
        
        # Sort by created_at descending
        targets.sort(key=lambda x: x.created_at, reverse=True)
        return targets
    
    def update(self, target_id: str, target_update: TargetUpdate) -> Optional[Target]:
        """Update a target."""
        target = self.get(target_id)
        
        if not target:
            return None
        
        # Update fields
        if target_update.name is not None:
            target.name = target_update.name
        if target_update.config is not None:
            target.config = target_update.config
        if target_update.is_active is not None:
            target.is_active = target_update.is_active
        
        target.updated_at = datetime.utcnow()
        
        # Save to disk
        target_path = self._get_target_path(target_id)
        with open(target_path, 'w') as f:
            json.dump(target.model_dump(mode='json'), f, indent=2, default=str)
        
        return target
    
    def delete(self, target_id: str) -> bool:
        """Delete a target."""
        target_path = self._get_target_path(target_id)
        
        if not target_path.exists():
            return False
        
        target_path.unlink()
        return True


# Global instance
target_storage = TargetStorage()
