# Amazon Bedrock Integration

This module provides integration with Amazon Bedrock for generating realistic text fields in synthetic data.

## Overview

The Bedrock integration enables the Synthetic Data Agent to generate high-quality, contextually appropriate text values for sensitive fields like names, emails, addresses, and descriptions. It includes:

- **BedrockClient**: Wrapper for Amazon Bedrock API with retry logic and batching
- **BedrockConfig**: Configuration for model selection and generation parameters
- **RuleBasedTextGenerator**: Fallback generator using Faker when Bedrock is unavailable

## Features

### 1. Retry Logic with Exponential Backoff

The client automatically retries failed API calls with exponential backoff:
- Initial delay: 1 second
- Maximum delay: 16 seconds
- Maximum retries: 3 (configurable)
- Jitter added to prevent thundering herd

```python
from shared.utils.bedrock_client import BedrockClient, BedrockConfig

config = BedrockConfig(
    max_retries=3,
    initial_retry_delay=1.0,
    max_retry_delay=16.0
)

bedrock_client = BedrockClient(bedrock_runtime_client, config)
```

### 2. Efficient Batching

Large generation requests are automatically batched to optimize API usage:
- Default batch size: 100 values
- Configurable batch size
- Automatic batching for any number of values

```python
# Generate 500 values in batches of 100
values = bedrock_client.generate_text_field(
    field_name='email',
    field_type='email',
    num_values=500
)
```

### 3. Context-Aware Prompt Construction

Prompts include context from related fields to improve generation quality:

```python
context = {
    'first_name': ['John', 'Jane', 'Bob'],
    'company': ['Acme Corp', 'Tech Inc']
}

values = bedrock_client.generate_text_field(
    field_name='email',
    field_type='email',
    num_values=10,
    context=context  # Emails will be contextually appropriate
)
```

### 4. Constraint Support

Generation can be constrained by patterns, formats, or other requirements:

```python
constraints = {
    'pattern': r'^\d{3}-\d{3}-\d{4}$',
    'format': 'US phone number'
}

values = bedrock_client.generate_text_field(
    field_name='phone',
    field_type='phone',
    num_values=10,
    constraints=constraints
)
```

### 5. Automatic Fallback

When Bedrock fails or is unavailable, the system automatically falls back to rule-based generation using Faker:

```python
from shared.utils.bedrock_client import RuleBasedTextGenerator

fallback_generator = RuleBasedTextGenerator()

# This will use Bedrock, but fall back to Faker on failure
values = bedrock_client.generate_text_field(
    field_name='name',
    field_type='name',
    num_values=100,
    fallback_generator=lambda **kwargs: fallback_generator.generate(**kwargs)
)
```

## Usage

### Basic Usage

```python
from shared.utils.aws_config import AWSConfig
from shared.utils.bedrock_client import BedrockClient, BedrockConfig

# Initialize AWS configuration
aws_config = AWSConfig(region_name='us-east-1')
bedrock_runtime = aws_config.get_bedrock_client()

# Create Bedrock client
bedrock_config = BedrockConfig(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    temperature=0.9,
    batch_size=100
)
bedrock_client = BedrockClient(bedrock_runtime, bedrock_config)

# Generate text values
names = bedrock_client.generate_text_field(
    field_name='customer_name',
    field_type='name',
    num_values=50
)
```

### Integration with Synthetic Data Agent

```python
from agents.synthetic_data.agent import SyntheticDataAgent
from shared.utils.bedrock_client import BedrockClient, BedrockConfig

# Initialize agent with Bedrock
agent = SyntheticDataAgent(
    bedrock_client=bedrock_client,
    bedrock_config=bedrock_config
)

# Generate synthetic data
# Sensitive text fields will be replaced with Bedrock-generated values
synthetic_dataset = agent.generate_synthetic_data(
    data=production_data,
    sensitivity_report=sensitivity_report,
    num_rows=1000,
    sdv_model='gaussian_copula',
    seed=42
)
```

## Supported Field Types

The Bedrock integration supports generation of various text field types:

- **Names**: `name`, `first_name`, `last_name`
- **Contact**: `email`, `phone`, `address`, `street_address`
- **Location**: `city`, `state`, `country`, `postcode`
- **Business**: `company`, `job`
- **Text**: `text`, `sentence`, `paragraph`, `description`

## Configuration Options

### BedrockConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | str | `anthropic.claude-3-haiku-20240307-v1:0` | Bedrock model identifier |
| `temperature` | float | 0.9 | Sampling temperature (0-1) |
| `max_tokens` | int | 2000 | Maximum tokens per response |
| `top_p` | float | 0.9 | Nucleus sampling parameter |
| `batch_size` | int | 100 | Number of values per batch |
| `max_retries` | int | 3 | Maximum retry attempts |
| `initial_retry_delay` | float | 1.0 | Initial retry delay (seconds) |
| `max_retry_delay` | float | 16.0 | Maximum retry delay (seconds) |

## Error Handling

The Bedrock client handles various error scenarios:

1. **Transient Errors**: Automatic retry with exponential backoff
   - Network timeouts
   - Rate limiting (throttling)
   - Temporary service unavailability

2. **Permanent Errors**: Immediate failure with detailed error message
   - Invalid model ID
   - Authentication failures
   - Invalid request format

3. **Fallback on Exhausted Retries**: Uses rule-based generator if provided

## Performance Considerations

### Batching Strategy

- Small datasets (< 100 values): Single batch
- Medium datasets (100-1000 values): Multiple batches
- Large datasets (> 1000 values): Consider parallel processing

### Cost Optimization

- Use appropriate batch sizes to minimize API calls
- Consider using Haiku model for cost-effective generation
- Cache generated values when possible
- Use fallback generator for non-critical fields

### Latency

- Single batch: ~1-3 seconds
- Multiple batches: ~1-3 seconds per batch
- Retry delays: 1s, 2s, 4s (exponential)

## Testing

Run the unit tests:

```bash
pytest tests/unit/test_bedrock_client.py -v
```

Run the demo:

```bash
python examples/demo_bedrock_integration.py
```

## Requirements

- boto3 >= 1.28.0
- botocore >= 1.31.0
- faker >= 20.0.0
- AWS credentials configured
- Amazon Bedrock access enabled in AWS account

## Troubleshooting

### "No credentials found"

Configure AWS credentials:
```bash
export AWS_PROFILE=your-profile
# or
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

### "Bedrock access denied"

Ensure your AWS account has Bedrock enabled and your IAM role has the necessary permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

### "Model not found"

Verify the model ID is correct and available in your region:
```python
bedrock = boto3.client('bedrock', region_name='us-east-1')
models = bedrock.list_foundation_models(byProvider='anthropic')
print([m['modelId'] for m in models['modelSummaries']])
```

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Anthropic Claude Models](https://docs.anthropic.com/claude/docs)
- [Faker Documentation](https://faker.readthedocs.io/)
