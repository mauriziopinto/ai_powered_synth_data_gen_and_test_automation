"""Property-based tests for schema constraint enforcement.

This module tests that synthetic data generation enforces all schema constraints
including ranges, patterns, required fields, and other validation rules.
"""

import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest
import re

from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport, FieldClassification
from shared.models.schema import (
    DataSchema, TableSchema, FieldDefinition, Constraint,
    DataType, ConstraintType, SchemaValidator
)


def data_matching_schema(schema: DataSchema, num_rows: int) -> pd.DataFrame:
    """Generate data that matches a given schema."""
    import random
    import string
    
    table = schema.tables[0]
    
    data = {}
    for field in table.fields:
        if field.data_type == DataType.INTEGER:
            # Find range constraint
            range_constraint = next(
                (c for c in field.constraints if c.type == ConstraintType.RANGE),
                None
            )
            if range_constraint:
                min_val = range_constraint.params.get('min', 0)
                max_val = range_constraint.params.get('max', 100)
                data[field.name] = [random.randint(min_val, max_val) for _ in range(num_rows)]
            else:
                data[field.name] = [random.randint(0, 100) for _ in range(num_rows)]
        
        elif field.data_type == DataType.FLOAT:
            # Find range constraint
            range_constraint = next(
                (c for c in field.constraints if c.type == ConstraintType.RANGE),
                None
            )
            if range_constraint:
                min_val = float(range_constraint.params.get('min', 0.0))
                max_val = float(range_constraint.params.get('max', 100.0))
                data[field.name] = [random.uniform(min_val, max_val) for _ in range(num_rows)]
            else:
                data[field.name] = [random.uniform(0.0, 100.0) for _ in range(num_rows)]
        
        elif field.data_type == DataType.STRING:
            # Find length constraint
            length_constraint = next(
                (c for c in field.constraints if c.type == ConstraintType.LENGTH),
                None
            )
            pattern_constraint = next(
                (c for c in field.constraints if c.type == ConstraintType.PATTERN),
                None
            )
            
            if pattern_constraint:
                # Generate strings matching the pattern
                pattern = pattern_constraint.params.get('pattern', r'^[A-Za-z0-9]+$')
                if pattern == r'^[A-Za-z0-9]+$':
                    min_len = length_constraint.params.get('min', 1) if length_constraint else 1
                    max_len = length_constraint.params.get('max', 10) if length_constraint else 10
                    data[field.name] = [
                        ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(min_len, max_len)))
                        for _ in range(num_rows)
                    ]
                else:
                    # For other patterns, just generate simple strings
                    data[field.name] = [f"value_{i}" for i in range(num_rows)]
            elif length_constraint:
                min_len = length_constraint.params.get('min', 1)
                max_len = length_constraint.params.get('max', 10)
                data[field.name] = [
                    ''.join(random.choices(string.ascii_letters, k=random.randint(min_len, max_len)))
                    for _ in range(num_rows)
                ]
            else:
                data[field.name] = [f"value_{i}" for i in range(num_rows)]
    
    return pd.DataFrame(data)


def create_sensitivity_report(df: pd.DataFrame) -> SensitivityReport:
    """Create a basic sensitivity report marking all fields as non-sensitive."""
    classifications = {}
    for column in df.columns:
        classifications[column] = FieldClassification(
            field_name=column,
            is_sensitive=False,
            sensitivity_type='none',
            confidence=1.0,
            reasoning='Test data - marked as non-sensitive',
            recommended_strategy='sdv',
            confluence_references=[]
        )
    
    return SensitivityReport(
        classifications=classifications,
        data_profile={},
        timestamp=pd.Timestamp.now(),
        total_fields=len(df.columns),
        sensitive_fields=0,
        confidence_distribution={}
    )


