"""Property-based tests for statistical property preservation.

This module tests that synthetic data maintains statistical properties
of the source data within configurable tolerance thresholds.
"""

import numpy as np
import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from scipy.stats import ks_2samp, chi2_contingency
import pytest
import os

from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport, FieldClassification


# Custom strategies for generating test data using MGW dataset
def load_mgw_data():
    """Load the MGW_File.csv dataset for testing."""
    mgw_path = "MGW_File.csv"
    if not os.path.exists(mgw_path):
        raise FileNotFoundError(f"MGW_File.csv not found at {mgw_path}")
    df = pd.read_csv(mgw_path)
    # Select numeric columns for statistical testing
    numeric_columns = ['session_duration', 'data_usage_mb', 'user_id', 'location_id', 
                      'signal_strength', 'battery_level']
    # Ensure all selected columns exist and are numeric
    available_numeric = []
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if not df[col].isna().all():
                available_numeric.append(col)
    if len(available_numeric) < 2:
        raise ValueError("Need at least 2 numeric columns for testing")
    return df[available_numeric].dropna()

@composite
def mgw_dataframe_strategy(draw):
    """Generate test cases using subsets of the MGW dataset.
    This uses real data which should be much more realistic for SDV to learn from.
    """
    # Load the full MGW dataset
    full_df = load_mgw_data()
    # Choose a random subset size (minimum 100 rows for good SDV performance)
    min_rows = min(100, len(full_df))
    max_rows = len(full_df)
    num_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    # Choose a random subset of columns (minimum 2)
    available_columns = list(full_df.columns)
    num_columns = draw(st.integers(min_value=2, max_value=len(available_columns)))
    selected_columns = draw(st.lists(
        st.sampled_from(available_columns), 
        min_size=num_columns, 
        max_size=num_columns,
        unique=True
    ))
    # Sample random rows
    if num_rows < len(full_df):
        sampled_df = full_df[selected_columns].sample(n=num_rows, random_state=42)
    else:
        sampled_df = full_df[selected_columns]
    return sampled_df.reset_index(drop=True)


@composite
def mgw_mixed_dataframe_strategy(draw):
    """Generate test cases using mixed numeric and categorical columns from MGW dataset."""
    # Load the full MGW dataset
    mgw_path = "MGW_File.csv"
    if not os.path.exists(mgw_path):
        raise FileNotFoundError(f"MGW_File.csv not found at {mgw_path}")
    df = pd.read_csv(mgw_path)
    # Define numeric and categorical columns
    numeric_columns = ['session_duration', 'data_usage_mb', 'user_id', 'location_id', 
                      'signal_strength', 'battery_level']
    categorical_columns = ['device_type', 'network_type', 'app_category']
    # Ensure numeric columns are properly typed
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # Select available columns
    available_numeric = [col for col in numeric_columns if col in df.columns and not df[col].isna().all()]
    available_categorical = [col for col in categorical_columns if col in df.columns]
    if len(available_numeric) < 2 or len(available_categorical) < 1:
        raise ValueError("Need at least 2 numeric and 1 categorical column")
    # Choose subset of columns
    num_numeric = draw(st.integers(min_value=2, max_value=len(available_numeric)))
    num_categorical = draw(st.integers(min_value=1, max_value=len(available_categorical)))
    selected_numeric = draw(st.lists(
        st.sampled_from(available_numeric), 
        min_size=num_numeric, 
        max_size=num_numeric,
        unique=True
    ))
    selected_categorical = draw(st.lists(
        st.sampled_from(available_categorical), 
        min_size=num_categorical, 
        max_size=num_categorical,
        unique=True
    ))
    selected_columns = selected_numeric + selected_categorical
    result_df = df[selected_columns].dropna()
    # Choose subset of rows
    min_rows = min(100, len(result_df))
    max_rows = len(result_df)
    num_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    if num_rows < len(result_df):
        result_df = result_df.sample(n=num_rows, random_state=42)
    return result_df.reset_index(drop=True)


def create_sensitivity_report(df: pd.DataFrame) -> SensitivityReport:
    """Create a basic sensitivity report marking all fields as non-sensitive.
    
    This allows us to test the statistical preservation without the complexity
    of sensitive field handling.
    """
    classifications = {}
    for column in df.columns:
        classifications[column] = FieldClassification(
            field_name=column,
            is_sensitive=False,
            sensitivity_type='none',
            confidence=1.0,
            reasoning='Test data - marked as non-sensitive',
            recommended_strategy='sdv',
            confluence_references=[]
        )
    
    return SensitivityReport(
        classifications=classifications,
        data_profile={},
        timestamp=pd.Timestamp.now(),
        total_fields=len(df.columns),
        sensitive_fields=0,
        confidence_distribution={}
    )


