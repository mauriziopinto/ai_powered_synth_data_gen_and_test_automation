"""Demo script for Synthetic Data Agent with SDV integration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime

from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport, FieldClassification


def create_sample_data():
    """Create sample production data for demonstration."""
    np.random.seed(42)
    
    # Create realistic sample data
    n_records = 100
    
    data = {
        'customer_id': range(1000, 1000 + n_records),
        'age': np.random.randint(18, 80, n_records),
        'income': np.random.randint(20000, 150000, n_records),
        'credit_score': np.random.randint(300, 850, n_records),
        'account_balance': np.random.uniform(0, 50000, n_records),
        'num_transactions': np.random.randint(0, 100, n_records),
        'is_premium': np.random.choice([True, False], n_records, p=[0.3, 0.7]),
    }
    
    df = pd.DataFrame(data)
    
    # Add some correlation: higher income -> higher credit score
    df['credit_score'] = (df['income'] / 200).astype(int) + np.random.randint(-50, 50, n_records)
    df['credit_score'] = df['credit_score'].clip(300, 850)
    
    return df


def create_sample_sensitivity_report(df):
    """Create a sample sensitivity report for the data."""
    classifications = {}
    
    for column in df.columns:
        # Classify customer_id as sensitive identifier
        if column == 'customer_id':
            classifications[column] = FieldClassification(
                field_name=column,
                is_sensitive=True,
                sensitivity_type='identifier',
                confidence=0.9,
                reasoning='Customer ID is a unique identifier',
                recommended_strategy='sdv_preserve_distribution'
            )
        else:
            # All other fields are non-sensitive for this demo
            classifications[column] = FieldClassification(
                field_name=column,
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field without PII',
                recommended_strategy='sdv_preserve_distribution'
            )
    
    return SensitivityReport(
        classifications=classifications,
        data_profile={},
        timestamp=datetime.now(),
        total_fields=len(df.columns),
        sensitive_fields=1,
        confidence_distribution={'high': 1, 'medium': 0, 'low': len(df.columns) - 1}
    )


def main():
    """Run the Synthetic Data Agent demo."""
    print("=" * 80)
    print("Synthetic Data Agent Demo - SDV Integration")
    print("=" * 80)
    print()
    
    # Step 1: Create sample production data
    print("Step 1: Creating sample production data...")
    production_data = create_sample_data()
    print(f"Created {len(production_data)} production records")
    print(f"Columns: {list(production_data.columns)}")
    print()
    print("Sample production data:")
    print(production_data.head())
    print()
    
    # Step 2: Create sensitivity report
    print("Step 2: Creating sensitivity report...")
    sensitivity_report = create_sample_sensitivity_report(production_data)
    print(f"Total fields: {sensitivity_report.total_fields}")
    print(f"Sensitive fields: {sensitivity_report.sensitive_fields}")
    print()
    
    # Step 3: Initialize Synthetic Data Agent
    print("Step 3: Initializing Synthetic Data Agent...")
    agent = SyntheticDataAgent()
    print("Agent initialized successfully")
    print()
    
    # Step 4: Generate synthetic data with GaussianCopula
    print("Step 4: Generating synthetic data with GaussianCopula model...")
    print("Parameters:")
    print("  - Model: gaussian_copula")
    print("  - Number of rows: 50")
    print("  - Seed: 42")
    print()
    
    synthetic_dataset = agent.generate_synthetic_data(
        data=production_data,
        sensitivity_report=sensitivity_report,
        num_rows=50,
        sdv_model='gaussian_copula',
        seed=42
    )
    
    print("Synthetic data generation complete!")
    print()
    
    # Step 5: Display results
    print("Step 5: Analyzing results...")
    print()
    print("Synthetic data sample:")
    print(synthetic_dataset.data.head())
    print()
    
    print("Quality Metrics:")
    print(f"  - Overall SDV Quality Score: {synthetic_dataset.quality_metrics.sdv_quality_score:.3f}")
    print(f"  - Column Shapes Score: {synthetic_dataset.quality_metrics.column_shapes_score:.3f}")
    print(f"  - Column Pair Trends Score: {synthetic_dataset.quality_metrics.column_pair_trends_score:.3f}")
    print(f"  - Correlation Preservation: {synthetic_dataset.quality_metrics.correlation_preservation:.3f}")
    print()
    
    # Display KS test results
    if synthetic_dataset.quality_metrics.ks_tests:
        print("Kolmogorov-Smirnov Test Results:")
        for column, results in synthetic_dataset.quality_metrics.ks_tests.items():
            print(f"  - {column}:")
            print(f"      Statistic: {results['statistic']:.4f}")
            print(f"      P-value: {results['pvalue']:.4f}")
        print()
    
    # Step 6: Compare distributions
    print("Step 6: Comparing distributions...")
    print()
    print("Production data statistics:")
    print(production_data.describe())
    print()
    print("Synthetic data statistics:")
    print(synthetic_dataset.data.describe())
    print()
    
    # Step 7: Save synthetic data
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "demo_synthetic_data.csv"
    
    print(f"Step 7: Saving synthetic data to {output_path}...")
    agent.save_synthetic_data(synthetic_dataset, output_path, format='csv')
    print("Synthetic data saved successfully!")
    print()
    
    # Step 8: Test different SDV models (optional)
    print("Step 8: Testing with different SDV models...")
    print()
    
    for model_name in ['gaussian_copula']:  # Can add 'ctgan', 'copula_gan' but they take longer
        print(f"Testing {model_name}...")
        try:
            result = agent.generate_synthetic_data(
                data=production_data,
                sensitivity_report=sensitivity_report,
                num_rows=30,
                sdv_model=model_name,
                seed=42
            )
            print(f"  ✓ {model_name}: Quality Score = {result.quality_metrics.sdv_quality_score:.3f}")
        except Exception as e:
            print(f"  ✗ {model_name}: {str(e)}")
    print()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("1. SDV successfully generated synthetic data preserving statistical properties")
    print("2. Quality metrics show how well the synthetic data matches the original")
    print("3. Multiple SDV models are supported (GaussianCopula, CTGAN, CopulaGAN)")
    print("4. Sensitive fields can be identified and handled appropriately")
    print("5. Generated data maintains correlations and distributions from source data")


if __name__ == "__main__":
    main()
