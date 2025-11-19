"""Data quality and synthetic dataset models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd


@dataclass
class QualityMetrics:
    """Quality metrics for synthetic data."""
    sdv_quality_score: float
    column_shapes_score: float
    column_pair_trends_score: float
    ks_tests: Dict[str, Dict[str, float]]
    correlation_preservation: float
    edge_case_frequency_match: float
    
    # Per-field metrics
    field_scores: Dict[str, float] = field(default_factory=dict)
    
    # Visualizations (stored as file paths or base64)
    distribution_plots: Dict[str, str] = field(default_factory=dict)
    correlation_heatmaps: Dict[str, str] = field(default_factory=dict)
    qq_plots: Dict[str, str] = field(default_factory=dict)


@dataclass
class SyntheticDataset:
    """Generated synthetic dataset with metadata."""
    data: pd.DataFrame
    quality_metrics: QualityMetrics
    generation_metadata: Dict[str, Any]
    timestamp: datetime
    seed: Optional[int] = None
    num_records: int = 0
    
    def __post_init__(self):
        """Calculate num_records from data."""
        if self.num_records == 0:
            self.num_records = len(self.data)
