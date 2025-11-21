"""Sensitivity analysis models."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


@dataclass
class FieldClassification:
    """Classification result for a single field."""
    field_name: str
    is_sensitive: bool
    sensitivity_type: str  # 'name', 'email', 'phone', 'ssn', 'address', etc.
    confidence: float
    reasoning: str
    recommended_strategy: str
    data_type: Optional[str] = None  # User-friendly data type: 'string', 'integer', 'float', 'boolean', 'date'
    confluence_references: List[str] = field(default_factory=list)
    pattern_matches: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldClassification':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SensitivityReport:
    """Complete sensitivity analysis report."""
    classifications: Dict[str, FieldClassification]
    data_profile: Dict[str, Any]
    timestamp: datetime
    total_fields: int
    sensitive_fields: int
    confidence_distribution: Dict[str, int]  # 'high', 'medium', 'low' counts
    column_order: List[str] = field(default_factory=list)  # Ordered list of column names
    
    def get_sensitive_fields(self) -> List[str]:
        """Get list of sensitive field names."""
        return [
            name for name, classification in self.classifications.items()
            if classification.is_sensitive
        ]
    
    def get_non_sensitive_fields(self) -> List[str]:
        """Get list of non-sensitive field names."""
        return [
            name for name, classification in self.classifications.items()
            if not classification.is_sensitive
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'classifications': {
                name: classification.to_dict()
                for name, classification in self.classifications.items()
            },
            'data_profile': self.data_profile,
            'timestamp': self.timestamp.isoformat(),
            'total_fields': self.total_fields,
            'sensitive_fields': self.sensitive_fields,
            'confidence_distribution': self.confidence_distribution,
            'column_order': self.column_order
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SensitivityReport':
        """Create from dictionary."""
        # Convert classification dicts to FieldClassification objects
        classifications = {
            name: FieldClassification.from_dict(classification)
            for name, classification in data['classifications'].items()
        }
        
        # Convert ISO string to datetime
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        
        return cls(
            classifications=classifications,
            data_profile=data['data_profile'],
            timestamp=timestamp,
            total_fields=data['total_fields'],
            sensitive_fields=data['sensitive_fields'],
            confidence_distribution=data['confidence_distribution'],
            column_order=data.get('column_order', [])  # Default to empty list for backward compatibility
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SensitivityReport':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
