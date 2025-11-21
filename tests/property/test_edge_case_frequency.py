"""Property-based tests for edge case frequency matching.

This module tests that edge cases are injected at the specified frequency
within the configured tolerance threshold.
"""

import numpy as np
import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest

from shared.utils.edge_case_generator import (
    EdgeCaseGenerator,
    EdgeCaseRule,
    EdgeCaseType,
    EdgeCasePatternLibrary
)


@composite
def dataframe_with_fields_strategy(draw):
    """Generate DataFrames with various field types for edge case testing."""
    # Generate number of rows (minimum 100 for meaningful frequency testing)
    num_rows = draw(st.integers(min_value=100, max_value=1000))
    
    # Generate different field types
    data = {}
    
    # Email field
    data['email'] = [f'user{i}@example.com' for i in range(num_rows)]
    
    # Phone field
    data['phone'] = [f'555-{i:04d}' for i in range(num_rows)]
    
    # Postcode field
    data['postcode'] = [f'{i:05d}' for i in range(num_rows)]
    
    # Numeric fields
    data['age'] = np.random.randint(18, 80, num_rows)
    data['balance'] = np.random.uniform(0, 10000, num_rows).round(2)
    
    # String field
    data['name'] = [f'Customer {i}' for i in range(num_rows)]
    
    return pd.DataFrame(data)


@composite
def edge_case_rule_strategy(draw):
    """Generate valid EdgeCaseRule configurations."""
    # Choose a field name
    field_name = draw(st.sampled_from(['email', 'phone', 'postcode', 'age', 'balance', 'name']))
    
    # Map field names to appropriate edge case types
    field_type_mapping = {
        'email': {
            'types': [EdgeCaseType.MALFORMED_EMAIL, EdgeCaseType.EMPTY_STRING, EdgeCaseType.NULL_VALUE],
            'field_type': 'email'
        },
        'phone': {
            'types': [EdgeCaseType.MALFORMED_PHONE, EdgeCaseType.NULL_VALUE],
            'field_type': 'phone'
        },
        'postcode': {
            'types': [EdgeCaseType.INVALID_POSTCODE, EdgeCaseType.EMPTY_STRING],
            'field_type': 'postcode'
        },
        'age': {
            'types': [EdgeCaseType.NEGATIVE_VALUE, EdgeCaseType.ZERO_VALUE, EdgeCaseType.BOUNDARY_VALUE],
            'field_type': 'number'
        },
        'balance': {
            'types': [EdgeCaseType.NEGATIVE_VALUE, EdgeCaseType.ZERO_VALUE],
            'field_type': 'number'
        },
        'name': {
            'types': [EdgeCaseType.EMPTY_STRING, EdgeCaseType.WHITESPACE_ONLY, EdgeCaseType.SPECIAL_CHARACTERS],
            'field_type': 'string'
        }
    }
    
    mapping = field_type_mapping[field_name]
    
    # Choose 1-3 edge case types
    num_types = draw(st.integers(min_value=1, max_value=min(3, len(mapping['types']))))
    edge_case_types = draw(st.lists(
        st.sampled_from(mapping['types']),
        min_size=num_types,
        max_size=num_types,
        unique=True
    ))
    
    # Choose frequency between 0.01 (1%) and 0.30 (30%)
    # This range is realistic for edge case testing
    frequency = draw(st.floats(min_value=0.01, max_value=0.30))
    
    return EdgeCaseRule(
        field_name=field_name,
        edge_case_types=edge_case_types,
        frequency=frequency,
        field_type=mapping['field_type']
    )


