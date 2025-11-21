"""Property-based tests for Bedrock prompt context inclusion.

This module tests that Bedrock prompts include context from related fields
and specified constraints when generating text fields.
"""

import json
import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest
from unittest.mock import Mock, patch, call
from typing import Dict, Any, List

from shared.utils.bedrock_client import BedrockClient, BedrockConfig


@composite
def field_context_strategy(draw):
    """Generate random field context dictionaries.
    
    Context includes related field values that should inform text generation.
    """
    # Generate 1-5 related fields
    num_fields = draw(st.integers(min_value=1, max_value=5))
    
    context = {}
    for i in range(num_fields):
        field_name = draw(st.sampled_from([
            'country', 'city', 'department', 'role', 'company',
            'age_group', 'region', 'category', 'status'
        ]))
        
        # Generate sample values for this field
        num_samples = draw(st.integers(min_value=1, max_value=5))
        samples = [
            draw(st.text(min_size=3, max_size=20, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'), 
                whitelist_characters=' '
            )))
            for _ in range(num_samples)
        ]
        
        context[field_name] = samples
    
    return context


@composite
def field_constraints_strategy(draw):
    """Generate random field constraint dictionaries.
    
    Constraints specify requirements like format, length, pattern, etc.
    """
    constraints = {}
    
    # Optionally add various constraint types
    if draw(st.booleans()):
        constraints['format'] = draw(st.sampled_from([
            'email', 'phone', 'url', 'postal_code', 'date'
        ]))
    
    if draw(st.booleans()):
        constraints['max_length'] = draw(st.integers(min_value=10, max_value=100))
    
    if draw(st.booleans()):
        constraints['pattern'] = draw(st.sampled_from([
            r'^\d{3}-\d{3}-\d{4}$',  # Phone pattern
            r'^[A-Z]{2}\d{5}$',       # Postal code pattern
            r'^[a-z]+@[a-z]+\.[a-z]+$'  # Email pattern
        ]))
    
    if draw(st.booleans()):
        constraints['must_contain'] = draw(st.text(min_size=1, max_size=10))
    
    # Return None if no constraints were added
    return constraints if constraints else None


