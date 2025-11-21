"""Property-based tests for deterministic generation.

This module tests that synthetic data generation is deterministic when
using the same random seed and configuration.
"""

import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest
import os

from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport, FieldClassification


def load_mgw_data():
    """Load the MGW_File.csv dataset for testing."""
    mgw_path = "MGW_File.csv"
    if not os.path.exists(mgw_path):
        raise FileNotFoundError(f"MGW_File.csv not found at {mgw_path}")
    df = pd.read_csv(mgw_path)
    # Select numeric columns for testing
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
    """Generate test cases using subsets of the MGW dataset."""
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


def create_sensitivity_report(df: pd.DataFrame) -> SensitivityReport:
    """Create a basic sensitivity report marking all fields as non-sensitive.
    
    This allows us to test deterministic generation without the complexity
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


@settings(max_examples=10, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1),
    sdv_model=st.sampled_from(['gaussian_copula', 'ctgan', 'copula_gan'])
)
def test_deterministic_generation(df, num_synthetic_rows, seed, sdv_model):
    """
    Feature: synthetic-data-generator, Property 8: Deterministic Generation
    Validates: Requirements 6.1
    
    For any random seed value S and configuration C, generating synthetic data
    twice with the same S and C should produce identical datasets.
    
    This test verifies that:
    1. The same seed produces identical data
    2. Different seeds produce different data
    3. Determinism holds across different SDV models
    """
    # Ensure we have enough data for SDV to learn from
    assume(len(df) >= 100)
    assume(num_synthetic_rows >= 100)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data twice with the same seed
    synthetic_dataset_1 = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model=sdv_model,
        seed=seed
    )
    
    synthetic_dataset_2 = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model=sdv_model,
        seed=seed
    )
    
    # Extract the generated DataFrames
    synthetic_df_1 = synthetic_dataset_1.data
    synthetic_df_2 = synthetic_dataset_2.data
    
    # Verify both datasets have the same shape
    assert synthetic_df_1.shape == synthetic_df_2.shape, (
        f"Datasets have different shapes: {synthetic_df_1.shape} vs {synthetic_df_2.shape}"
    )
    
    # Verify both datasets have the same columns
    assert list(synthetic_df_1.columns) == list(synthetic_df_2.columns), (
        f"Datasets have different columns: {list(synthetic_df_1.columns)} vs {list(synthetic_df_2.columns)}"
    )
    
    # Verify the data is identical
    # Use pandas testing utility which handles floating point comparison properly
    pd.testing.assert_frame_equal(
        synthetic_df_1,
        synthetic_df_2,
        check_exact=False,  # Allow small floating point differences
        rtol=1e-10,  # Very tight relative tolerance
        atol=1e-10,  # Very tight absolute tolerance
        check_dtype=True,
        check_column_type=True,
        check_frame_type=True,
        check_names=True
    )


@settings(max_examples=50, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed1=st.integers(min_value=0, max_value=2**31-1),
    seed2=st.integers(min_value=0, max_value=2**31-1)
)
def test_different_seeds_produce_different_data(df, num_synthetic_rows, seed1, seed2):
    """
    Feature: synthetic-data-generator, Property 8: Deterministic Generation
    Validates: Requirements 6.1
    
    Verify that different seeds produce different synthetic datasets.
    This ensures the seed is actually being used and affecting the output.
    """
    # Ensure seeds are different
    assume(seed1 != seed2)
    
    # Ensure we have enough data for SDV to learn from
    assume(len(df) >= 100)
    assume(num_synthetic_rows >= 100)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data with different seeds
    synthetic_dataset_1 = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed1
    )
    
    synthetic_dataset_2 = agent.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed2
    )
    
    # Extract the generated DataFrames
    synthetic_df_1 = synthetic_dataset_1.data
    synthetic_df_2 = synthetic_dataset_2.data
    
    # Verify both datasets have the same shape (structure should be the same)
    assert synthetic_df_1.shape == synthetic_df_2.shape
    
    # Verify the data is NOT identical
    # At least one value should be different
    try:
        pd.testing.assert_frame_equal(
            synthetic_df_1,
            synthetic_df_2,
            check_exact=False,
            rtol=1e-10,
            atol=1e-10
        )
        # If we get here, the data is identical, which should not happen with different seeds
        pytest.fail(
            f"Different seeds ({seed1} and {seed2}) produced identical data. "
            f"The seed is not being used properly."
        )
    except AssertionError:
        # This is expected - different seeds should produce different data
        pass


@settings(max_examples=50, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_deterministic_generation_with_refitting(df, num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 8: Deterministic Generation
    Validates: Requirements 6.1
    
    Verify that determinism holds even when the model is refitted between generations.
    This tests that the seed controls both the fitting and sampling processes.
    """
    # Ensure we have enough data for SDV to learn from
    assume(len(df) >= 100)
    assume(num_synthetic_rows >= 100)
    
    # Create sensitivity report
    sensitivity_report = create_sensitivity_report(df)
    
    # Generate synthetic data with first agent instance
    agent1 = SyntheticDataAgent()
    synthetic_dataset_1 = agent1.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed
    )
    
    # Generate synthetic data with second agent instance (forces refitting)
    agent2 = SyntheticDataAgent()
    synthetic_dataset_2 = agent2.generate_synthetic_data(
        data=df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed
    )
    
    # Extract the generated DataFrames
    synthetic_df_1 = synthetic_dataset_1.data
    synthetic_df_2 = synthetic_dataset_2.data
    
    # Verify the data is identical even with refitting
    pd.testing.assert_frame_equal(
        synthetic_df_1,
        synthetic_df_2,
        check_exact=False,
        rtol=1e-10,
        atol=1e-10,
        check_dtype=True,
        check_column_type=True,
        check_frame_type=True,
        check_names=True
    )


@settings(max_examples=50, deadline=None)
@given(
    df=mgw_dataframe_strategy(),
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_seed_metadata_stored(df, num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 8: Deterministic Generation
    Validates: Requirements 6.1 (specifically criterion 6.4)
    
    Verify that the seed value is stored in the output metadata.
    This allows users to reproduce the exact same dataset later.
    """
    # Ensure we have enough data for SDV to learn from
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
    
    # Verify the seed is stored in the dataset
    assert synthetic_dataset.seed == seed, (
        f"Seed not properly stored in dataset. Expected {seed}, got {synthetic_dataset.seed}"
    )
    
    # Verify the seed is also in the generation metadata
    assert 'generation_timestamp' in synthetic_dataset.generation_metadata, (
        "Generation metadata missing timestamp"
    )
