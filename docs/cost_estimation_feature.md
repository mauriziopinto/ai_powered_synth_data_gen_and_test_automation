# Bedrock Cost Estimation Feature

## Overview

This feature provides real-time cost estimation for synthetic data generation using AWS Bedrock before the user commits to generating the data. This helps users make informed decisions about their configuration and avoid unexpected costs.

## Components

### Backend

**File:** `web/backend/routers/cost_estimation.py`

- **Endpoint:** `POST /api/v1/cost/estimate`
  - Calculates estimated costs based on:
    - Number of records to generate
    - Number of fields using Bedrock
    - Model being used (Haiku, Sonnet, Opus)
    - Whether examples are provided (affects token count)
  
- **Endpoint:** `GET /api/v1/cost/models`
  - Returns available Bedrock models with pricing information

**Pricing Data:**
- Claude 3 Haiku: $0.25/$1.25 per 1M input/output tokens
- Claude 3 Sonnet: $3/$15 per 1M input/output tokens
- Claude 3.5 Sonnet: $3/$15 per 1M input/output tokens
- Claude 3 Opus: $15/$75 per 1M input/output tokens

### Frontend

**File:** `web/frontend/src/components/workflow/CostEstimationPanel.tsx`

A React component that:
- Displays estimated total cost
- Shows cost breakdown (input/output tokens)
- Lists Bedrock-generated fields
- Provides cost per record and cost per field
- Shows warnings for high-cost configurations
- Updates automatically when configuration changes

**Integration:** `web/frontend/src/pages/StrategySelectionPage.tsx`

The cost estimation panel appears:
- Only when at least one field uses Bedrock (bedrock_llm or bedrock_examples)
- Before the "Apply Strategies & Continue" button
- Updates in real-time as users change field strategies

## Token Estimation Logic

The system estimates tokens based on:

1. **Base prompt tokens:** ~150 tokens (system message + instructions)
2. **Field context:** ~20 tokens per field name
3. **Examples:** ~50 additional tokens if examples are provided
4. **Output:** ~30 tokens per generated value

Formula:
```
input_tokens = (base + field_context + examples) * num_records
output_tokens = 30 * num_records
total_cost = (input_tokens/1000 * input_price) + (output_tokens/1000 * output_price)
```

## Cost Warnings

The system provides warnings when:
- Total cost > $10: "High cost estimate"
- Total cost > $50: "Very high cost estimate"
- Number of records > 10,000: "Large dataset warning"

## User Experience

1. User selects field strategies on the Strategy Selection page
2. If any field uses Bedrock, the cost estimation panel appears automatically
3. Panel shows:
   - Total estimated cost (color-coded: green < $1, yellow < $10, red >= $10)
   - Token breakdown
   - Cost per record and per field
   - List of Bedrock fields
   - Warnings if applicable
4. User can adjust configuration and see costs update in real-time
5. User proceeds with full cost transparency

## Testing

**File:** `tests/test_cost_estimation.py`

Tests cover:
- Token estimation with and without examples
- Pricing data structure validation
- Model comparison (Haiku is cheapest)
- Cost calculation accuracy

## Future Enhancements

Potential improvements:
1. Integration with AWS Pricing API for real-time pricing updates
2. Historical cost tracking per workflow
3. Budget alerts and limits
4. Cost optimization suggestions
5. Comparison of different model choices
6. Batch size optimization recommendations

## Notes

- Costs are estimates based on typical token usage
- Actual costs may vary slightly based on actual token consumption
- Pricing is current as of 2024 and should be updated periodically
- The feature helps prevent bill shock and enables cost-conscious decisions