@settings(max_examples=20, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_statistical_property_preservation_ks_test(df, seed):
    """
    Feature: synthetic-data-generator, Property 1: Statistical Property Preservation
    Validates: Requirements 1.2
    
    For any production dataset with measurable statistical properties,
    when synthetic data is generated, the statistical distance between
    production and synthetic data should be within the configured tolerance threshold.
    
    This test uses the Kolmogorov-Smirnov test to verify that distributions
    are preserved within the tolerance threshold.
    
    For small datasets (50-200 rows), we use a tolerance of 0.35 which is
    realistic given the statistical variance inherent in synthetic data generation.
    """
    # Ensure we have enough data for meaningful statistical tests
    # SDV needs at least 100 rows to learn distributions well
    assume(len(df) >= 100)
    
    # Generate same number of synthetic rows as source data
    # This ensures we're testing distribution preservation, not sample size effects
    num_synthetic_rows = len(df)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed
    )
    
    synthetic_df = synthetic_dataset.data
    
    # Verify we got the requested number of rows
    assert len(synthetic_df) == num_synthetic_rows
    
    # For each numeric column, perform KS test
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    # Use realistic tolerance for KS test
    # KS statistic measures maximum distance between CDFs
    # 0.3 is a reasonable threshold for synthetic data
    tolerance = 0.3
    
    for column in numeric_columns:
        if column not in synthetic_df.columns:
            continue
        
        real_values = df[column].dropna()
        synth_values = synthetic_df[column].dropna()
        
        # Skip if insufficient data
        if len(real_values) < 10 or len(synth_values) < 10:
            continue
        
        # Perform KS test
        statistic, pvalue = ks_2samp(real_values, synth_values)
        
        # The KS statistic should be within tolerance
        # Lower statistic means distributions are more similar
        assert statistic <= tolerance, (
            f"Column '{column}' KS statistic {statistic:.4f} exceeds tolerance {tolerance:.4f}. "
            f"This indicates the distributions differ significantly."
        )


@settings(max_examples=20, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_statistical_property_preservation_mean_std(df, seed):
    """
    Feature: synthetic-data-generator, Property 1: Statistical Property Preservation
    Validates: Requirements 1.2
    
    For any production dataset, the mean and standard deviation of numeric columns
    in synthetic data should be within the tolerance threshold of the original data.
    
    Uses adaptive tolerance and absolute differences for near-zero means to avoid
    instability in relative error calculations.
    """
    # Ensure we have enough data
    # SDV needs at least 100 rows to learn distributions well
    assume(len(df) >= 100)
    
    # Generate same number of synthetic rows as source data
    num_synthetic_rows = len(df)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed
    )
    
    synthetic_df = synthetic_dataset.data
    
    # For each numeric column, check mean and std
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    # Use realistic tolerance for mean/std preservation
    # 20% relative difference is reasonable for synthetic data
    tolerance = 0.2
    
    for column in numeric_columns:
        if column not in synthetic_df.columns:
            continue
        
        real_values = df[column].dropna()
        synth_values = synthetic_df[column].dropna()
        
        # Skip if insufficient data
        if len(real_values) < 10 or len(synth_values) < 10:
            continue
        
        real_mean = real_values.mean()
        synth_mean = synth_values.mean()
        real_std = real_values.std()
        synth_std = synth_values.std()
        
        # Skip if std is too small (near-constant column)
        if real_std < 1e-6:
            continue
        
        # For mean: use absolute difference if real_mean is near zero
        # Otherwise use relative difference
        if abs(real_mean) < 1.0:
            # Use absolute difference for near-zero means
            mean_diff = abs(synth_mean - real_mean)
            mean_threshold = real_std * tolerance  # Scale by std
        else:
            # Use relative difference for larger means
            mean_diff = abs(synth_mean - real_mean) / abs(real_mean)
            mean_threshold = tolerance
        
        # For std: always use relative difference
        std_diff = abs(synth_std - real_std) / real_std
        
        # Mean and std should be within tolerance
        assert mean_diff <= mean_threshold, (
            f"Column '{column}' mean difference {mean_diff:.4f} exceeds threshold {mean_threshold:.4f}. "
            f"Real mean: {real_mean:.4f}, Synthetic mean: {synth_mean:.4f}"
        )
        
        assert std_diff <= tolerance, (
            f"Column '{column}' std difference {std_diff:.4f} exceeds tolerance {tolerance:.4f}. "
            f"Real std: {real_std:.4f}, Synthetic std: {synth_std:.4f}"
        )