@settings(max_examples=50, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    rule=edge_case_rule_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_frequency_matching_single_rule(df, rule, seed):
    """
    Feature: synthetic-data-generator, Property 5: Edge Case Frequency Matching
    Validates: Requirements 3.1
    
    For any edge-case generation rule with specified frequency F,
    the actual frequency of edge cases in generated data should be
    within ±5% of F.
    
    This test verifies that when a single edge case rule is applied,
    the actual frequency of injected edge cases matches the target
    frequency within the tolerance threshold.
    """
    # Ensure the field exists in the DataFrame
    assume(rule.field_name in df.columns)
    
    # Ensure we have enough rows for meaningful frequency testing
    # With 100 rows and 1% frequency, we expect at least 1 edge case
    assume(len(df) >= 100)
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=[rule],
        seed=seed
    )
    
    # Calculate expected number of edge cases
    expected_count = int(len(df) * rule.frequency)
    actual_count = injection_result.injected_count
    
    # Calculate actual frequency
    actual_frequency = injection_result.frequency_achieved
    target_frequency = rule.frequency
    
    # Tolerance is ±5% as specified in the property
    tolerance = 0.05
    
    # Check that frequency is within tolerance
    frequency_deviation = abs(actual_frequency - target_frequency)
    
    assert frequency_deviation <= tolerance, (
        f"Edge case frequency deviation {frequency_deviation:.4f} exceeds tolerance {tolerance:.4f}. "
        f"Target frequency: {target_frequency:.4f}, Actual frequency: {actual_frequency:.4f}. "
        f"Expected ~{expected_count} edge cases, got {actual_count} in {len(df)} records."
    )


@settings(max_examples=50, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    rules=st.lists(edge_case_rule_strategy(), min_size=2, max_size=4, unique_by=lambda r: r.field_name),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_frequency_matching_multiple_rules(df, rules, seed):
    """
    Feature: synthetic-data-generator, Property 5: Edge Case Frequency Matching
    Validates: Requirements 3.1
    
    For any set of edge-case generation rules, each rule's frequency
    should be independently maintained within ±5% tolerance.
    
    This test verifies that when multiple edge case rules are applied
    to different fields, each field's edge case frequency matches its
    target frequency within the tolerance threshold.
    """
    # Filter rules to only include fields that exist in the DataFrame
    valid_rules = [rule for rule in rules if rule.field_name in df.columns]
    
    # Ensure we have at least 2 valid rules
    assume(len(valid_rules) >= 2)
    
    # Ensure we have enough rows for meaningful frequency testing
    assume(len(df) >= 100)
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=valid_rules,
        seed=seed
    )
    
    # Tolerance is ±5% as specified in the property
    tolerance = 0.05
    
    # Check frequency for each field independently
    for rule in valid_rules:
        field_name = rule.field_name
        
        # Count how many records have edge cases for this specific field
        field_edge_case_count = sum(
            1 for idx in injection_result.injected_indices
            if any(tag['field'] == field_name for tag in result_df.at[idx, '_edge_case_tags'])
        )
        
        # Calculate actual frequency for this field
        field_actual_frequency = field_edge_case_count / len(df)
        field_target_frequency = rule.frequency
        
        # Check that frequency is within tolerance
        field_frequency_deviation = abs(field_actual_frequency - field_target_frequency)
        
        assert field_frequency_deviation <= tolerance, (
            f"Field '{field_name}' edge case frequency deviation {field_frequency_deviation:.4f} "
            f"exceeds tolerance {tolerance:.4f}. "
            f"Target frequency: {field_target_frequency:.4f}, "
            f"Actual frequency: {field_actual_frequency:.4f}. "
            f"Expected ~{int(len(df) * field_target_frequency)} edge cases, "
            f"got {field_edge_case_count} in {len(df)} records."
        )


@settings(max_examples=50, deadline=None)
@given(
    num_rows=st.integers(min_value=100, max_value=1000),
    frequency=st.floats(min_value=0.01, max_value=0.30),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_frequency_matching_various_frequencies(num_rows, frequency, seed):
    """
    Feature: synthetic-data-generator, Property 5: Edge Case Frequency Matching
    Validates: Requirements 3.1
    
    For any specified frequency F across different dataset sizes,
    the actual frequency of edge cases should be within ±5% of F.
    
    This test verifies that the frequency matching property holds
    across various combinations of dataset sizes and target frequencies.
    """
    # Create a simple DataFrame
    df = pd.DataFrame({
        'email': [f'user{i}@example.com' for i in range(num_rows)],
        'value': np.random.randint(0, 100, num_rows)
    })
    
    # Create a rule with the specified frequency
    rule = EdgeCaseRule(
        field_name='email',
        edge_case_types=[EdgeCaseType.MALFORMED_EMAIL, EdgeCaseType.EMPTY_STRING],
        frequency=frequency,
        field_type='email'
    )
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=[rule],
        seed=seed
    )
    
    # Calculate actual frequency
    actual_frequency = injection_result.frequency_achieved
    target_frequency = frequency
    
    # Tolerance is ±5% as specified in the property
    tolerance = 0.05
    
    # Check that frequency is within tolerance
    frequency_deviation = abs(actual_frequency - target_frequency)
    
    assert frequency_deviation <= tolerance, (
        f"Edge case frequency deviation {frequency_deviation:.4f} exceeds tolerance {tolerance:.4f}. "
        f"Target frequency: {target_frequency:.4f}, Actual frequency: {actual_frequency:.4f}. "
        f"Dataset size: {num_rows} rows, Expected ~{int(num_rows * target_frequency)} edge cases, "
        f"got {injection_result.injected_count}."
    )


