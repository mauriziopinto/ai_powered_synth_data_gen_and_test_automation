"""Demo script for edge case generation functionality."""

import pandas as pd
import numpy as np
from datetime import datetime

from shared.utils.edge_case_generator import (
    EdgeCaseGenerator,
    EdgeCaseRule,
    EdgeCaseType,
    EdgeCasePatternLibrary
)


def main():
    """Demonstrate edge case generation."""
    print("=" * 80)
    print("Edge Case Generation Demo")
    print("=" * 80)
    print()
    
    # Create sample data
    print("Creating sample data...")
    data = pd.DataFrame({
        'customer_id': range(1, 101),
        'email': [f'user{i}@example.com' for i in range(1, 101)],
        'phone': [f'555-{i:04d}' for i in range(1, 101)],
        'postcode': [f'{i:05d}' for i in range(1, 101)],
        'age': np.random.randint(18, 80, 100),
        'balance': np.random.uniform(0, 10000, 100).round(2),
        'name': [f'Customer {i}' for i in range(1, 101)]
    })
    
    print(f"Created {len(data)} records with {len(data.columns)} columns")
    print(f"Columns: {list(data.columns)}")
    print()
    
    # Initialize edge case generator
    print("Initializing edge case generator...")
    generator = EdgeCaseGenerator()
    print()
    
    # Display available patterns
    print("Available edge case patterns:")
    pattern_library = generator.pattern_library
    for edge_case_type, pattern in pattern_library.patterns.items():
        print(f"  - {pattern.name} ({edge_case_type.value})")
        print(f"    Description: {pattern.description}")
        print(f"    Applicable types: {pattern.applicable_types or 'all'}")
    print()
    
    # Define edge case rules
    print("Defining edge case rules...")
    rules = [
        EdgeCaseRule(
            field_name='email',
            edge_case_types=[
                EdgeCaseType.MALFORMED_EMAIL,
                EdgeCaseType.EMPTY_STRING,
                EdgeCaseType.NULL_VALUE
            ],
            frequency=0.10,  # 10% of records
            field_type='email'
        ),
        EdgeCaseRule(
            field_name='phone',
            edge_case_types=[
                EdgeCaseType.MALFORMED_PHONE,
                EdgeCaseType.NULL_VALUE
            ],
            frequency=0.08,  # 8% of records
            field_type='phone'
        ),
        EdgeCaseRule(
            field_name='postcode',
            edge_case_types=[
                EdgeCaseType.INVALID_POSTCODE,
                EdgeCaseType.EMPTY_STRING
            ],
            frequency=0.05,  # 5% of records
            field_type='postcode'
        ),
        EdgeCaseRule(
            field_name='age',
            edge_case_types=[
                EdgeCaseType.NEGATIVE_VALUE,
                EdgeCaseType.ZERO_VALUE,
                EdgeCaseType.BOUNDARY_VALUE
            ],
            frequency=0.03,  # 3% of records
            field_type='number'
        ),
        EdgeCaseRule(
            field_name='balance',
            edge_case_types=[
                EdgeCaseType.NEGATIVE_VALUE,
                EdgeCaseType.ZERO_VALUE
            ],
            frequency=0.07,  # 7% of records
            field_type='number'
        ),
        EdgeCaseRule(
            field_name='name',
            edge_case_types=[
                EdgeCaseType.EMPTY_STRING,
                EdgeCaseType.WHITESPACE_ONLY,
                EdgeCaseType.SPECIAL_CHARACTERS
            ],
            frequency=0.06,  # 6% of records
            field_type='string'
        )
    ]
    
    for rule in rules:
        print(f"  - Field: {rule.field_name}")
        print(f"    Edge case types: {[ect.value for ect in rule.edge_case_types]}")
        print(f"    Frequency: {rule.frequency:.1%}")
    print()
    
    # Inject edge cases
    print("Injecting edge cases...")
    result_df, injection_result = generator.inject_edge_cases(
        data=data,
        rules=rules,
        seed=42
    )
    print()
    
    # Display results
    print("Injection Results:")
    print(f"  Total records: {injection_result.total_records}")
    print(f"  Records with edge cases: {injection_result.injected_count}")
    print(f"  Frequency achieved: {injection_result.frequency_achieved:.2%}")
    print()
    
    # Validate frequency
    print("Validating frequency...")
    # Calculate overall target frequency (weighted average)
    total_target_injections = sum(len(data) * rule.frequency for rule in rules)
    target_frequency = total_target_injections / len(data)
    
    is_valid = generator.validate_frequency(
        result=injection_result,
        target_frequency=target_frequency,
        tolerance=0.05
    )
    print(f"  Target frequency: {target_frequency:.2%}")
    print(f"  Achieved frequency: {injection_result.frequency_achieved:.2%}")
    print(f"  Validation: {'PASSED' if is_valid else 'FAILED'}")
    print()
    
    # Show examples of injected edge cases
    print("Examples of injected edge cases:")
    print()
    
    # Get records with edge cases
    edge_case_indices = injection_result.injected_indices[:10]  # Show first 10
    
    for idx in edge_case_indices:
        print(f"Record {idx}:")
        print(f"  Original data: {data.iloc[idx].to_dict()}")
        print(f"  Modified data: {result_df.iloc[idx].drop('_edge_case_tags').to_dict()}")
        
        # Show edge case tags
        tags = result_df.at[idx, '_edge_case_tags']
        if tags:
            print(f"  Edge case tags:")
            for tag in tags:
                print(f"    - Field: {tag['field']}, Type: {tag['type']}")
                print(f"      Description: {tag['description']}")
        print()
    
    # Show statistics by field
    print("Edge case statistics by field:")
    for rule in rules:
        field_name = rule.field_name
        
        # Count how many records have edge cases for this field
        count = sum(
            1 for idx in injection_result.injected_indices
            if any(tag['field'] == field_name for tag in result_df.at[idx, '_edge_case_tags'])
        )
        
        actual_frequency = count / len(data)
        print(f"  {field_name}:")
        print(f"    Target: {rule.frequency:.2%}, Actual: {actual_frequency:.2%}")
        print(f"    Count: {count} records")
    print()
    
    # Save results
    output_path = 'data/synthetic/edge_case_demo.csv'
    print(f"Saving results to {output_path}...")
    result_df.to_csv(output_path, index=False)
    print("Done!")
    print()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
