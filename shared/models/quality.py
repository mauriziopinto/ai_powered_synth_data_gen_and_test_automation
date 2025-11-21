"""Quality metrics data models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd


@dataclass
class QualityMetrics:
    """Quality metrics for synthetic data."""
    
    # Overall quality score (0-1)
    sdv_quality_score: float
    
    # Column-level metrics
    column_shapes: Dict[str, Any] = field(default_factory=dict)
    column_pair_trends: Dict[str, Any] = field(default_factory=dict)
    
    # Aggregate scores (for backward compatibility)
    column_shapes_score: float = 0.0
    column_pair_trends_score: float = 0.0
    
    # Field-level scores
    field_scores: Dict[str, float] = field(default_factory=dict)
    
    # Statistical tests
    ks_tests: Dict[str, Dict[str, float]] = field(default_factory=dict)
    chi_squared_tests: Dict[str, Dict[str, float]] = field(default_factory=dict)
    wasserstein_distances: Dict[str, float] = field(default_factory=dict)
    
    # Correlation preservation (0-1, higher is better)
    correlation_preservation: float = 0.0
    
    # Edge case frequency match (0-1, higher is better)
    edge_case_frequency_match: float = 0.0
    
    # Column order preservation
    column_order_preserved: bool = True
    column_order_report: Dict[str, Any] = field(default_factory=dict)
    
    # Diagnostic metrics
    data_validity_score: float = 0.0
    data_structure_score: float = 0.0
    diagnostic_details: Dict[str, Any] = field(default_factory=dict)
    
    # Privacy/Data Leakage metrics
    nearest_neighbor_distances: Dict[str, float] = field(default_factory=dict)
    
    # Timestamp
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Visualization paths
    visualizations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'sdv_quality_score': self.sdv_quality_score,
            'column_shapes': self.column_shapes,
            'column_pair_trends': self.column_pair_trends,
            'ks_tests': self.ks_tests,
            'chi_squared_tests': self.chi_squared_tests,
            'wasserstein_distances': self.wasserstein_distances,
            'correlation_preservation': self.correlation_preservation,
            'edge_case_frequency_match': self.edge_case_frequency_match,
            'column_order_preserved': self.column_order_preserved,
            'column_order_report': self.column_order_report,
            'data_validity_score': self.data_validity_score,
            'data_structure_score': self.data_structure_score,
            'diagnostic_details': self.diagnostic_details,
            'nearest_neighbor_distances': self.nearest_neighbor_distances,
            'generated_at': self.generated_at.isoformat(),
            'visualizations': self.visualizations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityMetrics':
        """Create from dictionary."""
        data = data.copy()
        if 'generated_at' in data and isinstance(data['generated_at'], str):
            data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            f"Overall Quality Score: {self.sdv_quality_score:.3f}",
            f"Correlation Preservation: {self.correlation_preservation:.3f}",
            f"Edge Case Frequency Match: {self.edge_case_frequency_match:.3f}",
            f"Column Order Preserved: {'Yes' if self.column_order_preserved else 'No'}",
            f"",
            f"Statistical Tests:",
            f"  KS Tests: {len(self.ks_tests)} columns",
            f"  Chi-Squared Tests: {len(self.chi_squared_tests)} columns",
            f"  Wasserstein Distances: {len(self.wasserstein_distances)} columns"
        ]
        return "\n".join(lines)


@dataclass
class QualityReport:
    """Complete quality report with metrics and visualizations."""
    
    metrics: QualityMetrics
    real_data_summary: Dict[str, Any] = field(default_factory=dict)
    synthetic_data_summary: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metrics': self.metrics.to_dict(),
            'real_data_summary': self.real_data_summary,
            'synthetic_data_summary': self.synthetic_data_summary,
            'warnings': self.warnings,
            'recommendations': self.recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityReport':
        """Create from dictionary."""
        data = data.copy()
        if 'metrics' in data:
            data['metrics'] = QualityMetrics.from_dict(data['metrics'])
        return cls(**data)


@dataclass
class SyntheticDataset:
    """Represents a generated synthetic dataset."""
    
    data: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Optional[QualityMetrics] = None
    generated_at: datetime = field(default_factory=datetime.now)
    generation_method: str = "unknown"
    seed: Optional[int] = None
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    num_records: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding data)."""
        return {
            'metadata': self.metadata,
            'quality_metrics': self.quality_metrics.to_dict() if self.quality_metrics else None,
            'generated_at': self.generated_at.isoformat(),
            'generation_method': self.generation_method,
            'seed': self.seed,
            'row_count': len(self.data),
            'column_count': len(self.data.columns)
        }