@settings(max_examples=50, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    frequency=st.floats(min_value=0.05, max_value=0.20),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_frequency_matching_with_validation(df, frequency, seed):
    """
    Feature: synthetic-data-generator, Property 5: Edge Case Frequency Matching
    Validates: Requirements 3.1
    
    For any edge-case generation rule, the validate_frequency method
    should correctly identify when the achieved frequency is within
    the ±5% tolerance.
    
    This test verifies that the built-in validation method correctly
    validates frequency matching.
    """
    # Ensure we have enough rows
    assume(len(df) >= 100)
    
    # Create a rule
    rule = EdgeCaseRule(
        field_name='email',
        edge_case_types=[EdgeCaseType.MALFORMED_EMAIL],
        frequency=frequency,
        field_type='email'
    )
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=[rule],
        seed=seed
    )
    
    # Validate frequency using the built-in method
    tolerance = 0.05
    is_valid = generator.validate_frequency(
        result=injection_result,
        target_frequency=frequency,
        tolerance=tolerance
    )
    
    # Calculate actual deviation
    actual_deviation = abs(injection_result.frequency_achieved - frequency)
    
    # The validation result should match whether deviation is within tolerance
    expected_valid = actual_deviation <= tolerance
    
    assert is_valid == expected_valid, (
        f"Validation result {is_valid} does not match expected {expected_valid}. "
        f"Target frequency: {frequency:.4f}, Actual frequency: {injection_result.frequency_achieved:.4f}, "
        f"Deviation: {actual_deviation:.4f}, Tolerance: {tolerance:.4f}"
    )
    
    # If valid, the deviation should be within tolerance
    if is_valid:
        assert actual_deviation <= tolerance, (
            f"Validation passed but deviation {actual_deviation:.4f} exceeds tolerance {tolerance:.4f}"
        )


@settings(max_examples=30, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_frequency_matching_extreme_frequencies(df, seed):
    """
    Feature: synthetic-data-generator, Property 5: Edge Case Frequency Matching
    Validates: Requirements 3.1
    
    For edge case rules with very low (1%) or high (30%) frequencies,
    the actual frequency should still be within ±5% tolerance.
    
    This test verifies that frequency matching works at the extremes
    of the realistic frequency range.
    """
    # Ensure we have enough rows
    assume(len(df) >= 200)  # Need more rows for extreme frequencies
    
    # Test both low and high frequencies
    frequencies = [0.01, 0.30]  # 1% and 30%
    
    tolerance = 0.05
    
    for target_frequency in frequencies:
        # Create a rule
        rule = EdgeCaseRule(
            field_name='email',
            edge_case_types=[EdgeCaseType.MALFORMED_EMAIL],
            frequency=target_frequency,
            field_type='email'
        )
        
        # Create edge case generator
        generator = EdgeCaseGenerator()
        
        # Inject edge cases
        result_df, injection_result = generator.inject_edge_cases(
            data=df,
            rules=[rule],
            seed=seed
        )
        
        # Calculate actual frequency
        actual_frequency = injection_result.frequency_achieved
        
        # Check that frequency is within tolerance
        frequency_deviation = abs(actual_frequency - target_frequency)
        
        assert frequency_deviation <= tolerance, (
            f"Extreme frequency test failed for target {target_frequency:.2%}. "
            f"Deviation {frequency_deviation:.4f} exceeds tolerance {tolerance:.4f}. "
            f"Actual frequency: {actual_frequency:.4f}. "
            f"Expected ~{int(len(df) * target_frequency)} edge cases, "
            f"got {injection_result.injected_count} in {len(df)} records."
        )