@settings(max_examples=100, deadline=None)
@given(
    field_name=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll'), 
        whitelist_characters='_'
    )),
    field_type=st.sampled_from(['name', 'email', 'address', 'phone', 'description']),
    num_values=st.integers(min_value=1, max_value=50),
    context=field_context_strategy(),
    constraints=field_constraints_strategy()
)
def test_bedrock_prompt_includes_context(field_name, field_type, num_values, context, constraints):
    """
    Feature: synthetic-data-generator, Property 19: Bedrock Prompt Context Inclusion
    Validates: Requirements 13.3
    
    For any text field generation using Bedrock, the prompt should include
    context from related fields and specified constraints.
    
    This test verifies that:
    1. Context from related fields is included in the prompt
    2. Constraints are included in the prompt when provided
    3. The prompt structure is consistent and well-formed
    """
    # Ensure field_name is valid
    assume(len(field_name.strip()) > 0)
    assume(not field_name.isspace())
    
    # Create mock Bedrock runtime client
    mock_bedrock_runtime = Mock()
    
    # Mock response that returns a valid JSON array
    mock_response_body = json.dumps([f"{field_type}_{i}" for i in range(num_values)])
    mock_response = {
        'body': Mock(read=Mock(return_value=json.dumps({
            'content': [{'text': mock_response_body}]
        }).encode()))
    }
    mock_bedrock_runtime.invoke_model.return_value = mock_response
    
    # Create Bedrock client
    config = BedrockConfig(batch_size=max(num_values, 10))
    client = BedrockClient(mock_bedrock_runtime, config)
    
    # Generate text field
    result = client.generate_text_field_batch(
        field_name=field_name,
        field_type=field_type,
        num_values=num_values,
        context=context,
        constraints=constraints
    )
    
    # Verify the method was called
    assert mock_bedrock_runtime.invoke_model.called, "Bedrock invoke_model was not called"
    
    # Extract the prompt from the call
    call_args = mock_bedrock_runtime.invoke_model.call_args
    body_str = call_args.kwargs['body']
    body = json.loads(body_str)
    
    # Extract prompt from body (Anthropic format)
    if 'messages' in body:
        prompt = body['messages'][0]['content']
    else:
        prompt = body.get('prompt', '')
    
    # Verify prompt is not empty
    assert len(prompt) > 0, "Prompt should not be empty"
    
    # Verify field name is mentioned in prompt
    assert field_name in prompt, (
        f"Field name '{field_name}' should be mentioned in prompt"
    )
    
    # Verify field type is mentioned in prompt
    assert field_type in prompt, (
        f"Field type '{field_type}' should be mentioned in prompt"
    )
    
    # Verify number of values is mentioned in prompt
    assert str(num_values) in prompt, (
        f"Number of values '{num_values}' should be mentioned in prompt"
    )
    
    # Verify context is included when provided
    if context:
        # Check that "context" or "Context" appears in prompt
        assert 'context' in prompt.lower() or 'Context' in prompt, (
            "Prompt should mention context when context is provided"
        )
        
        # Verify at least some context field names appear in prompt
        context_fields_in_prompt = sum(
            1 for field in context.keys() if field in prompt
        )
        assert context_fields_in_prompt > 0, (
            f"At least one context field should appear in prompt. "
            f"Context fields: {list(context.keys())}"
        )
    
    # Verify constraints are included when provided
    if constraints:
        # Check that "constraint" or "Constraint" appears in prompt
        assert 'constraint' in prompt.lower() or 'Constraint' in prompt, (
            "Prompt should mention constraints when constraints are provided"
        )
        
        # Verify at least some constraint keys or values appear in prompt
        constraint_items_in_prompt = sum(
            1 for key, value in constraints.items()
            if key in prompt or str(value) in prompt
        )
        assert constraint_items_in_prompt > 0, (
            f"At least one constraint should appear in prompt. "
            f"Constraints: {constraints}"
        )
    
    # Verify JSON format instruction is present
    assert 'JSON' in prompt or 'json' in prompt, (
        "Prompt should instruct model to return JSON format"
    )
    
    # Verify result is a list of strings
    assert isinstance(result, list), "Result should be a list"
    assert all(isinstance(v, str) for v in result), "All values should be strings"


@settings(max_examples=50, deadline=None)
@given(
    field_name=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll'), 
        whitelist_characters='_'
    )),
    field_type=st.sampled_from(['name', 'email', 'address']),
    num_values=st.integers(min_value=5, max_value=20),
    context=field_context_strategy()
)
def test_context_values_appear_in_prompt(field_name, field_type, num_values, context):
    """
    Feature: synthetic-data-generator, Property 19: Bedrock Prompt Context Inclusion
    Validates: Requirements 13.3
    
    Verify that actual context values (not just field names) appear in the prompt.
    This ensures the LLM has concrete examples to work with.
    """
    # Ensure field_name is valid
    assume(len(field_name.strip()) > 0)
    assume(not field_name.isspace())
    
    # Create mock Bedrock runtime client
    mock_bedrock_runtime = Mock()
    
    # Mock response
    mock_response_body = json.dumps([f"{field_type}_{i}" for i in range(num_values)])
    mock_response = {
        'body': Mock(read=Mock(return_value=json.dumps({
            'content': [{'text': mock_response_body}]
        }).encode()))
    }
    mock_bedrock_runtime.invoke_model.return_value = mock_response
    
    # Create Bedrock client
    config = BedrockConfig(batch_size=max(num_values, 10))
    client = BedrockClient(mock_bedrock_runtime, config)
    
    # Generate text field
    client.generate_text_field_batch(
        field_name=field_name,
        field_type=field_type,
        num_values=num_values,
        context=context,
        constraints=None
    )
    
    # Extract the prompt
    call_args = mock_bedrock_runtime.invoke_model.call_args
    body_str = call_args.kwargs['body']
    body = json.loads(body_str)
    
    if 'messages' in body:
        prompt = body['messages'][0]['content']
    else:
        prompt = body.get('prompt', '')
    
    # Verify at least some context values appear in prompt
    # (not just field names, but actual sample values)
    context_values_found = 0
    for field, values in context.items():
        if isinstance(values, (list, tuple)):
            for value in values[:3]:  # Check first 3 values
                if str(value) in prompt:
                    context_values_found += 1
                    break
    
    # At least one context value should appear
    assert context_values_found > 0, (
        f"At least one context value should appear in prompt. "
        f"Context: {context}"
    )