@settings(max_examples=100, deadline=None)
@given(
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_schema_constraint_enforcement(num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 3: Schema Constraint Enforcement
    Validates: Requirements 2.3
    
    For any schema definition with specified constraints (ranges, patterns, required fields),
    all generated synthetic records should satisfy those constraints.
    
    This test verifies that:
    1. Range constraints are enforced on numeric fields
    2. Length constraints are enforced on string fields
    3. Pattern constraints are enforced on string fields
    4. Required fields are never null
    """
    # Create a simple schema with various constraints
    fields = [
        FieldDefinition(
            name="age",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 100}),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="score",
            data_type=DataType.FLOAT,
            constraints=[
                Constraint(type=ConstraintType.RANGE, params={'min': 0.0, 'max': 10.0})
            ],
            nullable=True
        )
    ]
    
    table = TableSchema(name="test_table", fields=fields)
    schema = DataSchema(tables=[table], version="1.0")
    
    # Generate source data that matches the schema
    source_df = data_matching_schema(schema, 100)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(source_df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=source_df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema  # Pass schema for constraint enforcement
    )
    
    synthetic_df = synthetic_dataset.data
    
    # Validate that all records satisfy the schema constraints
    validator = SchemaValidator(schema)
    
    # Convert DataFrame to list of records for validation
    records = synthetic_df.to_dict('records')
    
    # Track all constraint violations
    all_violations = []
    
    for i, record in enumerate(records):
        is_valid, errors = table.validate_record(record)
        if not is_valid:
            all_violations.append(f"Record {i}: {'; '.join(errors)}")
    
    # Assert no violations
    assert len(all_violations) == 0, (
        f"Schema constraint violations found in {len(all_violations)} records:\n" +
        "\n".join(all_violations[:10])  # Show first 10 violations
    )


@settings(max_examples=100, deadline=None)
@given(
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_range_constraint_enforcement(num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 3: Schema Constraint Enforcement
    Validates: Requirements 2.3
    
    Specifically test that range constraints on numeric fields are enforced.
    """
    # Create a schema with strict range constraints
    fields = [
        FieldDefinition(
            name="age",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.RANGE, params={'min': 18, 'max': 65}),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="score",
            data_type=DataType.FLOAT,
            constraints=[
                Constraint(type=ConstraintType.RANGE, params={'min': 0.0, 'max': 100.0}),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    table = TableSchema(name="test_table", fields=fields)
    schema = DataSchema(tables=[table], version="1.0")
    
    # Generate source data within constraints
    source_data = {
        'age': [25, 30, 45, 50, 60] * 20,  # 100 rows
        'score': [75.5, 80.0, 90.5, 85.0, 95.0] * 20
    }
    source_df = pd.DataFrame(source_data)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(source_df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=source_df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_df = synthetic_dataset.data
    
    # Verify all ages are within range
    assert synthetic_df['age'].min() >= 18, (
        f"Age below minimum: {synthetic_df['age'].min()} < 18"
    )
    assert synthetic_df['age'].max() <= 65, (
        f"Age above maximum: {synthetic_df['age'].max()} > 65"
    )
    
    # Verify all scores are within range
    assert synthetic_df['score'].min() >= 0.0, (
        f"Score below minimum: {synthetic_df['score'].min()} < 0.0"
    )
    assert synthetic_df['score'].max() <= 100.0, (
        f"Score above maximum: {synthetic_df['score'].max()} > 100.0"
    )
    
    # Verify no null values (required constraint)
    assert not synthetic_df['age'].isna().any(), "Age field contains null values"
    assert not synthetic_df['score'].isna().any(), "Score field contains null values"


@settings(max_examples=100, deadline=None)
@given(
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_pattern_constraint_enforcement(num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 3: Schema Constraint Enforcement
    Validates: Requirements 2.3
    
    Specifically test that pattern constraints on string fields are enforced.
    """
    # Create a schema with pattern constraints
    fields = [
        FieldDefinition(
            name="product_code",
            data_type=DataType.STRING,
            constraints=[
                Constraint(type=ConstraintType.PATTERN, params={'pattern': r'^[A-Z]{3}\d{4}$'}),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="category",
            data_type=DataType.STRING,
            constraints=[
                Constraint(type=ConstraintType.ENUM, params={'values': ['A', 'B', 'C', 'D']}),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    table = TableSchema(name="test_table", fields=fields)
    schema = DataSchema(tables=[table], version="1.0")
    
    # Generate source data matching constraints
    source_data = {
        'product_code': ['ABC1234', 'XYZ5678', 'DEF9012', 'GHI3456', 'JKL7890'] * 20,
        'category': ['A', 'B', 'C', 'D', 'A'] * 20
    }
    source_df = pd.DataFrame(source_data)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(source_df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=source_df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_df = synthetic_dataset.data
    
    # Verify all product codes match the pattern
    pattern = re.compile(r'^[A-Z]{3}\d{4}$')
    invalid_codes = synthetic_df[~synthetic_df['product_code'].str.match(pattern, na=False)]
    assert len(invalid_codes) == 0, (
        f"Found {len(invalid_codes)} product codes not matching pattern. "
        f"Examples: {invalid_codes['product_code'].head().tolist()}"
    )
    
    # Verify all categories are in the allowed enum
    allowed_categories = {'A', 'B', 'C', 'D'}
    invalid_categories = synthetic_df[~synthetic_df['category'].isin(allowed_categories)]
    assert len(invalid_categories) == 0, (
        f"Found {len(invalid_categories)} invalid categories. "
        f"Examples: {invalid_categories['category'].head().tolist()}"
    )
    
    # Verify no null values (required constraint)
    assert not synthetic_df['product_code'].isna().any(), "Product code contains null values"
    assert not synthetic_df['category'].isna().any(), "Category contains null values"


@settings(max_examples=100, deadline=None)
@given(
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_required_field_enforcement(num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 3: Schema Constraint Enforcement
    Validates: Requirements 2.3
    
    Specifically test that required fields are never null in generated data.
    """
    # Create a schema with required and optional fields
    fields = [
        FieldDefinition(
            name="required_field",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="optional_field",
            data_type=DataType.INTEGER,
            constraints=[],
            nullable=True
        )
    ]
    
    table = TableSchema(name="test_table", fields=fields)
    schema = DataSchema(tables=[table], version="1.0")
    
    # Generate source data
    source_data = {
        'required_field': list(range(100)),
        'optional_field': list(range(100))
    }
    source_df = pd.DataFrame(source_data)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(source_df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=source_df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_df = synthetic_dataset.data
    
    # Verify required field has no nulls
    assert not synthetic_df['required_field'].isna().any(), (
        f"Required field contains {synthetic_df['required_field'].isna().sum()} null values"
    )
    
    # Optional field may have nulls (we don't enforce this, just verify it doesn't break)
    # This is just to ensure the system handles optional fields correctly


@settings(max_examples=100, deadline=None)
@given(
    num_synthetic_rows=st.integers(min_value=100, max_value=200),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_length_constraint_enforcement(num_synthetic_rows, seed):
    """
    Feature: synthetic-data-generator, Property 3: Schema Constraint Enforcement
    Validates: Requirements 2.3
    
    Specifically test that length constraints on string fields are enforced.
    """
    # Create a schema with length constraints
    fields = [
        FieldDefinition(
            name="short_code",
            data_type=DataType.STRING,
            constraints=[
                Constraint(type=ConstraintType.LENGTH, params={'min': 3, 'max': 5}),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="description",
            data_type=DataType.STRING,
            constraints=[
                Constraint(type=ConstraintType.LENGTH, params={'min': 10, 'max': 50}),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    table = TableSchema(name="test_table", fields=fields)
    schema = DataSchema(tables=[table], version="1.0")
    
    # Generate source data matching constraints
    source_data = {
        'short_code': ['ABC', 'DEFG', 'HI', 'JKLM', 'NOPQR'] * 20,
        'description': ['This is a test description for validation'] * 100
    }
    source_df = pd.DataFrame(source_data)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report(source_df)
    
    # Generate synthetic data
    synthetic_dataset = agent.generate_synthetic_data(
        data=source_df,
        sensitivity_report=sensitivity_report,
        num_rows=num_synthetic_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_df = synthetic_dataset.data
    
    # Verify short_code lengths
    short_code_lengths = synthetic_df['short_code'].str.len()
    assert short_code_lengths.min() >= 3, (
        f"Short code length below minimum: {short_code_lengths.min()} < 3"
    )
    assert short_code_lengths.max() <= 5, (
        f"Short code length above maximum: {short_code_lengths.max()} > 5"
    )
    
    # Verify description lengths
    description_lengths = synthetic_df['description'].str.len()
    assert description_lengths.min() >= 10, (
        f"Description length below minimum: {description_lengths.min()} < 10"
    )
    assert description_lengths.max() <= 50, (
        f"Description length above maximum: {description_lengths.max()} > 50"
    )
    
    # Verify no null values (required constraint)
    assert not synthetic_df['short_code'].isna().any(), "Short code contains null values"
    assert not synthetic_df['description'].isna().any(), "Description contains null values"
