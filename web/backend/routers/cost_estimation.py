"""
Cost Estimation Router

Provides endpoints for estimating Bedrock costs before synthetic data generation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cost", tags=["cost-estimation"])


class CostEstimationRequest(BaseModel):
    """Request model for cost estimation."""
    num_records: int
    bedrock_fields: List[str]
    field_examples: Optional[Dict[str, List[str]]] = None
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"


class CostEstimationResponse(BaseModel):
    """Response model for cost estimation."""
    estimated_cost_usd: float
    num_records: int
    num_bedrock_fields: int
    bedrock_fields: List[str]
    model_id: str
    input_tokens_estimate: int
    output_tokens_estimate: int
    input_cost_per_1k: float
    output_cost_per_1k: float
    breakdown: Dict[str, float]
    warnings: List[str]


# Bedrock Claude pricing (as of 2024)
# Source: https://aws.amazon.com/bedrock/pricing/
BEDROCK_PRICING = {
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "input_per_1k": 0.00025,  # $0.25 per 1M tokens
        "output_per_1k": 0.00125,  # $1.25 per 1M tokens
        "name": "Claude 3 Haiku"
    },
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "input_per_1k": 0.003,  # $3 per 1M tokens
        "output_per_1k": 0.015,  # $15 per 1M tokens
        "name": "Claude 3 Sonnet"
    },
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "input_per_1k": 0.003,  # $3 per 1M tokens
        "output_per_1k": 0.015,  # $15 per 1M tokens
        "name": "Claude 3.5 Sonnet"
    },
    "anthropic.claude-3-opus-20240229-v1:0": {
        "input_per_1k": 0.015,  # $15 per 1M tokens
        "output_per_1k": 0.075,  # $75 per 1M tokens
        "name": "Claude 3 Opus"
    }
}


def estimate_tokens_per_field(field_name: str, has_examples: bool = False) -> tuple[int, int]:
    """
    Estimate input and output tokens for generating one field value.
    
    Args:
        field_name: Name of the field
        has_examples: Whether examples are provided
        
    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    # Base prompt tokens (system message + instructions)
    base_input = 150
    
    # Field name and context
    field_context = len(field_name.split()) * 2 + 20
    
    # Examples add significant tokens
    examples_tokens = 0
    if has_examples:
        # Assume 5 examples, ~10 tokens each
        examples_tokens = 50
    
    # Total input tokens
    input_tokens = base_input + field_context + examples_tokens
    
    # Output tokens (generated value)
    # Most field values are short (10-50 tokens)
    output_tokens = 30
    
    return input_tokens, output_tokens


@router.post("/estimate", response_model=CostEstimationResponse)
async def estimate_cost(request: CostEstimationRequest):
    """
    Estimate the cost of generating synthetic data using Bedrock.
    
    This endpoint calculates the estimated cost based on:
    - Number of records to generate
    - Number of fields using Bedrock
    - Model being used (Haiku, Sonnet, Opus)
    - Whether examples are provided (affects token count)
    """
    try:
        # Validate model
        if request.model_id not in BEDROCK_PRICING:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model: {request.model_id}. Supported models: {list(BEDROCK_PRICING.keys())}"
            )
        
        pricing = BEDROCK_PRICING[request.model_id]
        
        # Calculate total tokens
        total_input_tokens = 0
        total_output_tokens = 0
        
        for field in request.bedrock_fields:
            has_examples = (
                request.field_examples is not None and 
                field in request.field_examples and 
                len(request.field_examples[field]) > 0
            )
            
            input_tokens, output_tokens = estimate_tokens_per_field(field, has_examples)
            
            # Multiply by number of records
            total_input_tokens += input_tokens * request.num_records
            total_output_tokens += output_tokens * request.num_records
        
        # Calculate costs
        input_cost = (total_input_tokens / 1000) * pricing["input_per_1k"]
        output_cost = (total_output_tokens / 1000) * pricing["output_per_1k"]
        total_cost = input_cost + output_cost
        
        # Generate warnings
        warnings = []
        if total_cost > 10:
            warnings.append(f"High cost estimate (${total_cost:.2f}). Consider reducing the number of records or using fewer Bedrock fields.")
        if total_cost > 50:
            warnings.append("Very high cost estimate. Strongly recommend reviewing your configuration.")
        if request.num_records > 10000:
            warnings.append("Large dataset. Generation may take significant time.")
        
        # Breakdown by component
        breakdown = {
            "input_tokens_cost": round(input_cost, 4),
            "output_tokens_cost": round(output_cost, 4),
            "cost_per_record": round(total_cost / request.num_records, 6) if request.num_records > 0 else 0,
            "cost_per_field": round(total_cost / len(request.bedrock_fields), 4) if request.bedrock_fields else 0
        }
        
        return CostEstimationResponse(
            estimated_cost_usd=round(total_cost, 4),
            num_records=request.num_records,
            num_bedrock_fields=len(request.bedrock_fields),
            bedrock_fields=request.bedrock_fields,
            model_id=request.model_id,
            input_tokens_estimate=total_input_tokens,
            output_tokens_estimate=total_output_tokens,
            input_cost_per_1k=pricing["input_per_1k"],
            output_cost_per_1k=pricing["output_per_1k"],
            breakdown=breakdown,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """Get list of available Bedrock models with pricing information."""
    return {
        "models": [
            {
                "id": model_id,
                "name": info["name"],
                "input_cost_per_1m": info["input_per_1k"] * 1000,
                "output_cost_per_1m": info["output_per_1k"] * 1000,
                "recommended_for": "Fast, cost-effective generation" if "haiku" in model_id.lower() 
                    else "Balanced performance and cost" if "sonnet" in model_id.lower()
                    else "Highest quality, most expensive"
            }
            for model_id, info in BEDROCK_PRICING.items()
        ]
    }