@settings(max_examples=50, deadline=None)
@given(
    field_name=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll'), 
        whitelist_characters='_'
    )),
    field_type=st.sampled_from(['email', 'phone', 'address']),
    num_values=st.integers(min_value=5, max_value=20)
)
def test_prompt_without_context_still_valid(field_name, field_type, num_values):
    """
    Feature: synthetic-data-generator, Property 19: Bedrock Prompt Context Inclusion
    Validates: Requirements 13.3
    
    Verify that prompts are still valid and well-formed even when no context
    or constraints are provided.
    """
    # Ensure field_name is valid
    assume(len(field_name.strip()) > 0)
    assume(not field_name.isspace())
    
    # Create mock Bedrock runtime client
    mock_bedrock_runtime = Mock()
    
    # Mock response
    mock_response_body = json.dumps([f"{field_type}_{i}" for i in range(num_values)])
    mock_response = {
        'body': Mock(read=Mock(return_value=json.dumps({
            'content': [{'text': mock_response_body}]
        }).encode()))
    }
    mock_bedrock_runtime.invoke_model.return_value = mock_response
    
    # Create Bedrock client
    config = BedrockConfig(batch_size=max(num_values, 10))
    client = BedrockClient(mock_bedrock_runtime, config)
    
    # Generate text field without context or constraints
    result = client.generate_text_field_batch(
        field_name=field_name,
        field_type=field_type,
        num_values=num_values,
        context=None,
        constraints=None
    )
    
    # Extract the prompt
    call_args = mock_bedrock_runtime.invoke_model.call_args
    body_str = call_args.kwargs['body']
    body = json.loads(body_str)
    
    if 'messages' in body:
        prompt = body['messages'][0]['content']
    else:
        prompt = body.get('prompt', '')
    
    # Verify prompt is still well-formed
    assert len(prompt) > 0, "Prompt should not be empty"
    assert field_name in prompt, "Field name should be in prompt"
    assert field_type in prompt, "Field type should be in prompt"
    assert str(num_values) in prompt, "Number of values should be in prompt"
    
    # Verify JSON format instruction is present
    assert 'JSON' in prompt or 'json' in prompt, (
        "Prompt should instruct model to return JSON format"
    )
    
    # Verify result is valid
    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Result should not be empty"


@settings(max_examples=50, deadline=None)
@given(
    field_name=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll'), 
        whitelist_characters='_'
    )),
    field_type=st.sampled_from(['name', 'email', 'address']),
    num_values=st.integers(min_value=5, max_value=20),
    constraints=field_constraints_strategy()
)
def test_constraint_details_in_prompt(field_name, field_type, num_values, constraints):
    """
    Feature: synthetic-data-generator, Property 19: Bedrock Prompt Context Inclusion
    Validates: Requirements 13.3
    
    Verify that specific constraint details (not just the word "constraint")
    appear in the prompt to guide generation.
    """
    # Ensure field_name is valid
    assume(len(field_name.strip()) > 0)
    assume(not field_name.isspace())
    
    # Only test when constraints are provided
    assume(constraints is not None)
    assume(len(constraints) > 0)
    
    # Create mock Bedrock runtime client
    mock_bedrock_runtime = Mock()
    
    # Mock response
    mock_response_body = json.dumps([f"{field_type}_{i}" for i in range(num_values)])
    mock_response = {
        'body': Mock(read=Mock(return_value=json.dumps({
            'content': [{'text': mock_response_body}]
        }).encode()))
    }
    mock_bedrock_runtime.invoke_model.return_value = mock_response
    
    # Create Bedrock client
    config = BedrockConfig(batch_size=max(num_values, 10))
    client = BedrockClient(mock_bedrock_runtime, config)
    
    # Generate text field
    client.generate_text_field_batch(
        field_name=field_name,
        field_type=field_type,
        num_values=num_values,
        context=None,
        constraints=constraints
    )
    
    # Extract the prompt
    call_args = mock_bedrock_runtime.invoke_model.call_args
    body_str = call_args.kwargs['body']
    body = json.loads(body_str)
    
    if 'messages' in body:
        prompt = body['messages'][0]['content']
    else:
        prompt = body.get('prompt', '')
    
    # Verify specific constraint keys appear in prompt
    for key in constraints.keys():
        assert key in prompt, (
            f"Constraint key '{key}' should appear in prompt"
        )
    
    # Verify at least one constraint value appears in prompt
    values_found = sum(
        1 for value in constraints.values()
        if str(value) in prompt
    )
    
    assert values_found > 0, (
        f"At least one constraint value should appear in prompt. "
        f"Constraints: {constraints}"
    )


