# Plain-Language Explanation System

## Overview

The Plain-Language Explanation System provides transparent, understandable descriptions of all agent actions, decisions, and data transformations throughout the synthetic data generation workflow. This system fulfills **Requirement 25** by making the entire process accessible to non-technical stakeholders.

## Key Features

1. **Explanation Templates** - Pre-defined templates for each agent action
2. **Dynamic Generation** - Context-aware explanations with real-time data
3. **Before/After Comparisons** - Visual highlighting of data transformations
4. **Decision Reasoning** - Detailed breakdown of classification decisions
5. **Contextual Progress** - Specific action descriptions instead of generic percentages

## Architecture

```
ExplanationGenerator (Singleton)
├── DataProcessorExplanations
├── SyntheticDataExplanations
├── DistributionExplanations
├── TestCaseExplanations
└── TestExecutionExplanations
```

## Usage

### Basic Explanation Generation

```python
from shared.utils.explanation_generator import get_explanation_generator

generator = get_explanation_generator()

# Generate explanation for an action
explanation = generator.generate('data_processor', 'field_classification', {
    'field_name': 'customer_email'
})

print(explanation.plain_language)
# Output: "Analyzing field "customer_email" to determine if it contains sensitive personal information"

print(explanation.reasoning)
# Output: "Using multiple classification methods: pattern matching for common PII formats..."
```

### Integrating with Agents

Agents can emit explanations using a callback pattern:

```python
class DataProcessorAgent:
    def __init__(self, explanation_callback=None):
        self.explanation_callback = explanation_callback
        self.explanation_generator = get_explanation_generator()
    
    def _emit_explanation(self, action: str, context: Dict[str, Any]):
        if self.explanation_callback:
            explanation = self.explanation_generator.generate(
                'data_processor', action, context
            )
            self.explanation_callback(explanation)
    
    def process(self, data_file):
        # Emit explanation at key points
        self._emit_explanation('start_analysis', {
            'num_columns': 50,
            'num_rows': 10000
        })
        
        # ... processing logic ...
        
        self._emit_explanation('field_classified_sensitive', {
            'field_name': 'customer_email',
            'pii_type': 'email',
            'confidence': 95,
            'reasoning_summary': 'pattern matching (95%), name-based (85%)',
            'strategy': 'bedrock_text'
        })
```

### Progress Messages

Generate contextual progress messages that describe specific actions:

```python
# Instead of: "Processing... 50%"
# Generate: "[50%] Processing batch of 100 email values (batch 50 of 100)"

progress_msg = generator.generate_progress_message(
    agent_name='synthetic_data',
    progress=0.50,
    current_action='bedrock_batch',
    context={
        'batch_size': 100,
        'field_type': 'email',
        'batch_num': 50,
        'total_batches': 100
    }
)
```

### Before/After Comparisons

Highlight data transformations with automatic change detection:

```python
before = {
    'customer_email': 'john.doe@example.com',
    'customer_phone': '555-123-4567',
    'account_balance': 1250.50
}

after = {
    'customer_email': 'synthetic.user.847@testmail.com',
    'customer_phone': '555-987-6543',
    'account_balance': 1250.50
}

comparison = generator.generate_comparison(
    before=before,
    after=after,
    highlights=['customer_email', 'customer_phone']  # Optional - auto-detected if omitted
)

# Access comparison data
for change in comparison['changes']:
    print(f"{change['field']}: {change['before_value']} → {change['after_value']}")
    print(f"Change type: {change['change_type']}")  # 'added', 'removed', 'modified', 'unchanged'
```

### Decision Reasoning

Display detailed reasoning for classification decisions:

```python
decision_reasoning = generator.format_decision_reasoning(
    decision="Classify 'customer_email' as SENSITIVE (email)",
    factors=[
        {
            'classifier': 'Pattern Matching',
            'confidence': 0.95,
            'reasoning': 'Found email pattern in 95% of samples'
        },
        {
            'classifier': 'Name-Based',
            'confidence': 0.85,
            'reasoning': 'Field name contains keyword "email"'
        },
        {
            'classifier': 'Confluence Knowledge',
            'confidence': 0.90,
            'reasoning': 'Documentation confirms this is an email field'
        }
    ],
    conclusion="Aggregated confidence: 95%. Recommended strategy: bedrock_text"
)
```

## Available Actions by Agent

### Data Processor Agent

- `start_analysis` - Beginning data analysis
- `field_classification` - Analyzing a specific field
- `pattern_detected` - PII pattern found
- `name_match` - Field name indicates PII
- `confluence_query` - Searching knowledge base
- `confluence_found` - Documentation retrieved
- `field_classified_sensitive` - Field marked as sensitive
- `field_classified_non_sensitive` - Field marked as non-sensitive
- `analysis_complete` - Analysis finished