@settings(max_examples=20, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_statistical_property_preservation_correlation(df, num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 1: Statistical Property Preservation
    Validates: Requirements 1.2
    
    For any production dataset with correlated columns, the correlations
    in synthetic data should be preserved within the tolerance threshold.
    
    Uses adaptive tolerance based on dataset size - smaller datasets have
    more variance in correlation estimates.
    """
    # Ensure we have enough data and columns for correlation
    # SDV needs at least 100 rows to learn distributions well
    assume(len(df) >= 100)
    assume(num_synthetic_rows >= 100)
    assume(len(df.columns) >= 2)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed
    )
    
    synthetic_df = synthetic_dataset.data
    
    # Get numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    common_numeric = [col for col in numeric_columns if col in synthetic_df.columns]
    
    # Need at least 2 columns for correlation
    assume(len(common_numeric) >= 2)
    
    # Calculate correlation matrices
    real_corr = df[common_numeric].corr()
    synth_corr = synthetic_df[common_numeric].corr()
    
    # Calculate absolute differences in correlations
    corr_diff = np.abs(real_corr - synth_corr)
    
    # Remove diagonal (self-correlation)
    np.fill_diagonal(corr_diff.values, 0)
    
    # Get upper triangle (avoid counting each pair twice)
    upper_triangle_indices = np.triu_indices_from(corr_diff.values, k=1)
    correlation_differences = corr_diff.values[upper_triangle_indices]
    
    # Use realistic tolerance for correlation preservation
    # Correlations can vary more in synthetic data
    tolerance = 0.3
    
    # Check that all pairwise correlations are within tolerance
    max_corr_diff = correlation_differences.max()
    
    assert max_corr_diff <= tolerance, (
        f"Maximum correlation difference {max_corr_diff:.4f} exceeds tolerance {tolerance:.4f}. "
        f"Correlations are not well preserved."
    )


@settings(max_examples=20, deadline=None)
@given(
    df=mgw_mixed_dataframe_strategy(),
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_statistical_property_preservation_categorical_distribution(df, num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 1: Statistical Property Preservation
    Validates: Requirements 1.2
    
    For any production dataset with categorical columns, the category distributions
    in synthetic data should be similar to the original data.
    """
    # Ensure we have enough data
    # SDV needs at least 100 rows to learn distributions well
    assume(len(df) >= 100)
    assume(num_synthetic_rows >= 100)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed
    )
    
    synthetic_df = synthetic_dataset.data
    
    # For each categorical column, check distribution
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    
    for column in categorical_columns:
        if column not in synthetic_df.columns:
            continue
        
        # Get value counts (normalized)
        real_dist = df[column].value_counts(normalize=True).sort_index()
        synth_dist = synthetic_df[column].value_counts(normalize=True).sort_index()
        
        # Ensure both have the same categories
        all_categories = set(real_dist.index) | set(synth_dist.index)
        
        # Skip if too few categories
        if len(all_categories) < 2:
            continue
        
        # Reindex to have same categories (fill missing with 0)
        real_dist = real_dist.reindex(all_categories, fill_value=0)
        synth_dist = synth_dist.reindex(all_categories, fill_value=0)
        
        # Calculate chi-squared statistic manually
        # (chi2_contingency requires contingency table)
        # We'll use a simpler metric: max absolute difference in proportions
        max_diff = np.abs(real_dist - synth_dist).max()
        
        # Allow up to 20% difference in category proportions
        # This is reasonable for synthetic data
        tolerance = 0.2
        
        assert max_diff <= tolerance, (
            f"Column '{column}' has category distribution difference {max_diff:.4f} "
            f"exceeding tolerance {tolerance:.4f}. "
            f"Real distribution: {real_dist.to_dict()}, "
            f"Synthetic distribution: {synth_dist.to_dict()}"
        )


@settings(max_examples=20, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_statistical_property_preservation_sdv_quality_score(df, num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 1: Statistical Property Preservation
    Validates: Requirements 1.2
    
    For any production dataset, the SDV quality score should indicate
    good statistical similarity (score >= 0.5 for reasonable quality).
    """
    # Ensure we have enough data
    # SDV needs at least 100 rows to learn distributions well
    assume(len(df) >= 100)
    assume(num_synthetic_rows >= 100)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed
    )
    
    # Check SDV quality score
    quality_score = synthetic_dataset.quality_metrics.sdv_quality_score
    
    # SDV quality score should be at least 0.5 for reasonable quality
    # Lower threshold accounts for randomness in small datasets
    min_quality_score = 0.5
    
    assert quality_score >= min_quality_score, (
        f"SDV quality score {quality_score:.4f} is below minimum threshold {min_quality_score:.4f}. "
        f"This indicates poor statistical similarity between real and synthetic data."
    )
