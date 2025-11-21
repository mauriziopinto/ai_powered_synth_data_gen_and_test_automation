"""Property-based tests for referential integrity preservation.

This module tests that synthetic data generation maintains referential integrity
across tables with foreign key relationships.
"""

import pandas as pd
from hypothesis import given, strategies as st, settings
import pytest

from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport, FieldClassification
from shared.models.schema import (
    DataSchema, TableSchema, FieldDefinition, Constraint,
    DataType, ConstraintType, ForeignKeyRelationship
)


def create_sensitivity_report_for_tables(tables_data: dict) -> dict:
    """Create sensitivity reports for multiple tables."""
    reports = {}
    for table_name, df in tables_data.items():
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
        
        reports[table_name] = SensitivityReport(
            classifications=classifications,
            data_profile={},
            timestamp=pd.Timestamp.now(),
            total_fields=len(df.columns),
            sensitive_fields=0,
            confidence_distribution={}
        )
    
    return reports


@settings(max_examples=100, deadline=None)
@given(
    num_parent_rows=st.integers(min_value=10, max_value=50),
    num_child_rows=st.integers(min_value=20, max_value=100),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_referential_integrity_preservation(num_parent_rows, num_child_rows, seed):
    """
    Feature: synthetic-data-generator, Property 4: Referential Integrity Preservation
    Validates: Requirements 2.4
    
    For any schema with foreign key relationships, all foreign key values in generated
    synthetic data should reference existing primary key values.
    
    This test verifies that:
    1. All foreign key values exist in the referenced table's primary key column
    2. No orphaned records are created (child records without valid parent references)
    3. The relationship structure is maintained across generation
    """
    # Create a schema with parent-child relationship
    # Parent table: departments
    parent_fields = [
        FieldDefinition(
            name="dept_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="dept_name",
            data_type=DataType.STRING,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    parent_table = TableSchema(
        name="departments",
        fields=parent_fields,
        primary_key="dept_id"
    )
    
    # Child table: employees (references departments)
    child_fields = [
        FieldDefinition(
            name="emp_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="emp_name",
            data_type=DataType.STRING,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="dept_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    params={
                        'target_table': 'departments',
                        'target_field': 'dept_id'
                    }
                ),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    child_table = TableSchema(
        name="employees",
        fields=child_fields,
        primary_key="emp_id"
    )
    
    schema = DataSchema(
        tables=[parent_table, child_table],
        version="1.0"
    )
    
    # Generate source data with valid relationships
    parent_data = {
        'dept_id': list(range(1, num_parent_rows + 1)),
        'dept_name': [f"Department_{i}" for i in range(1, num_parent_rows + 1)]
    }
    parent_df = pd.DataFrame(parent_data)
    
    # Child data references parent dept_ids
    import random
    random.seed(seed)
    child_data = {
        'emp_id': list(range(1, num_child_rows + 1)),
        'emp_name': [f"Employee_{i}" for i in range(1, num_child_rows + 1)],
        'dept_id': [random.choice(parent_data['dept_id']) for _ in range(num_child_rows)]
    }
    child_df = pd.DataFrame(child_data)
    
    # Create agent and sensitivity reports
    agent = SyntheticDataAgent()
    tables_data = {
        'departments': parent_df,
        'employees': child_df
    }
    sensitivity_reports = create_sensitivity_report_for_tables(tables_data)
    
    # Generate synthetic data for both tables
    synthetic_parent = agent.generate_synthetic_data(
        data=parent_df,
        sensitivity_report=sensitivity_reports['departments'],
        num_rows=num_parent_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_parent_df = synthetic_parent.data
    
    synthetic_child = agent.generate_synthetic_data(
        data=child_df,
        sensitivity_report=sensitivity_reports['employees'],
        num_rows=num_child_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema,
        referenced_data={'departments': synthetic_parent_df}
    )
    
    synthetic_child_df = synthetic_child.data
    
    # Validate referential integrity
    # Get all valid parent dept_ids
    valid_dept_ids = set(synthetic_parent_df['dept_id'].dropna().unique())
    
    # Check that all child dept_ids reference valid parent dept_ids
    child_dept_ids = synthetic_child_df['dept_id'].dropna()
    invalid_references = child_dept_ids[~child_dept_ids.isin(valid_dept_ids)]
    
    assert len(invalid_references) == 0, (
        f"Found {len(invalid_references)} foreign key violations in employees table. "
        f"Invalid dept_id values: {invalid_references.unique().tolist()[:10]}. "
        f"Valid dept_ids: {sorted(valid_dept_ids)[:10]}"
    )
    
    # Verify no null foreign keys (since it's required)
    null_fk_count = synthetic_child_df['dept_id'].isna().sum()
    assert null_fk_count == 0, (
        f"Found {null_fk_count} null foreign key values in required field 'dept_id'"
    )


@settings(max_examples=100, deadline=None)
@given(
    num_rows_a=st.integers(min_value=10, max_value=30),
    num_rows_b=st.integers(min_value=10, max_value=30),
    num_rows_c=st.integers(min_value=20, max_value=60),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_multi_level_referential_integrity(num_rows_a, num_rows_b, num_rows_c, seed):
    """
    Feature: synthetic-data-generator, Property 4: Referential Integrity Preservation
    Validates: Requirements 2.4
    
    Test referential integrity with multi-level relationships (A -> B -> C).
    Verifies that transitive relationships are maintained.
    """
    # Create a three-level hierarchy: countries -> states -> cities
    
    # Level 1: countries
    country_fields = [
        FieldDefinition(
            name="country_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="country_name",
            data_type=DataType.STRING,
            constraints=[Constraint(type=ConstraintType.REQUIRED, params={})],
            nullable=False
        )
    ]
    
    country_table = TableSchema(
        name="countries",
        fields=country_fields,
        primary_key="country_id"
    )
    
    # Level 2: states (references countries)
    state_fields = [
        FieldDefinition(
            name="state_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="state_name",
            data_type=DataType.STRING,
            constraints=[Constraint(type=ConstraintType.REQUIRED, params={})],
            nullable=False
        ),
        FieldDefinition(
            name="country_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    params={'target_table': 'countries', 'target_field': 'country_id'}
                ),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    state_table = TableSchema(
        name="states",
        fields=state_fields,
        primary_key="state_id"
    )
    
    # Level 3: cities (references states)
    city_fields = [
        FieldDefinition(
            name="city_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="city_name",
            data_type=DataType.STRING,
            constraints=[Constraint(type=ConstraintType.REQUIRED, params={})],
            nullable=False
        ),
        FieldDefinition(
            name="state_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    params={'target_table': 'states', 'target_field': 'state_id'}
                ),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    city_table = TableSchema(
        name="cities",
        fields=city_fields,
        primary_key="city_id"
    )
    
    schema = DataSchema(
        tables=[country_table, state_table, city_table],
        version="1.0"
    )
    
    # Generate source data with valid relationships
    import random
    random.seed(seed)
    
    country_data = {
        'country_id': list(range(1, num_rows_a + 1)),
        'country_name': [f"Country_{i}" for i in range(1, num_rows_a + 1)]
    }
    country_df = pd.DataFrame(country_data)
    
    state_data = {
        'state_id': list(range(1, num_rows_b + 1)),
        'state_name': [f"State_{i}" for i in range(1, num_rows_b + 1)],
        'country_id': [random.choice(country_data['country_id']) for _ in range(num_rows_b)]
    }
    state_df = pd.DataFrame(state_data)
    
    city_data = {
        'city_id': list(range(1, num_rows_c + 1)),
        'city_name': [f"City_{i}" for i in range(1, num_rows_c + 1)],
        'state_id': [random.choice(state_data['state_id']) for _ in range(num_rows_c)]
    }
    city_df = pd.DataFrame(city_data)
    
    # Create agent and sensitivity reports
    agent = SyntheticDataAgent()
    tables_data = {
        'countries': country_df,
        'states': state_df,
        'cities': city_df
    }
    sensitivity_reports = create_sensitivity_report_for_tables(tables_data)
    
    # Generate synthetic data for all three tables
    synthetic_countries = agent.generate_synthetic_data(
        data=country_df,
        sensitivity_report=sensitivity_reports['countries'],
        num_rows=num_rows_a,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_states = agent.generate_synthetic_data(
        data=state_df,
        sensitivity_report=sensitivity_reports['states'],
        num_rows=num_rows_b,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema,
        referenced_data={'countries': synthetic_countries.data}
    )
    
    synthetic_cities = agent.generate_synthetic_data(
        data=city_df,
        sensitivity_report=sensitivity_reports['cities'],
        num_rows=num_rows_c,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema,
        referenced_data={'states': synthetic_states.data}
    )
    
    # Validate referential integrity at each level
    valid_country_ids = set(synthetic_countries.data['country_id'].dropna().unique())
    valid_state_ids = set(synthetic_states.data['state_id'].dropna().unique())
    
    # Check states -> countries relationship
    state_country_refs = synthetic_states.data['country_id'].dropna()
    invalid_state_refs = state_country_refs[~state_country_refs.isin(valid_country_ids)]
    
    assert len(invalid_state_refs) == 0, (
        f"Found {len(invalid_state_refs)} foreign key violations in states table. "
        f"Invalid country_id values: {invalid_state_refs.unique().tolist()}"
    )
    
    # Check cities -> states relationship
    city_state_refs = synthetic_cities.data['state_id'].dropna()
    invalid_city_refs = city_state_refs[~city_state_refs.isin(valid_state_ids)]
    
    assert len(invalid_city_refs) == 0, (
        f"Found {len(invalid_city_refs)} foreign key violations in cities table. "
        f"Invalid state_id values: {invalid_city_refs.unique().tolist()}"
    )


@settings(max_examples=100, deadline=None)
@given(
    num_students=st.integers(min_value=20, max_value=50),
    num_courses=st.integers(min_value=5, max_value=15),
    num_enrollments=st.integers(min_value=30, max_value=100),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_many_to_many_referential_integrity(num_students, num_courses, num_enrollments, seed):
    """
    Feature: synthetic-data-generator, Property 4: Referential Integrity Preservation
    Validates: Requirements 2.4
    
    Test referential integrity with many-to-many relationships through a junction table.
    Verifies that both foreign keys in the junction table reference valid records.
    """
    # Create a many-to-many relationship: students <-> enrollments <-> courses
    
    # Students table
    student_fields = [
        FieldDefinition(
            name="student_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="student_name",
            data_type=DataType.STRING,
            constraints=[Constraint(type=ConstraintType.REQUIRED, params={})],
            nullable=False
        )
    ]
    
    student_table = TableSchema(
        name="students",
        fields=student_fields,
        primary_key="student_id"
    )
    
    # Courses table
    course_fields = [
        FieldDefinition(
            name="course_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="course_name",
            data_type=DataType.STRING,
            constraints=[Constraint(type=ConstraintType.REQUIRED, params={})],
            nullable=False
        )
    ]
    
    course_table = TableSchema(
        name="courses",
        fields=course_fields,
        primary_key="course_id"
    )
    
    # Enrollments junction table (references both students and courses)
    enrollment_fields = [
        FieldDefinition(
            name="enrollment_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="student_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    params={'target_table': 'students', 'target_field': 'student_id'}
                ),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="course_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    params={'target_table': 'courses', 'target_field': 'course_id'}
                ),
                Constraint(type=ConstraintType.REQUIRED, params={})
            ],
            nullable=False
        )
    ]
    
    enrollment_table = TableSchema(
        name="enrollments",
        fields=enrollment_fields,
        primary_key="enrollment_id"
    )
    
    schema = DataSchema(
        tables=[student_table, course_table, enrollment_table],
        version="1.0"
    )
    
    # Generate source data with valid relationships
    import random
    random.seed(seed)
    
    student_data = {
        'student_id': list(range(1, num_students + 1)),
        'student_name': [f"Student_{i}" for i in range(1, num_students + 1)]
    }
    student_df = pd.DataFrame(student_data)
    
    course_data = {
        'course_id': list(range(1, num_courses + 1)),
        'course_name': [f"Course_{i}" for i in range(1, num_courses + 1)]
    }
    course_df = pd.DataFrame(course_data)
    
    enrollment_data = {
        'enrollment_id': list(range(1, num_enrollments + 1)),
        'student_id': [random.choice(student_data['student_id']) for _ in range(num_enrollments)],
        'course_id': [random.choice(course_data['course_id']) for _ in range(num_enrollments)]
    }
    enrollment_df = pd.DataFrame(enrollment_data)
    
    # Create agent and sensitivity reports
    agent = SyntheticDataAgent()
    tables_data = {
        'students': student_df,
        'courses': course_df,
        'enrollments': enrollment_df
    }
    sensitivity_reports = create_sensitivity_report_for_tables(tables_data)
    
    # Generate synthetic data for all tables
    synthetic_students = agent.generate_synthetic_data(
        data=student_df,
        sensitivity_report=sensitivity_reports['students'],
        num_rows=num_students,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_courses = agent.generate_synthetic_data(
        data=course_df,
        sensitivity_report=sensitivity_reports['courses'],
        num_rows=num_courses,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_enrollments = agent.generate_synthetic_data(
        data=enrollment_df,
        sensitivity_report=sensitivity_reports['enrollments'],
        num_rows=num_enrollments,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema,
        referenced_data={
            'students': synthetic_students.data,
            'courses': synthetic_courses.data
        }
    )
    
    # Validate referential integrity for both foreign keys
    valid_student_ids = set(synthetic_students.data['student_id'].dropna().unique())
    valid_course_ids = set(synthetic_courses.data['course_id'].dropna().unique())
    
    # Check enrollments -> students relationship
    enrollment_student_refs = synthetic_enrollments.data['student_id'].dropna()
    invalid_student_refs = enrollment_student_refs[~enrollment_student_refs.isin(valid_student_ids)]
    
    assert len(invalid_student_refs) == 0, (
        f"Found {len(invalid_student_refs)} foreign key violations for student_id in enrollments. "
        f"Invalid values: {invalid_student_refs.unique().tolist()}"
    )
    
    # Check enrollments -> courses relationship
    enrollment_course_refs = synthetic_enrollments.data['course_id'].dropna()
    invalid_course_refs = enrollment_course_refs[~enrollment_course_refs.isin(valid_course_ids)]
    
    assert len(invalid_course_refs) == 0, (
        f"Found {len(invalid_course_refs)} foreign key violations for course_id in enrollments. "
        f"Invalid values: {invalid_course_refs.unique().tolist()}"
    )


@settings(max_examples=100, deadline=None)
@given(
    num_rows=st.integers(min_value=50, max_value=150),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_self_referential_integrity(num_rows, seed):
    """
    Feature: synthetic-data-generator, Property 4: Referential Integrity Preservation
    Validates: Requirements 2.4
    
    Test referential integrity with self-referencing foreign keys (e.g., employee -> manager).
    Verifies that self-references point to valid records in the same table.
    """
    # Create a self-referencing table: employees with manager_id
    employee_fields = [
        FieldDefinition(
            name="emp_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED, params={}),
                Constraint(type=ConstraintType.UNIQUE, params={})
            ],
            nullable=False
        ),
        FieldDefinition(
            name="emp_name",
            data_type=DataType.STRING,
            constraints=[Constraint(type=ConstraintType.REQUIRED, params={})],
            nullable=False
        ),
        FieldDefinition(
            name="manager_id",
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    params={'target_table': 'employees', 'target_field': 'emp_id'}
                )
            ],
            nullable=True  # Top-level employees have no manager
        )
    ]
    
    employee_table = TableSchema(
        name="employees",
        fields=employee_fields,
        primary_key="emp_id"
    )
    
    schema = DataSchema(
        tables=[employee_table],
        version="1.0"
    )
    
    # Generate source data with valid self-references
    import random
    random.seed(seed)
    
    emp_ids = list(range(1, num_rows + 1))
    
    # Create a hierarchy: some employees have no manager (top level),
    # others reference earlier employees as managers
    manager_ids = []
    for i, emp_id in enumerate(emp_ids):
        if i < 5:  # First 5 are top-level (no manager)
            manager_ids.append(None)
        else:
            # Reference one of the earlier employees
            manager_ids.append(random.choice(emp_ids[:i]))
    
    employee_data = {
        'emp_id': emp_ids,
        'emp_name': [f"Employee_{i}" for i in emp_ids],
        'manager_id': manager_ids
    }
    employee_df = pd.DataFrame(employee_data)
    
    # Create agent and sensitivity report
    agent = SyntheticDataAgent()
    sensitivity_report = create_sensitivity_report_for_tables({'employees': employee_df})['employees']
    
    # Generate synthetic data
    synthetic_employees = agent.generate_synthetic_data(
        data=employee_df,
        sensitivity_report=sensitivity_report,
        num_rows=num_rows,
        sdv_model='gaussian_copula',
        seed=seed,
        schema=schema
    )
    
    synthetic_df = synthetic_employees.data
    
    # Validate self-referential integrity
    valid_emp_ids = set(synthetic_df['emp_id'].dropna().unique())
    
    # Check that all non-null manager_ids reference valid emp_ids
    manager_refs = synthetic_df['manager_id'].dropna()
    invalid_manager_refs = manager_refs[~manager_refs.isin(valid_emp_ids)]
    
    assert len(invalid_manager_refs) == 0, (
        f"Found {len(invalid_manager_refs)} self-referential foreign key violations. "
        f"Invalid manager_id values: {invalid_manager_refs.unique().tolist()[:10]}. "
        f"Valid emp_ids: {sorted(valid_emp_ids)[:10]}"
    )