@settings(max_examples=50, deadline=None)
@given(
    field_name=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll'), 
        whitelist_characters='_'
    )),
    field_type=st.sampled_from(['name', 'email', 'address']),
    num_values=st.integers(min_value=5, max_value=20),
    context=field_context_strategy(),
    constraints=field_constraints_strategy()
)
def test_prompt_structure_consistency(field_name, field_type, num_values, context, constraints):
    """
    Feature: synthetic-data-generator, Property 19: Bedrock Prompt Context Inclusion
    Validates: Requirements 13.3
    
    Verify that prompts follow a consistent structure regardless of
    what context and constraints are provided.
    """
    # Ensure field_name is valid
    assume(len(field_name.strip()) > 0)
    assume(not field_name.isspace())
    
    # Create mock Bedrock runtime client
    mock_bedrock_runtime = Mock()
    
    # Mock response
    mock_response_body = json.dumps([f"{field_type}_{i}" for i in range(num_values)])
    mock_response = {
        'body': Mock(read=Mock(return_value=json.dumps({
            'content': [{'text': mock_response_body}]
        }).encode()))
    }
    mock_bedrock_runtime.invoke_model.return_value = mock_response
    
    # Create Bedrock client
    config = BedrockConfig(batch_size=max(num_values, 10))
    client = BedrockClient(mock_bedrock_runtime, config)
    
    # Generate text field
    client.generate_text_field_batch(
        field_name=field_name,
        field_type=field_type,
        num_values=num_values,
        context=context,
        constraints=constraints
    )
    
    # Extract the prompt
    call_args = mock_bedrock_runtime.invoke_model.call_args
    body_str = call_args.kwargs['body']
    body = json.loads(body_str)
    
    if 'messages' in body:
        prompt = body['messages'][0]['content']
    else:
        prompt = body.get('prompt', '')
    
    # Verify prompt has expected structural elements
    # 1. Introduction/instruction
    assert 'Generate' in prompt or 'generate' in prompt, (
        "Prompt should contain generation instruction"
    )
    
    # 2. Field information
    assert field_name in prompt, "Prompt should contain field name"
    assert field_type in prompt, "Prompt should contain field type"
    
    # 3. Output format specification
    assert 'JSON' in prompt or 'json' in prompt, (
        "Prompt should specify JSON output format"
    )
    assert '[' in prompt and ']' in prompt, (
        "Prompt should show array format example"
    )
    
    # 4. Context section (if context provided)
    if context:
        # Should have a section header for context
        assert any(marker in prompt for marker in ['Context', 'context', 'related']), (
            "Prompt should have context section when context is provided"
        )
    
    # 5. Constraints section (if constraints provided)
    if constraints:
        # Should have a section header for constraints
        assert any(marker in prompt for marker in ['Constraint', 'constraint', 'requirement']), (
            "Prompt should have constraints section when constraints are provided"
        )
