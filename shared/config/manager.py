"""Configuration management for saving, loading, and sharing workflow configurations."""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationMetadata:
    """Metadata for a workflow configuration."""
    config_id: str
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'config_id': self.config_id,
            'name': self.name,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationMetadata':
        """Create from dictionary."""
        return cls(
            config_id=data['config_id'],
            name=data['name'],
            description=data['description'],
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            created_by=data.get('created_by', 'system'),
            version=data.get('version', '1.0')
        )


@dataclass
class WorkflowConfiguration:
    """Complete workflow configuration."""
    metadata: ConfigurationMetadata
    schema_definition: Dict[str, Any]
    generation_parameters: Dict[str, Any]
    edge_case_rules: Dict[str, Any]
    target_system_settings: Dict[str, Any]
    additional_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metadata': self.metadata.to_dict(),
            'schema_definition': self.schema_definition,
            'generation_parameters': self.generation_parameters,
            'edge_case_rules': self.edge_case_rules,
            'target_system_settings': self.target_system_settings,
            'additional_settings': self.additional_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowConfiguration':
        """Create from dictionary."""
        return cls(
            metadata=ConfigurationMetadata.from_dict(data['metadata']),
            schema_definition=data['schema_definition'],
            generation_parameters=data['generation_parameters'],
            edge_case_rules=data['edge_case_rules'],
            target_system_settings=data['target_system_settings'],
            additional_settings=data.get('additional_settings', {})
        )
    
    def validate(self) -> List[str]:
        """Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate metadata
        if not self.metadata.config_id:
            errors.append("Configuration ID is required")
        if not self.metadata.name:
            errors.append("Configuration name is required")
        
        # Validate schema definition
        if not self.schema_definition:
            errors.append("Schema definition is required")
        elif 'tables' not in self.schema_definition and 'fields' not in self.schema_definition:
            errors.append("Schema must contain 'tables' or 'fields'")
        
        # Validate generation parameters
        if not self.generation_parameters:
            errors.append("Generation parameters are required")
        elif 'num_records' not in self.generation_parameters:
            errors.append("Generation parameters must specify 'num_records'")
        
        # Validate target system settings
        if not self.target_system_settings:
            errors.append("Target system settings are required")
        elif 'type' not in self.target_system_settings:
            errors.append("Target system must specify 'type'")
        
        return errors


class ConfigurationManager:
    """Manages workflow configuration save/load operations."""
    
    def __init__(self, config_dir: str = "configs"):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory for storing configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized configuration manager: {config_dir}")

    def generate_config_id(self) -> str:
        """Generate unique configuration ID.
        
        Returns:
            Unique configuration ID
        """
        return f"config_{uuid.uuid4().hex[:12]}"
    
    def save(self, config: WorkflowConfiguration) -> str:
        """Save workflow configuration.
        
        Args:
            config: Configuration to save
        
        Returns:
            Configuration ID
        """
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        # Update timestamp
        config.metadata.updated_at = datetime.now()
        
        # Save to file
        config_file = self.config_dir / f"{config.metadata.config_id}.json"
        with open(config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        logger.info(f"Saved configuration: {config.metadata.config_id}")
        return config.metadata.config_id
    
    def load(self, config_id: str) -> WorkflowConfiguration:
        """Load workflow configuration.
        
        Args:
            config_id: Configuration ID to load
        
        Returns:
            Loaded configuration
        """
        config_file = self.config_dir / f"{config_id}.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration not found: {config_id}")
        
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        config = WorkflowConfiguration.from_dict(data)
        
        # Validate loaded configuration
        errors = config.validate()
        if errors:
            logger.warning(f"Loaded configuration has validation errors: {', '.join(errors)}")
        
        logger.info(f"Loaded configuration: {config_id}")
        return config
    
    def delete(self, config_id: str) -> None:
        """Delete workflow configuration.
        
        Args:
            config_id: Configuration ID to delete
        """
        config_file = self.config_dir / f"{config_id}.json"
        
        if config_file.exists():
            config_file.unlink()
            logger.info(f"Deleted configuration: {config_id}")
        else:
            logger.warning(f"Configuration not found for deletion: {config_id}")

    def export_config(self, config_id: str, export_path: str) -> None:
        """Export configuration to file.
        
        Args:
            config_id: Configuration ID to export
            export_path: Path to export file
        """
        config = self.load(config_id)
        
        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        logger.info(f"Exported configuration {config_id} to {export_path}")
    
    def import_config(self, import_path: str, new_name: Optional[str] = None) -> str:
        """Import configuration from file.
        
        Args:
            import_path: Path to import file
            new_name: Optional new name for imported config
        
        Returns:
            New configuration ID
        """
        import_file = Path(import_path)
        
        if not import_file.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")
        
        with open(import_file, 'r') as f:
            data = json.load(f)
        
        config = WorkflowConfiguration.from_dict(data)
        
        # Generate new ID for imported config
        old_id = config.metadata.config_id
        config.metadata.config_id = self.generate_config_id()
        config.metadata.created_at = datetime.now()
        config.metadata.updated_at = datetime.now()
        
        if new_name:
            config.metadata.name = new_name
        
        # Save imported config
        new_id = self.save(config)
        
        logger.info(f"Imported configuration from {import_path} as {new_id}")
        return new_id
    
    def list_configs(self) -> List[ConfigurationMetadata]:
        """List all saved configurations.
        
        Returns:
            List of configuration metadata
        """
        configs = []
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                metadata = ConfigurationMetadata.from_dict(data['metadata'])
                configs.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to load config {config_file}: {str(e)}")
        
        # Sort by updated_at descending
        configs.sort(key=lambda c: c.updated_at, reverse=True)
        
        return configs



class ConfigurationLibrary:
    """Library interface for browsing and searching configurations."""
    
    def __init__(self, manager: ConfigurationManager):
        """Initialize configuration library.
        
        Args:
            manager: Configuration manager instance
        """
        self.manager = manager
    
    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> List[ConfigurationMetadata]:
        """Search configurations.
        
        Args:
            query: Search query for name/description
            tags: Filter by tags
            created_by: Filter by creator
        
        Returns:
            List of matching configurations
        """
        all_configs = self.manager.list_configs()
        results = []
        
        for config in all_configs:
            # Filter by query
            if query:
                query_lower = query.lower()
                if (query_lower not in config.name.lower() and 
                    query_lower not in config.description.lower()):
                    continue
            
            # Filter by tags
            if tags:
                if not any(tag in config.tags for tag in tags):
                    continue
            
            # Filter by creator
            if created_by:
                if config.created_by != created_by:
                    continue
            
            results.append(config)
        
        return results
    
    def get_by_tag(self, tag: str) -> List[ConfigurationMetadata]:
        """Get configurations by tag.
        
        Args:
            tag: Tag to filter by
        
        Returns:
            List of configurations with the tag
        """
        return self.search(tags=[tag])
    
    def get_recent(self, limit: int = 10) -> List[ConfigurationMetadata]:
        """Get recently updated configurations.
        
        Args:
            limit: Maximum number to return
        
        Returns:
            List of recent configurations
        """
        all_configs = self.manager.list_configs()
        return all_configs[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics.
        
        Returns:
            Statistics dictionary
        """
        all_configs = self.manager.list_configs()
        
        # Collect all tags
        all_tags = set()
        creators = set()
        
        for config in all_configs:
            all_tags.update(config.tags)
            creators.add(config.created_by)
        
        return {
            'total_configs': len(all_configs),
            'unique_tags': len(all_tags),
            'unique_creators': len(creators),
            'tags': sorted(list(all_tags)),
            'creators': sorted(list(creators))
        }
