"""Property-based tests for edge case tagging completeness.

This module tests that all edge cases injected into synthetic data
are properly tagged with appropriate metadata identifying the anomaly type.
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
    # Generate number of rows (minimum 50 for meaningful testing)
    num_rows = draw(st.integers(min_value=50, max_value=500))
    
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
    
    # Date field
    data['signup_date'] = pd.date_range('2020-01-01', periods=num_rows, freq='D')
    
    return pd.DataFrame(data)


@composite
def edge_case_rule_strategy(draw):
    """Generate valid EdgeCaseRule configurations."""
    # Choose a field name
    field_name = draw(st.sampled_from(['email', 'phone', 'postcode', 'age', 'balance', 'name', 'signup_date']))
    
    # Map field names to appropriate edge case types
    field_type_mapping = {
        'email': {
            'types': [EdgeCaseType.MALFORMED_EMAIL, EdgeCaseType.EMPTY_STRING, EdgeCaseType.NULL_VALUE],
            'field_type': 'email'
        },
        'phone': {
            'types': [EdgeCaseType.MALFORMED_PHONE, EdgeCaseType.NULL_VALUE, EdgeCaseType.EMPTY_STRING],
            'field_type': 'phone'
        },
        'postcode': {
            'types': [EdgeCaseType.INVALID_POSTCODE, EdgeCaseType.EMPTY_STRING, EdgeCaseType.NULL_VALUE],
            'field_type': 'postcode'
        },
        'age': {
            'types': [EdgeCaseType.NEGATIVE_VALUE, EdgeCaseType.ZERO_VALUE, EdgeCaseType.BOUNDARY_VALUE, EdgeCaseType.NULL_VALUE],
            'field_type': 'number'
        },
        'balance': {
            'types': [EdgeCaseType.NEGATIVE_VALUE, EdgeCaseType.ZERO_VALUE, EdgeCaseType.NULL_VALUE],
            'field_type': 'number'
        },
        'name': {
            'types': [EdgeCaseType.EMPTY_STRING, EdgeCaseType.WHITESPACE_ONLY, EdgeCaseType.SPECIAL_CHARACTERS, EdgeCaseType.NULL_VALUE],
            'field_type': 'string'
        },
        'signup_date': {
            'types': [EdgeCaseType.INVALID_DATE, EdgeCaseType.FUTURE_DATE, EdgeCaseType.PAST_DATE, EdgeCaseType.NULL_VALUE],
            'field_type': 'date'
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
    
    # Choose frequency between 0.05 (5%) and 0.30 (30%)
    frequency = draw(st.floats(min_value=0.05, max_value=0.30))
    
    return EdgeCaseRule(
        field_name=field_name,
        edge_case_types=edge_case_types,
        frequency=frequency,
        field_type=mapping['field_type']
    )


@settings(max_examples=100, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    rule=edge_case_rule_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_tagging_completeness_single_rule(df, rule, seed):
    """
    Feature: synthetic-data-generator, Property 6: Edge Case Tagging Completeness
    Validates: Requirements 3.3
    
    For any generated dataset with injected edge cases, all edge-case records
    should have appropriate tags identifying the anomaly type.
    
    This test verifies that when edge cases are injected, every injected
    edge case is properly tagged with metadata including field name, edge case type,
    and description.
    """
    # Ensure the field exists in the DataFrame
    assume(rule.field_name in df.columns)
    
    # Ensure we have enough rows for meaningful testing
    assume(len(df) >= 50)
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=[rule],
        seed=seed,
        tag_column='_edge_case_tags'
    )
    
    # Verify that the tag column exists
    assert '_edge_case_tags' in result_df.columns, (
        "Tag column '_edge_case_tags' not found in result DataFrame"
    )
    
    # For each injected index, verify that tags exist and are complete
    for idx in injection_result.injected_indices:
        tags = result_df.at[idx, '_edge_case_tags']
        
        # Tags should be a list
        assert isinstance(tags, list), (
            f"Tags at index {idx} should be a list, got {type(tags)}"
        )
        
        # Tags should not be empty
        assert len(tags) > 0, (
            f"Tags at index {idx} should not be empty for an injected edge case"
        )
        
        # Each tag should be a dictionary with required fields
        for tag in tags:
            assert isinstance(tag, dict), (
                f"Tag at index {idx} should be a dictionary, got {type(tag)}"
            )
            
            # Verify required fields exist
            assert 'field' in tag, (
                f"Tag at index {idx} missing 'field' key: {tag}"
            )
            assert 'type' in tag, (
                f"Tag at index {idx} missing 'type' key: {tag}"
            )
            assert 'description' in tag, (
                f"Tag at index {idx} missing 'description' key: {tag}"
            )
            
            # Verify field name matches the rule
            assert tag['field'] == rule.field_name, (
                f"Tag at index {idx} has incorrect field name: "
                f"expected '{rule.field_name}', got '{tag['field']}'"
            )
            
            # Verify type is a valid EdgeCaseType value
            assert tag['type'] in [ect.value for ect in EdgeCaseType], (
                f"Tag at index {idx} has invalid edge case type: '{tag['type']}'"
            )
            
            # Verify type is one of the types specified in the rule
            assert tag['type'] in [ect.value for ect in rule.edge_case_types], (
                f"Tag at index {idx} has edge case type '{tag['type']}' "
                f"which is not in the rule's edge case types: {[ect.value for ect in rule.edge_case_types]}"
            )
            
            # Verify description is a non-empty string
            assert isinstance(tag['description'], str), (
                f"Tag description at index {idx} should be a string, got {type(tag['description'])}"
            )
            assert len(tag['description']) > 0, (
                f"Tag description at index {idx} should not be empty"
            )
    
    # Verify that non-injected indices don't have edge case tags (or have empty lists)
    non_injected_indices = set(range(len(result_df))) - set(injection_result.injected_indices)
    for idx in non_injected_indices:
        tags = result_df.at[idx, '_edge_case_tags']
        
        # Tags should be a list (possibly empty)
        assert isinstance(tags, list), (
            f"Tags at non-injected index {idx} should be a list, got {type(tags)}"
        )
        
        # For this single rule test, non-injected records should have empty tag lists
        assert len(tags) == 0, (
            f"Non-injected index {idx} should have empty tags, got {len(tags)} tags"
        )


@settings(max_examples=100, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    rules=st.lists(edge_case_rule_strategy(), min_size=2, max_size=4, unique_by=lambda r: r.field_name),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_tagging_completeness_multiple_rules(df, rules, seed):
    """
    Feature: synthetic-data-generator, Property 6: Edge Case Tagging Completeness
    Validates: Requirements 3.3
    
    For any generated dataset with multiple edge case rules applied to different fields,
    all edge-case records should have appropriate tags for each field that was modified.
    
    This test verifies that when multiple edge case rules are applied, each injected
    edge case is properly tagged, and records can have multiple tags if multiple
    fields were modified.
    """
    # Filter rules to only include fields that exist in the DataFrame
    valid_rules = [rule for rule in rules if rule.field_name in df.columns]
    
    # Ensure we have at least 2 valid rules
    assume(len(valid_rules) >= 2)
    
    # Ensure we have enough rows
    assume(len(df) >= 50)
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=valid_rules,
        seed=seed,
        tag_column='_edge_case_tags'
    )
    
    # Verify that the tag column exists
    assert '_edge_case_tags' in result_df.columns, (
        "Tag column '_edge_case_tags' not found in result DataFrame"
    )
    
    # For each injected index, verify that tags exist and are complete
    for idx in injection_result.injected_indices:
        tags = result_df.at[idx, '_edge_case_tags']
        
        # Tags should be a list
        assert isinstance(tags, list), (
            f"Tags at index {idx} should be a list, got {type(tags)}"
        )
        
        # Tags should not be empty
        assert len(tags) > 0, (
            f"Tags at index {idx} should not be empty for an injected edge case"
        )
        
        # Track which fields have been tagged at this index
        tagged_fields = set()
        
        # Each tag should be a dictionary with required fields
        for tag in tags:
            assert isinstance(tag, dict), (
                f"Tag at index {idx} should be a dictionary, got {type(tag)}"
            )
            
            # Verify required fields exist
            assert 'field' in tag, (
                f"Tag at index {idx} missing 'field' key: {tag}"
            )
            assert 'type' in tag, (
                f"Tag at index {idx} missing 'type' key: {tag}"
            )
            assert 'description' in tag, (
                f"Tag at index {idx} missing 'description' key: {tag}"
            )
            
            # Track this field
            tagged_fields.add(tag['field'])
            
            # Verify field name is from one of the valid rules
            rule_field_names = [r.field_name for r in valid_rules]
            assert tag['field'] in rule_field_names, (
                f"Tag at index {idx} has field name '{tag['field']}' "
                f"which is not in the valid rules: {rule_field_names}"
            )
            
            # Find the rule for this field
            matching_rule = next((r for r in valid_rules if r.field_name == tag['field']), None)
            assert matching_rule is not None, (
                f"Could not find matching rule for field '{tag['field']}'"
            )
            
            # Verify type is a valid EdgeCaseType value
            assert tag['type'] in [ect.value for ect in EdgeCaseType], (
                f"Tag at index {idx} has invalid edge case type: '{tag['type']}'"
            )
            
            # Verify type is one of the types specified in the matching rule
            assert tag['type'] in [ect.value for ect in matching_rule.edge_case_types], (
                f"Tag at index {idx} has edge case type '{tag['type']}' "
                f"which is not in the rule's edge case types for field '{tag['field']}': "
                f"{[ect.value for ect in matching_rule.edge_case_types]}"
            )
            
            # Verify description is a non-empty string
            assert isinstance(tag['description'], str), (
                f"Tag description at index {idx} should be a string, got {type(tag['description'])}"
            )
            assert len(tag['description']) > 0, (
                f"Tag description at index {idx} should not be empty"
            )
        
        # Verify that the number of unique fields in tags matches what we expect
        # (Each field should appear at most once per record)
        assert len(tagged_fields) == len(tags), (
            f"Index {idx} has duplicate field tags. "
            f"Tagged fields: {tagged_fields}, Total tags: {len(tags)}"
        )


@settings(max_examples=100, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    rule=edge_case_rule_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1),
    custom_tag_column=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122))
)
def test_edge_case_tagging_with_custom_column_name(df, rule, seed, custom_tag_column):
    """
    Feature: synthetic-data-generator, Property 6: Edge Case Tagging Completeness
    Validates: Requirements 3.3
    
    For any generated dataset with injected edge cases using a custom tag column name,
    all edge-case records should have appropriate tags in the specified column.
    
    This test verifies that the tagging mechanism works correctly with custom
    column names, not just the default '_edge_case_tags'.
    """
    # Ensure the field exists in the DataFrame
    assume(rule.field_name in df.columns)
    
    # Ensure custom tag column name doesn't conflict with existing columns
    assume(custom_tag_column not in df.columns)
    
    # Ensure we have enough rows
    assume(len(df) >= 50)
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases with custom tag column
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=[rule],
        seed=seed,
        tag_column=custom_tag_column
    )
    
    # Verify that the custom tag column exists
    assert custom_tag_column in result_df.columns, (
        f"Custom tag column '{custom_tag_column}' not found in result DataFrame"
    )
    
    # Verify that injected records have tags in the custom column
    for idx in injection_result.injected_indices:
        tags = result_df.at[idx, custom_tag_column]
        
        # Tags should be a list
        assert isinstance(tags, list), (
            f"Tags at index {idx} in column '{custom_tag_column}' should be a list, got {type(tags)}"
        )
        
        # Tags should not be empty
        assert len(tags) > 0, (
            f"Tags at index {idx} in column '{custom_tag_column}' should not be empty"
        )
        
        # Verify tag structure
        for tag in tags:
            assert isinstance(tag, dict), (
                f"Tag at index {idx} should be a dictionary, got {type(tag)}"
            )
            assert 'field' in tag and 'type' in tag and 'description' in tag, (
                f"Tag at index {idx} missing required keys: {tag}"
            )


@settings(max_examples=100, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    rule=edge_case_rule_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_tagging_matches_injection_result(df, rule, seed):
    """
    Feature: synthetic-data-generator, Property 6: Edge Case Tagging Completeness
    Validates: Requirements 3.3
    
    For any generated dataset with injected edge cases, the tags in the DataFrame
    should match the edge_case_tags in the EdgeCaseInjectionResult.
    
    This test verifies consistency between the tagging in the DataFrame and
    the metadata returned in the injection result.
    """
    # Ensure the field exists in the DataFrame
    assume(rule.field_name in df.columns)
    
    # Ensure we have enough rows
    assume(len(df) >= 50)
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=[rule],
        seed=seed,
        tag_column='_edge_case_tags'
    )
    
    # Verify that every index in injection_result.edge_case_tags has tags in the DataFrame
    for idx, edge_case_types in injection_result.edge_case_tags.items():
        # This index should be in the injected_indices
        assert idx in injection_result.injected_indices, (
            f"Index {idx} is in edge_case_tags but not in injected_indices"
        )
        
        # Get tags from DataFrame
        df_tags = result_df.at[idx, '_edge_case_tags']
        
        # Should have tags
        assert len(df_tags) > 0, (
            f"Index {idx} has edge case types in result but no tags in DataFrame"
        )
        
        # Extract edge case types from DataFrame tags
        df_edge_case_types = [EdgeCaseType(tag['type']) for tag in df_tags]
        
        # The edge case types should match
        assert set(df_edge_case_types) == set(edge_case_types), (
            f"Edge case types mismatch at index {idx}. "
            f"DataFrame: {df_edge_case_types}, Result: {edge_case_types}"
        )
    
    # Verify that every injected index has corresponding edge case tags
    for idx in injection_result.injected_indices:
        assert idx in injection_result.edge_case_tags, (
            f"Index {idx} is in injected_indices but not in edge_case_tags"
        )
        
        # Get tags from DataFrame
        df_tags = result_df.at[idx, '_edge_case_tags']
        
        # Should have tags
        assert len(df_tags) > 0, (
            f"Index {idx} is marked as injected but has no tags in DataFrame"
        )


@settings(max_examples=50, deadline=None)
@given(
    df=dataframe_with_fields_strategy(),
    rule=edge_case_rule_strategy(),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_edge_case_tagging_preserves_original_data_for_non_injected(df, rule, seed):
    """
    Feature: synthetic-data-generator, Property 6: Edge Case Tagging Completeness
    Validates: Requirements 3.3
    
    For any generated dataset with injected edge cases, records that were not
    injected should have empty tag lists and their original data should be preserved.
    
    This test verifies that the tagging mechanism doesn't affect non-injected records.
    """
    # Ensure the field exists in the DataFrame
    assume(rule.field_name in df.columns)
    
    # Ensure we have enough rows
    assume(len(df) >= 50)
    
    # Store original data for comparison
    original_df = df.copy()
    
    # Create edge case generator
    generator = EdgeCaseGenerator()
    
    # Inject edge cases
    result_df, injection_result = generator.inject_edge_cases(
        data=df,
        rules=[rule],
        seed=seed,
        tag_column='_edge_case_tags'
    )
    
    # Get non-injected indices
    non_injected_indices = set(range(len(result_df))) - set(injection_result.injected_indices)
    
    # Verify non-injected records
    for idx in non_injected_indices:
        # Tags should be empty
        tags = result_df.at[idx, '_edge_case_tags']
        assert isinstance(tags, list), (
            f"Tags at non-injected index {idx} should be a list"
        )
        assert len(tags) == 0, (
            f"Non-injected index {idx} should have empty tags, got {len(tags)} tags"
        )
        
        # Original data should be preserved (excluding the tag column)
        for col in original_df.columns:
            original_value = original_df.at[idx, col]
            result_value = result_df.at[idx, col]
            
            # Handle NaN comparison
            if pd.isna(original_value) and pd.isna(result_value):
                continue
            
            assert original_value == result_value, (
                f"Non-injected index {idx}, column '{col}': "
                f"original value '{original_value}' != result value '{result_value}'"
            )
