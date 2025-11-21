"""Demo script for Synthetic Data Agent with Bedrock integration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
import os

from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport, FieldClassification
from shared.utils.bedrock_client import BedrockClient, BedrockConfig
from shared.utils.aws_config import AWSConfig


def create_sample_data_with_text_fields():
    """Create sample production data with text fields for demonstration."""
    np.random.seed(42)
    
    # Create realistic sample data with text fields
    n_records = 20  # Smaller dataset for demo
    
    data = {
        'customer_id': range(1000, 1000 + n_records),
        'age': np.random.randint(18, 80, n_records),
        'income': np.random.randint(20000, 150000, n_records),
        'credit_score': np.random.randint(300, 850, n_records),
        'account_balance': np.random.uniform(0, 50000, n_records),
        # Text fields that will be replaced by Bedrock
        'first_name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'] * 4,
        'last_name': ['Smith', 'Doe', 'Johnson', 'Williams', 'Brown'] * 4,
        'email': [f'user{i}@example.com' for i in range(n_records)],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'] * 4,
    }
    
    df = pd.DataFrame(data)
    
    # Add some correlation: higher income -> higher credit score
    df['credit_score'] = (df['income'] / 200).astype(int) + np.random.randint(-50, 50, n_records)
    df['credit_score'] = df['credit_score'].clip(300, 850)
    
    return df


def create_sensitivity_report_with_text_fields(df):
    """Create a sensitivity report identifying text fields as sensitive."""
    classifications = {}
    
    # Define which fields are sensitive
    sensitive_text_fields = {
        'first_name': 'first_name',
        'last_name': 'last_name',
        'email': 'email',
        'city': 'city'
    }
    
    for column in df.columns:
        if column in sensitive_text_fields:
            classifications[column] = FieldClassification(
                field_name=column,
                is_sensitive=True,
                sensitivity_type=sensitive_text_fields[column],
                confidence=0.95,
                reasoning=f'{column} contains personally identifiable information',
                recommended_strategy='bedrock_generation'
            )
        else:
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
        sensitive_fields=len(sensitive_text_fields),
        confidence_distribution={'high': len(sensitive_text_fields), 'medium': 0, 'low': len(df.columns) - len(sensitive_text_fields)}
    )


def main():
    """Run the Bedrock integration demo."""
    print("=" * 80)
    print("Synthetic Data Agent Demo - Bedrock Integration")
    print("=" * 80)
    print()
    
    # Check if AWS credentials are available
    print("Checking AWS credentials...")
    try:
        aws_config = AWSConfig()
        if not aws_config.verify_credentials():
            print("⚠️  AWS credentials not configured. Using fallback generator only.")
            print("   To use Bedrock, configure AWS credentials with:")
            print("   - AWS_PROFILE environment variable, or")
            print("   - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or")
            print("   - ~/.aws/credentials file")
            print()
            bedrock_client = None
        else:
            print("✓ AWS credentials verified")
            
            # Check Bedrock access
            if aws_config.verify_bedrock_access():
                print("✓ Amazon Bedrock access verified")
                print()
                
                # Initialize Bedrock client
                bedrock_runtime = aws_config.get_bedrock_client()
                bedrock_config = BedrockConfig(
                    model_id='anthropic.claude-3-haiku-20240307-v1:0',
                    temperature=0.9,
                    batch_size=10,  # Small batch for demo
                    max_retries=2
                )
                bedrock_client = BedrockClient(bedrock_runtime, bedrock_config)
                print(f"Bedrock client initialized with model: {bedrock_config.model_id}")
                print()
            else:
                print("⚠️  Amazon Bedrock access not available. Using fallback generator only.")
                print()
                bedrock_client = None
    except Exception as e:
        print(f"⚠️  Error initializing AWS: {e}")
        print("   Using fallback generator only.")
        print()
        bedrock_client = None
    
    # Step 1: Create sample production data
    print("Step 1: Creating sample production data with text fields...")
    production_data = create_sample_data_with_text_fields()
    print(f"Created {len(production_data)} production records")
    print(f"Columns: {list(production_data.columns)}")
    print()
    print("Sample production data:")
    print(production_data.head())
    print()
    
    # Step 2: Create sensitivity report
    print("Step 2: Creating sensitivity report...")
    sensitivity_report = create_sensitivity_report_with_text_fields(production_data)
    print(f"Total fields: {sensitivity_report.total_fields}")
    print(f"Sensitive fields: {sensitivity_report.sensitive_fields}")
    print()
    print("Sensitive text fields identified:")
    for field_name, classification in sensitivity_report.classifications.items():
        if classification.is_sensitive:
            print(f"  - {field_name} ({classification.sensitivity_type})")
    print()
    
    # Step 3: Initialize Synthetic Data Agent with Bedrock
    print("Step 3: Initializing Synthetic Data Agent with Bedrock integration...")
    agent = SyntheticDataAgent(
        bedrock_client=bedrock_client,
        bedrock_config=BedrockConfig() if bedrock_client else None
    )
    
    if bedrock_client:
        print("✓ Agent initialized with Bedrock client")
    else:
        print("✓ Agent initialized with fallback generator (Faker)")
    print()
    
    # Step 4: Generate synthetic data
    print("Step 4: Generating synthetic data...")
    print("Parameters:")
    print("  - Model: gaussian_copula (SDV for numeric fields)")
    if bedrock_client:
        print("  - Text generation: Amazon Bedrock (Claude 3 Haiku)")
    else:
        print("  - Text generation: Faker (rule-based fallback)")
    print("  - Number of rows: 15")
    print("  - Seed: 42")
    print()
    
    try:
        synthetic_dataset = agent.generate_synthetic_data(
            data=production_data,
            sensitivity_report=sensitivity_report,
            num_rows=15,
            sdv_model='gaussian_copula',
            seed=42
        )
        
        print("✓ Synthetic data generation complete!")
        print()
        
        # Step 5: Display results
        print("Step 5: Analyzing results...")
        print()
        print("Synthetic data sample:")
        print(synthetic_dataset.data.head(10))
        print()
        
        print("Quality Metrics:")
        print(f"  - Overall SDV Quality Score: {synthetic_dataset.quality_metrics.sdv_quality_score:.3f}")
        print(f"  - Column Shapes Score: {synthetic_dataset.quality_metrics.column_shapes_score:.3f}")
        print(f"  - Column Pair Trends Score: {synthetic_dataset.quality_metrics.column_pair_trends_score:.3f}")
        print(f"  - Correlation Preservation: {synthetic_dataset.quality_metrics.correlation_preservation:.3f}")
        print()
        
        # Step 6: Verify no data leakage
        print("Step 6: Verifying no data leakage in sensitive fields...")
        print()
        
        for field in ['first_name', 'last_name', 'email', 'city']:
            original_values = set(production_data[field].unique())
            synthetic_values = set(synthetic_dataset.data[field].unique())
            
            # Check for exact matches
            matches = original_values.intersection(synthetic_values)
            
            if matches:
                print(f"  ⚠️  {field}: {len(matches)} values match original data")
                print(f"      Matches: {list(matches)[:3]}")
            else:
                print(f"  ✓ {field}: No data leakage detected")
        print()
        
        # Step 7: Compare text field samples
        print("Step 7: Comparing text field samples...")
        print()
        print("Original vs Synthetic Names:")
        print("Original first names:", production_data['first_name'].head(5).tolist())
        print("Synthetic first names:", synthetic_dataset.data['first_name'].head(5).tolist())
        print()
        print("Original emails:", production_data['email'].head(3).tolist())
        print("Synthetic emails:", synthetic_dataset.data['email'].head(3).tolist())
        print()
        
        # Step 8: Save synthetic data
        output_dir = Path("data/synthetic")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "demo_bedrock_synthetic_data.csv"
        
        print(f"Step 8: Saving synthetic data to {output_path}...")
        agent.save_synthetic_data(synthetic_dataset, output_path, format='csv')
        print("✓ Synthetic data saved successfully!")
        print()
        
    except Exception as e:
        print(f"✗ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("1. Bedrock integration enables realistic text field generation")
    print("2. Fallback to rule-based generation (Faker) when Bedrock unavailable")
    print("3. Retry logic with exponential backoff handles transient failures")
    print("4. Batching optimizes API usage for large datasets")
    print("5. Context from related fields improves generation quality")
    print("6. No data leakage - all sensitive values are newly generated")
    print()
    
    if not bedrock_client:
        print("Note: To see Bedrock in action, configure AWS credentials and try again!")


if __name__ == "__main__":
    main()
