"""
Tests for cost estimation functionality.
"""

import pytest
from web.backend.routers.cost_estimation import estimate_tokens_per_field, BEDROCK_PRICING


def test_estimate_tokens_per_field_without_examples():
    """Test token estimation for a field without examples."""
    input_tokens, output_tokens = estimate_tokens_per_field("email", has_examples=False)
    
    assert input_tokens > 0
    assert output_tokens > 0
    assert input_tokens > output_tokens  # Input should be larger (prompt + context)


def test_estimate_tokens_per_field_with_examples():
    """Test token estimation for a field with examples."""
    input_tokens_no_ex, _ = estimate_tokens_per_field("email", has_examples=False)
    input_tokens_with_ex, _ = estimate_tokens_per_field("email", has_examples=True)
    
    assert input_tokens_with_ex > input_tokens_no_ex  # Examples add tokens


def test_bedrock_pricing_structure():
    """Test that pricing data is properly structured."""
    assert len(BEDROCK_PRICING) > 0
    
    for model_id, pricing in BEDROCK_PRICING.items():
        assert "input_per_1k" in pricing
        assert "output_per_1k" in pricing
        assert "name" in pricing
        assert pricing["input_per_1k"] > 0
        assert pricing["output_per_1k"] > 0
        assert pricing["output_per_1k"] > pricing["input_per_1k"]  # Output is more expensive


def test_haiku_is_cheapest():
    """Test that Haiku is the cheapest model."""
    haiku_pricing = BEDROCK_PRICING["anthropic.claude-3-haiku-20240307-v1:0"]
    
    for model_id, pricing in BEDROCK_PRICING.items():
        if "haiku" not in model_id.lower():
            assert pricing["input_per_1k"] >= haiku_pricing["input_per_1k"]
            assert pricing["output_per_1k"] >= haiku_pricing["output_per_1k"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
