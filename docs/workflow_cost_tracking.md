# Workflow Cost Tracking

## Overview

The workflow list now displays actual estimated costs for each workflow based on the Bedrock fields selected during strategy selection. This replaces the previous $0.00 placeholder with real cost estimates.

## Implementation

### Backend Changes

**File:** `web/backend/routers/workflow.py`

#### Strategy Selection Endpoint
When users select synthesis strategies, the system now:

1. **Identifies Bedrock fields** - Finds all fields using `bedrock_llm` or `bedrock_examples` strategies
2. **Collects examples** - Extracts any provided examples for cost calculation
3. **Calculates token estimates** - Uses the same logic as the cost estimation panel
4. **Computes total cost** - Multiplies token estimates by number of records and pricing
5. **Stores cost** - Saves `estimated_cost_usd` in the workflow state

```python
# Calculate estimated cost for Bedrock fields
bedrock_fields = [
    field_name for field_name, strategy_info in strategy_dict.items()
    if strategy_info['strategy'] in ['bedrock_llm', 'bedrock_examples']
]

estimated_cost = 0.0
if bedrock_fields:
    # Token estimation and cost calculation
    ...
    workflow['estimated_cost_usd'] = estimated_cost
```

#### Workflow Status Endpoints
Both the single workflow status and list workflows endpoints now return the estimated cost:

```python
cost_usd=workflow.get('estimated_cost_usd', workflow.get('cost_usd', 0.0))
```

This prioritizes the estimated cost, falling back to actual cost (if tracked) or $0.00.

### Frontend Display

**File:** `web/frontend/src/pages/WorkflowListPage.tsx`

The workflows table already had a "Cost" column that was displaying $0.00. Now it displays:
- **$0.00** - For workflows that haven't selected strategies yet
- **Estimated cost** - For workflows after strategy selection (e.g., $0.25, $1.50, $10.00)

The cost is formatted with 2 decimal places and color-coded in the UI.

## Cost Calculation Logic

The cost is calculated using the same estimation logic as the cost estimation panel:

1. **Base prompt tokens:** ~150 tokens (system message + instructions)
2. **Field context:** ~20 tokens per field name
3. **Examples:** ~50 additional tokens if examples provided
4. **Output:** ~30 tokens per generated value

Formula:
```
For each Bedrock field:
  input_tokens = (base + field_context + examples) * num_records
  output_tokens = 30 * num_records

total_cost = (total_input_tokens/1000 * input_price) + 
             (total_output_tokens/1000 * output_price)
```

## User Experience Flow

1. User uploads CSV and starts workflow
2. Workflow shows $0.00 cost initially
3. User selects field strategies (some using Bedrock)
4. System calculates estimated cost based on selections
5. Workflow list updates to show estimated cost
6. User can see costs across all workflows at a glance

## Benefits

- **Cost transparency** - Users see estimated costs before and after strategy selection
- **Budget planning** - Easy to compare costs across workflows
- **Cost awareness** - Helps users make informed decisions about Bedrock usage
- **No surprises** - Costs are visible throughout the workflow lifecycle

## Testing

**File:** `tests/test_workflow_cost_tracking.py`

Tests verify:
- Cost calculation accuracy
- Linear scaling with number of records
- Examples increase cost appropriately
- Integration with workflow state

## Future Enhancements

1. **Actual cost tracking** - Track real token usage from Bedrock API responses
2. **Cost comparison** - Show estimated vs actual costs
3. **Cost alerts** - Notify when actual costs exceed estimates
4. **Cost optimization** - Suggest cheaper alternatives when costs are high
5. **Historical tracking** - Track costs over time for budgeting

## Notes

- Costs are estimates and may vary from actual usage
- Uses Claude 3 Haiku pricing by default (most cost-effective)
- Costs update when strategies are selected/changed
- Workflows without Bedrock fields show $0.00