### Synthetic Data Agent

- `start_generation` - Beginning data generation
- `sdv_training` - Training statistical model
- `sdv_sampling` - Generating records
- `bedrock_text_generation` - Using LLM for text fields
- `bedrock_batch` - Processing batch of values
- `rule_based_generation` - Using algorithmic generation
- `edge_case_injection` - Adding anomalies
- `quality_evaluation` - Evaluating quality
- `quality_score` - Quality metrics
- `generation_complete` - Generation finished

### Distribution Agent

- `start_distribution` - Beginning data distribution
- `target_connection` - Connecting to target
- `fk_analysis` - Analyzing foreign keys
- `fk_order` - Load order determined
- `table_load_start` - Loading table
- `table_load_complete` - Table loaded
- `salesforce_bulk` - Using Salesforce API
- `api_load` - Loading via REST API
- `load_error` - Load failed
- `distribution_complete` - Distribution finished

### Test Case Agent

- `start_test_generation` - Beginning test generation
- `jira_query` - Querying Jira
- `scenario_parsing` - Parsing scenario
- `test_code_generation` - Generating test code
- `data_mapping` - Mapping test data
- `test_case_created` - Test case created
- `generation_complete` - Generation finished

### Test Execution Agent

- `start_execution` - Beginning test execution
- `framework_setup` - Configuring framework
- `test_start` - Starting test
- `test_passed` - Test passed
- `test_failed` - Test failed
- `screenshot_captured` - Screenshot taken
- `jira_issue_created` - Issue created
- `jira_update` - Scenario updated
- `execution_complete` - Execution finished

## Web Interface Integration

The explanation system integrates with the web interface to provide real-time updates:

```typescript
// Frontend receives explanations via WebSocket
socket.on('explanation', (explanation) => {
  // Display in visualization dashboard
  displayExplanation({
    agent: explanation.agent_name,
    action: explanation.action,
    message: explanation.plain_language,
    reasoning: explanation.reasoning,
    timestamp: explanation.timestamp
  });
  
  // Show before/after comparison if available
  if (explanation.before_state && explanation.after_state) {
    displayComparison(
      explanation.before_state,
      explanation.after_state,
      explanation.highlights
    );
  }
});

// Progress updates with context
socket.on('progress', (progress) => {
  updateProgressBar(progress.percentage, progress.message);
  // Example: "[50%] Processing batch of 100 email values (batch 50 of 100)"
});
```

## Adding New Explanations

To add explanations for a new agent or action:

1. **Create Template Class**:

```python
class NewAgentExplanations(ExplanationTemplate):
    def __init__(self):
        super().__init__("New Agent Name")
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        return {
            'new_action': {
                'plain_language': 'Doing something with {param}',
                'reasoning': 'This action is necessary because...'
            }
        }
```

2. **Register in ExplanationGenerator**:

```python
class ExplanationGenerator:
    def __init__(self):
        self.templates = {
            # ... existing templates ...
            'new_agent': NewAgentExplanations()
        }
```

3. **Use in Agent**:

```python
self._emit_explanation('new_action', {'param': 'value'})
```

## Best Practices

1. **Be Specific**: Use concrete numbers and examples
   - ❌ "Processing data"
   - ✅ "Processing batch of 100 email values (batch 50 of 100)"

2. **Explain Why**: Always include reasoning
   - ❌ "Field classified as sensitive"
   - ✅ "Field classified as sensitive because pattern matching found email format in 95% of samples"

3. **Show Context**: Include related information
   - ❌ "Loading table"
   - ✅ "Loading 10,000 records into table 'customers' using truncate-insert strategy"

4. **Highlight Changes**: Make transformations visible
   - Use before/after comparisons
   - Highlight modified fields
   - Explain what changed and why

5. **Progressive Detail**: Start simple, allow drill-down
   - Plain language for overview
   - Reasoning for details
   - Full context in logs

## Testing

Run the demo to see all explanation types:

```bash
python examples/demo_plain_language_explanations.py
```

## Requirements Validation

This system validates **Requirement 25**:

- ✅ 25.1: Plain-language explanations for each agent action
- ✅ 25.2: Sample data transformations with before/after comparisons
- ✅ 25.3: Decision reasoning with confidence scores and references
- ✅ 25.4: Interactive drill-down capabilities (via web interface)
- ✅ 25.5: Contextual progress indicators with specific actions

## Related Documentation

- [Web Frontend Visualization](../../web/frontend/src/components/visualization/README.md)
- [Agent Architecture](../../agents/README.md)
- [Workflow Orchestration](../orchestration/README.md)
