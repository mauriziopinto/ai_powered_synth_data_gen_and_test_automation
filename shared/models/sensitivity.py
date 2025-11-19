"""Sensitivity analysis models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class FieldClassification:
    """Classification result for a single field."""
    field_name: str
    is_sensitive: bool
    sensitivity_type: str  # 'name', 'email', 'phone', 'ssn', 'address', etc.
    confidence: float
    reasoning: str
    recommended_strategy: str
    confluence_references: List[str] = field(default_factory=list)
    pattern_matches: List[str] = field(default_factory=list)


@dataclass
class SensitivityReport:
    """Complete sensitivity analysis report."""
    classifications: Dict[str, FieldClassification]
    data_profile: Dict[str, Any]
    timestamp: datetime
    total_fields: int
    sensitive_fields: int
    confidence_distribution: Dict[str, int]  # 'high', 'medium', 'low' counts
    
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
