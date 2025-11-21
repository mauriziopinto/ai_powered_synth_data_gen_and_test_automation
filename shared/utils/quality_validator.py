"""Quality validation utilities for synthetic data."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from scipy.stats import wasserstein_distance
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

from shared.models.quality import QualityMetrics, QualityReport

logger = logging.getLogger(__name__)


class QualityValidator:
    """Validates quality of synthetic data against real data."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize quality validator.
        
        Args:
            output_dir: Directory for saving visualizations
        """
        self.output_dir = output_dir or Path('results/quality')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        edge_case_columns: Optional[List[str]] = None
    ) -> QualityReport:
        """Validate synthetic data quality.
        
        Args:
            real_data: Original production data
            synthetic_data: Generated synthetic data
            edge_case_columns: Columns that may contain edge cases
        
        Returns:
            QualityReport with metrics and visualizations
        """
        logger.info("Starting quality validation...")
        
        # Calculate metrics
        metrics = self._calculate_metrics(real_data, synthetic_data, edge_case_columns)
        
        # Generate visualizations
        visualizations = self._generate_visualizations(real_data, synthetic_data)
        metrics.visualizations = visualizations
        
        # Generate summaries
        real_summary = self._generate_data_summary(real_data, "Real")
        synthetic_summary = self._generate_data_summary(synthetic_data, "Synthetic")
        
        # Generate warnings and recommendations
        warnings = self._generate_warnings(metrics)
        recommendations = self._generate_recommendations(metrics, warnings)
        
        report = QualityReport(
            metrics=metrics,
            real_data_summary=real_summary,
            synthetic_data_summary=synthetic_summary,
            warnings=warnings,
            recommendations=recommendations
        )
        
        logger.info(f"Quality validation complete. Overall score: {metrics.sdv_quality_score:.3f}")
        return report
    
    def _calculate_metrics(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        edge_case_columns: Optional[List[str]] = None
    ) -> QualityMetrics:
        """Calculate all quality metrics."""
        
        # SDV quality score (simplified - in real implementation would use SDV library)
        sdv_score = self._calculate_sdv_score(real_data, synthetic_data)
        
        # Column shape similarity
        column_shapes = self._calculate_column_shapes(real_data, synthetic_data)
        
        # Column pair trends
        column_pair_trends = self._calculate_column_pair_trends(real_data, synthetic_data)
        
        # Statistical tests
        ks_tests = self._perform_ks_tests(real_data, synthetic_data)
        chi_squared_tests = self._perform_chi_squared_tests(real_data, synthetic_data)
        wasserstein_distances = self._calculate_wasserstein_distances(real_data, synthetic_data)
        
        # Correlation preservation
        correlation_preservation = self._calculate_correlation_preservation(real_data, synthetic_data)
        
        # Edge case frequency match
        edge_case_match = self._calculate_edge_case_frequency_match(
            real_data, synthetic_data, edge_case_columns or []
        )
        
        return QualityMetrics(
            sdv_quality_score=sdv_score,
            column_shapes=column_shapes,
            column_pair_trends=column_pair_trends,
            ks_tests=ks_tests,
            chi_squared_tests=chi_squared_tests,
            wasserstein_distances=wasserstein_distances,
            correlation_preservation=correlation_preservation,
            edge_case_frequency_match=edge_case_match
        )
    
    def _calculate_sdv_score(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> float:
        """Calculate overall SDV quality score.
        
        This is a simplified version. In production, would use SDV's evaluate_quality.
        """
        scores = []
        
        # Column shape similarity
        for col in real_data.columns:
            if col in synthetic_data.columns:
                if pd.api.types.is_numeric_dtype(real_data[col]):
                    # Compare distributions using KS test
                    _, pvalue = stats.ks_2samp(
                        real_data[col].dropna(),
                        synthetic_data[col].dropna()
                    )
                    scores.append(pvalue)
                else:
                    # Compare value distributions for categorical
                    real_dist = real_data[col].value_counts(normalize=True)
                    synth_dist = synthetic_data[col].value_counts(normalize=True)
                    
                    # Calculate overlap
                    common_values = set(real_dist.index) & set(synth_dist.index)
                    if common_values:
                        overlap = sum(min(real_dist.get(v, 0), synth_dist.get(v, 0)) 
                                    for v in common_values)
                        scores.append(overlap)
        
        return np.mean(scores) if scores else 0.0
    
    def _calculate_column_shapes(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate column shape similarity metrics."""
        shapes = {}
        
        for col in real_data.columns:
            if col not in synthetic_data.columns:
                continue
            
            # Skip boolean columns for numeric analysis
            if pd.api.types.is_bool_dtype(real_data[col]):
                # Treat as categorical
                real_unique = set(real_data[col].dropna().unique())
                synth_unique = set(synthetic_data[col].dropna().unique())
                
                shapes[col] = {
                    'unique_count_real': len(real_unique),
                    'unique_count_synthetic': len(synth_unique),
                    'overlap': len(real_unique & synth_unique),
                    'jaccard_similarity': len(real_unique & synth_unique) / len(real_unique | synth_unique)
                        if real_unique | synth_unique else 0.0
                }
            elif pd.api.types.is_numeric_dtype(real_data[col]):
                real_vals = real_data[col].dropna()
                synth_vals = synthetic_data[col].dropna()
                
                shapes[col] = {
                    'mean_diff': float(abs(real_vals.mean() - synth_vals.mean())),
                    'std_diff': float(abs(real_vals.std() - synth_vals.std())),
                    'min_diff': float(abs(real_vals.min() - synth_vals.min())),
                    'max_diff': float(abs(real_vals.max() - synth_vals.max()))
                }
            else:
                # Categorical column
                real_unique = set(real_data[col].dropna().unique())
                synth_unique = set(synthetic_data[col].dropna().unique())
                
                shapes[col] = {
                    'unique_count_real': len(real_unique),
                    'unique_count_synthetic': len(synth_unique),
                    'overlap': len(real_unique & synth_unique),
                    'jaccard_similarity': len(real_unique & synth_unique) / len(real_unique | synth_unique)
                        if real_unique | synth_unique else 0.0
                }
        
        return shapes
    
    def _calculate_column_pair_trends(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate column pair correlation trends."""
        trends = {}
        
        numeric_cols = real_data.select_dtypes(include=[np.number]).columns
        
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                if col1 in synthetic_data.columns and col2 in synthetic_data.columns:
                    real_corr = real_data[[col1, col2]].corr().iloc[0, 1]
                    synth_corr = synthetic_data[[col1, col2]].corr().iloc[0, 1]
                    
                    pair_key = f"{col1}_vs_{col2}"
                    trends[pair_key] = {
                        'real_correlation': real_corr,
                        'synthetic_correlation': synth_corr,
                        'difference': abs(real_corr - synth_corr)
                    }
        
        return trends
    
    def _perform_ks_tests(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """Perform Kolmogorov-Smirnov tests on numeric columns."""
        ks_tests = {}
        
        for col in real_data.select_dtypes(include=[np.number]).columns:
            if col in synthetic_data.columns:
                real_vals = real_data[col].dropna()
                synth_vals = synthetic_data[col].dropna()
                
                if len(real_vals) > 0 and len(synth_vals) > 0:
                    statistic, pvalue = stats.ks_2samp(real_vals, synth_vals)
                    ks_tests[col] = {
                        'statistic': float(statistic),
                        'pvalue': float(pvalue),
                        'passed': pvalue > 0.05  # Standard significance level
                    }
        
        return ks_tests
    
    def _perform_chi_squared_tests(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """Perform chi-squared tests on categorical columns."""
        chi_tests = {}
        
        for col in real_data.select_dtypes(include=['object', 'category']).columns:
            if col not in synthetic_data.columns:
                continue
            
            # Get value counts
            real_counts = real_data[col].value_counts()
            synth_counts = synthetic_data[col].value_counts()
            
            # Align indices
            all_values = sorted(set(real_counts.index) | set(synth_counts.index))
            real_freq = [real_counts.get(v, 0) for v in all_values]
            synth_freq = [synth_counts.get(v, 0) for v in all_values]
            
            # Normalize to same total
            real_freq = np.array(real_freq) / sum(real_freq) * sum(synth_freq)
            
            # Perform chi-squared test
            if len(all_values) > 1 and sum(synth_freq) > 0:
                try:
                    statistic, pvalue = stats.chisquare(synth_freq, real_freq)
                    chi_tests[col] = {
                        'statistic': float(statistic),
                        'pvalue': float(pvalue),
                        'passed': pvalue > 0.05
                    }
                except Exception as e:
                    logger.warning(f"Chi-squared test failed for {col}: {str(e)}")
        
        return chi_tests
    
    def _calculate_wasserstein_distances(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate Wasserstein distances for numeric columns."""
        distances = {}
        
        for col in real_data.select_dtypes(include=[np.number]).columns:
            if col in synthetic_data.columns:
                real_vals = real_data[col].dropna().values
                synth_vals = synthetic_data[col].dropna().values
                
                if len(real_vals) > 0 and len(synth_vals) > 0:
                    distance = wasserstein_distance(real_vals, synth_vals)
                    distances[col] = float(distance)
        
        return distances
    
    def _calculate_correlation_preservation(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> float:
        """Calculate how well correlations are preserved."""
        numeric_cols = list(set(real_data.select_dtypes(include=[np.number]).columns) & 
                          set(synthetic_data.select_dtypes(include=[np.number]).columns))
        
        if len(numeric_cols) < 2:
            return 1.0  # Perfect if no correlations to preserve
        
        real_corr = real_data[numeric_cols].corr()
        synth_corr = synthetic_data[numeric_cols].corr()
        
        # Calculate mean absolute difference
        corr_diff = np.abs(real_corr - synth_corr).values
        # Exclude diagonal (self-correlation)
        mask = ~np.eye(corr_diff.shape[0], dtype=bool)
        mean_diff = corr_diff[mask].mean()
        
        # Convert to similarity score (0-1, higher is better)
        return max(0.0, 1.0 - mean_diff)
    
    def _calculate_edge_case_frequency_match(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        edge_case_columns: List[str]
    ) -> float:
        """Calculate how well edge case frequencies match."""
        if not edge_case_columns:
            return 1.0  # Perfect if no edge cases to check
        
        matches = []
        
        for col in edge_case_columns:
            if col not in real_data.columns or col not in synthetic_data.columns:
                continue
            
            # Count null/empty values
            real_null_freq = real_data[col].isna().sum() / len(real_data)
            synth_null_freq = synthetic_data[col].isna().sum() / len(synthetic_data)
            
            # Calculate similarity (1 - absolute difference)
            similarity = 1.0 - abs(real_null_freq - synth_null_freq)
            matches.append(similarity)
        
        return np.mean(matches) if matches else 1.0
    
    def _generate_visualizations(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, str]:
        """Generate visualization plots."""
        visualizations = {}
        
        # Histogram comparisons for numeric columns
        numeric_cols = real_data.select_dtypes(include=[np.number]).columns[:4]  # Limit to 4
        if len(numeric_cols) > 0:
            hist_path = self._plot_histograms(real_data, synthetic_data, numeric_cols)
            visualizations['histograms'] = str(hist_path)
        
        # Correlation heatmaps
        if len(real_data.select_dtypes(include=[np.number]).columns) >= 2:
            corr_path = self._plot_correlation_heatmaps(real_data, synthetic_data)
            visualizations['correlation_heatmaps'] = str(corr_path)
        
        # Q-Q plots for numeric columns
        if len(numeric_cols) > 0:
            qq_path = self._plot_qq_plots(real_data, synthetic_data, numeric_cols[:2])
            visualizations['qq_plots'] = str(qq_path)
        
        return visualizations
    
    def _plot_histograms(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        columns: List[str]
    ) -> Path:
        """Plot histogram comparisons."""
        n_cols = len(columns)
        fig, axes = plt.subplots(1, n_cols, figsize=(5*n_cols, 4))
        if n_cols == 1:
            axes = [axes]
        
        for ax, col in zip(axes, columns):
            real_vals = real_data[col].dropna()
            synth_vals = synthetic_data[col].dropna()
            
            ax.hist(real_vals, bins=30, alpha=0.5, label='Real', density=True)
            ax.hist(synth_vals, bins=30, alpha=0.5, label='Synthetic', density=True)
            ax.set_xlabel(col)
            ax.set_ylabel('Density')
            ax.legend()
            ax.set_title(f'{col} Distribution')
        
        plt.tight_layout()
        path = self.output_dir / 'histograms.png'
        plt.savefig(path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return path
    
    def _plot_correlation_heatmaps(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Path:
        """Plot correlation heatmaps."""
        numeric_cols = list(set(real_data.select_dtypes(include=[np.number]).columns) & 
                          set(synthetic_data.select_dtypes(include=[np.number]).columns))
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Real data correlation
        real_corr = real_data[numeric_cols].corr()
        sns.heatmap(real_corr, annot=True, fmt='.2f', cmap='coolwarm', 
                   center=0, ax=ax1, cbar_kws={'label': 'Correlation'})
        ax1.set_title('Real Data Correlations')
        
        # Synthetic data correlation
        synth_corr = synthetic_data[numeric_cols].corr()
        sns.heatmap(synth_corr, annot=True, fmt='.2f', cmap='coolwarm',
                   center=0, ax=ax2, cbar_kws={'label': 'Correlation'})
        ax2.set_title('Synthetic Data Correlations')
        
        plt.tight_layout()
        path = self.output_dir / 'correlation_heatmaps.png'
        plt.savefig(path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return path
    
    def _plot_qq_plots(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        columns: List[str]
    ) -> Path:
        """Plot Q-Q plots."""
        n_cols = len(columns)
        fig, axes = plt.subplots(1, n_cols, figsize=(5*n_cols, 4))
        if n_cols == 1:
            axes = [axes]
        
        for ax, col in zip(axes, columns):
            real_vals = real_data[col].dropna().values
            synth_vals = synthetic_data[col].dropna().values
            
            # Calculate quantiles
            quantiles = np.linspace(0, 1, min(len(real_vals), len(synth_vals), 100))
            real_quantiles = np.quantile(real_vals, quantiles)
            synth_quantiles = np.quantile(synth_vals, quantiles)
            
            ax.scatter(real_quantiles, synth_quantiles, alpha=0.5)
            
            # Add diagonal line
            min_val = min(real_quantiles.min(), synth_quantiles.min())
            max_val = max(real_quantiles.max(), synth_quantiles.max())
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect match')
            
            ax.set_xlabel(f'Real {col}')
            ax.set_ylabel(f'Synthetic {col}')
            ax.set_title(f'Q-Q Plot: {col}')
            ax.legend()
        
        plt.tight_layout()
        path = self.output_dir / 'qq_plots.png'
        plt.savefig(path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return path
    
    def _generate_data_summary(
        self,
        data: pd.DataFrame,
        label: str
    ) -> Dict[str, Any]:
        """Generate summary statistics for data."""
        return {
            'label': label,
            'rows': len(data),
            'columns': len(data.columns),
            'numeric_columns': len(data.select_dtypes(include=[np.number]).columns),
            'categorical_columns': len(data.select_dtypes(include=['object', 'category']).columns),
            'missing_values': int(data.isna().sum().sum()),
            'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024 / 1024
        }
    
    def _generate_warnings(self, metrics: QualityMetrics) -> List[str]:
        """Generate warnings based on metrics."""
        warnings = []
        
        # Check overall quality
        if metrics.sdv_quality_score < 0.7:
            warnings.append(
                f"Overall quality score is low ({metrics.sdv_quality_score:.3f}). "
                "Consider using a different synthesis method or adjusting parameters."
            )
        
        # Check correlation preservation
        if metrics.correlation_preservation < 0.8:
            warnings.append(
                f"Correlation preservation is low ({metrics.correlation_preservation:.3f}). "
                "Relationships between variables may not be well preserved."
            )
        
        # Check KS tests
        failed_ks = [col for col, result in metrics.ks_tests.items() 
                    if not result.get('passed', True)]
        if failed_ks:
            warnings.append(
                f"KS test failed for {len(failed_ks)} columns: {', '.join(failed_ks[:3])}. "
                "Distributions may differ significantly from real data."
            )
        
        # Check chi-squared tests
        failed_chi = [col for col, result in metrics.chi_squared_tests.items()
                     if not result.get('passed', True)]
        if failed_chi:
            warnings.append(
                f"Chi-squared test failed for {len(failed_chi)} columns: {', '.join(failed_chi[:3])}. "
                "Categorical distributions may differ from real data."
            )
        
        return warnings
    
    def _generate_recommendations(
        self,
        metrics: QualityMetrics,
        warnings: List[str]
    ) -> List[str]:
        """Generate recommendations based on metrics and warnings."""
        recommendations = []
        
        if metrics.sdv_quality_score < 0.7:
            recommendations.append(
                "Try using CTGAN or CopulaGAN instead of GaussianCopula for better quality."
            )
            recommendations.append(
                "Increase the number of training epochs for the synthesizer."
            )
        
        if metrics.correlation_preservation < 0.8:
            recommendations.append(
                "Use a copula-based method (GaussianCopula or CopulaGAN) to better preserve correlations."
            )
        
        if len(warnings) == 0:
            recommendations.append(
                "Quality metrics look good! Synthetic data is ready for use."
            )
        
        return recommendations
