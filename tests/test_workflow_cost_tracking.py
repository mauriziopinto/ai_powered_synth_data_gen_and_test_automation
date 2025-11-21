"""
Tests for workflow cost tracking functionality.
"""

import pytest
from web.backend.routers.cost_estimation import estimate_tokens_per_field, BEDROCK_PRICING


def test_workflow_cost_calculation():
    """Test that workflow cost calculation works correctly."""
    # Simulate workflow parameters
    num_records = 1000
    bedrock_fields = ['email', 'name', 'address']
    field_examples = {
        'email': ['test@example.com', 'user@domain.com']
    }
    
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    pricing = BEDROCK_PRICING[model_id]
    
    total_input_tokens = 0
    total_output_tokens = 0
    
    for field in bedrock_fields:
        has_examples = field in field_examples and len(field_examples[field]) > 0
        input_tokens, output_tokens = estimate_tokens_per_field(field, has_examples)
        total_input_tokens += input_tokens * num_records
        total_output_tokens += output_tokens * num_records
    
    input_cost = (total_input_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (total_output_tokens / 1000) * pricing["output_per_1k"]
    total_cost = input_cost + output_cost
    
    # Verify cost is calculated
    assert total_cost > 0
    assert input_cost > 0
    assert output_cost > 0
    
    # Note: Input cost may be higher due to more input tokens (prompt + context)
    # Output cost per token is higher, but there are fewer output tokens
    
    # Verify cost is reasonable for 1000 records with 3 fields
    # Should be less than $1 for Haiku
    assert total_cost < 1.0
    
    print(f"Total cost for {num_records} records with {len(bedrock_fields)} Bedrock fields: ${total_cost:.4f}")
    print(f"  Input tokens: {total_input_tokens:,} (${input_cost:.4f})")
    print(f"  Output tokens: {total_output_tokens:,} (${output_cost:.4f})")


def test_cost_scales_with_records():
    """Test that cost scales linearly with number of records."""
    bedrock_fields = ['email']
    
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    pricing = BEDROCK_PRICING[model_id]
    
    # Calculate cost for 100 records
    input_tokens_100, output_tokens_100 = estimate_tokens_per_field('email', False)
    cost_100 = ((input_tokens_100 * 100 / 1000) * pricing["input_per_1k"] + 
                (output_tokens_100 * 100 / 1000) * pricing["output_per_1k"])
    
    # Calculate cost for 1000 records
    input_tokens_1000, output_tokens_1000 = estimate_tokens_per_field('email', False)
    cost_1000 = ((input_tokens_1000 * 1000 / 1000) * pricing["input_per_1k"] + 
                 (output_tokens_1000 * 1000 / 1000) * pricing["output_per_1k"])
    
    # Cost should scale linearly (10x records = 10x cost)
    assert abs(cost_1000 / cost_100 - 10.0) < 0.1  # Allow small floating point error


def test_examples_increase_cost():
    """Test that providing examples increases the estimated cost."""
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    pricing = BEDROCK_PRICING[model_id]
    
    # Cost without examples
    input_no_ex, output_no_ex = estimate_tokens_per_field('email', False)
    cost_no_ex = ((input_no_ex / 1000) * pricing["input_per_1k"] + 
                  (output_no_ex / 1000) * pricing["output_per_1k"])
    
    # Cost with examples
    input_with_ex, output_with_ex = estimate_tokens_per_field('email', True)
    cost_with_ex = ((input_with_ex / 1000) * pricing["input_per_1k"] + 
                    (output_with_ex / 1000) * pricing["output_per_1k"])
    
    # Examples should increase cost
    assert cost_with_ex > cost_no_ex
    assert input_with_ex > input_no_ex


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
