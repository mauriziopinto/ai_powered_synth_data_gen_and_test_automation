# Synthetic Data Agent - SDV Integration

## Overview

The Synthetic Data Agent is responsible for generating GDPR-compliant synthetic datasets that preserve the statistical properties of production data. It uses the Synthetic Data Vault (SDV) library for tabular data synthesis and provides a unified interface for multiple SDV models.

## Features

### SDV Synthesizer Wrapper
- **Multiple Model Support**: GaussianCopula, CTGAN, and CopulaGAN
- **Automatic Metadata Generation**: Creates SDV metadata from DataFrames and sensitivity reports
- **Quality Evaluation**: Built-in quality assessment using SDV metrics
- **Flexible Configuration**: Supports custom parameters for each synthesizer type

### Synthetic Data Agent
- **Field Separation**: Automatically separates sensitive and non-sensitive fields
- **Statistical Preservation**: Maintains distributions, correlations, and value frequencies
- **Quality Metrics**: Comprehensive quality assessment including:
  - SDV Quality Score
  - Column Shapes Score
  - Column Pair Trends Score
  - Kolmogorov-Smirnov tests
  - Correlation preservation
- **Multiple Export Formats**: CSV, JSON, Parquet support

## Architecture

```
SyntheticDataAgent
├── SDVSynthesizerWrapper
│   ├── GaussianCopulaSynthesizer
│   ├── CTGANSynthesizer
│   └── CopulaGANSynthesizer
├── Quality Evaluation
│   ├── SDV Metrics
│   ├── Statistical Tests (KS)
│   └── Correlation Analysis
└── Data Export
    ├── CSV
    ├── JSON
    └── Parquet
```

## Usage

### Basic Example

```python
from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport

# Initialize agent
agent = SyntheticDataAgent()

# Generate synthetic data
synthetic_dataset = agent.generate_synthetic_data(
    data=production_df,
    sensitivity_report=sensitivity_report,
    num_rows=1000,
    sdv_model='gaussian_copula',
    seed=42
)

# Access results
print(f"Quality Score: {synthetic_dataset.quality_metrics.sdv_quality_score}")
print(synthetic_dataset.data.head())

# Save to file
agent.save_synthetic_data(synthetic_dataset, Path("output.csv"), format='csv')
```

### Advanced Configuration

```python
# Use CTGAN model with custom parameters
synthetic_dataset = agent.generate_synthetic_data(
    data=production_df,
    sensitivity_report=sensitivity_report,
    num_rows=5000,
    sdv_model='ctgan',
    seed=42,
    epochs=300,  # CTGAN-specific parameter
    batch_size=500
)
```

## SDV Models

### GaussianCopula
- **Best for**: Fast generation, moderate-sized datasets
- **Pros**: Quick training, good for continuous data
- **Cons**: May not capture complex distributions

### CTGAN
- **Best for**: High-quality synthesis, complex distributions
- **Pros**: Excellent quality, handles mixed data types
- **Cons**: Slower training, requires more data

### CopulaGAN
- **Best for**: Balance between quality and speed
- **Pros**: Good quality, faster than CTGAN
- **Cons**: More complex than GaussianCopula

## Quality Metrics

### SDV Quality Score
Overall quality score from SDV's evaluation framework (0-1, higher is better).

### Column Shapes Score
Measures how well individual column distributions are preserved.

### Column Pair Trends Score
Measures how well relationships between column pairs are preserved.

### KS Tests
Kolmogorov-Smirnov tests for each numeric column comparing distributions.

### Correlation Preservation
Measures how well correlations between numeric columns are maintained.

## Implementation Details

### Requirements Addressed
- **12.1**: SDV library integration for tabular data synthesis
- **12.2**: SDV synthesizers learn statistical properties and relationships
- **12.3**: User-specified parameters for SDV model configuration
- **12.4**: Support for GaussianCopula, CTGAN, and CopulaGAN models
- **12.5**: Quality metrics from SDV evaluation framework

### Key Components

1. **SDVSynthesizerWrapper**: Unified interface for all SDV models
   - Handles metadata creation
   - Manages model fitting and sampling
   - Provides quality evaluation

2. **SyntheticDataAgent**: Main agent class
   - Orchestrates data generation workflow
   - Separates sensitive/non-sensitive fields
   - Calculates comprehensive quality metrics
   - Handles data export

3. **Quality Evaluation**: Multi-faceted quality assessment
   - SDV built-in metrics
   - Statistical tests (KS, correlation)
   - Per-field and overall scores

## Testing

### Unit Tests
- 14 comprehensive unit tests covering:
  - Wrapper initialization and configuration
  - Metadata creation
  - Model fitting and sampling
  - Quality evaluation
  - Field separation
  - Data export

### Test Coverage
- 80% code coverage for agent.py
- All critical paths tested
- Edge cases handled

### Running Tests
```bash
pytest tests/unit/test_synthetic_data_agent.py -v
```

## Demo

Run the demo script to see the agent in action:

```bash
python examples/demo_synthetic_data_agent.py
```

The demo:
1. Creates sample production data
2. Generates sensitivity report
3. Produces synthetic data with GaussianCopula
4. Displays quality metrics
5. Compares distributions
6. Saves results to file

## Future Enhancements

### Planned Features
1. **Bedrock Integration**: Use Amazon Bedrock for sensitive text field generation
2. **Edge Case Injection**: Configurable edge case generation
3. **Constraint Enforcement**: Advanced schema constraint handling
4. **Incremental Generation**: Support for large-scale batch generation
5. **Custom Generators**: Plugin system for domain-specific generators

### Performance Optimizations
1. Parallel processing for large datasets
2. Caching of trained models
3. Streaming generation for memory efficiency

## References

- [SDV Documentation](https://docs.sdv.dev/)
- [Design Document](.kiro/specs/synthetic-data-generator/design.md)
- [Requirements Document](.kiro/specs/synthetic-data-generator/requirements.md)
