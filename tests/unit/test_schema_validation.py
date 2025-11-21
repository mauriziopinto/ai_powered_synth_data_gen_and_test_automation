"""Unit tests for schema validation."""

import json
import pytest
from shared.models.schema import (
    DataType,
    ConstraintType,
    Constraint,
    ForeignKeyRelationship,
    FieldDefinition,
    TableSchema,
    DataSchema,
    SchemaValidator
)


@pytest.mark.unit
class TestConstraint:
    """Test constraint validation."""
    
    def test_range_constraint_valid(self):
        """Test range constraint with valid value."""
        constraint = Constraint(
            type=ConstraintType.RANGE,
            params={'min': 0, 'max': 100}
        )
        is_valid, error = constraint.validate(50, 'age')
        assert is_valid
        assert error is None
    
    def test_range_constraint_below_min(self):
        """Test range constraint with value below minimum."""
        constraint = Constraint(
            type=ConstraintType.RANGE,
            params={'min': 0, 'max': 100}
        )
        is_valid, error = constraint.validate(-5, 'age')
        assert not is_valid
        assert 'below minimum' in error
    
    def test_range_constraint_above_max(self):
        """Test range constraint with value above maximum."""
        constraint = Constraint(
            type=ConstraintType.RANGE,
            params={'min': 0, 'max': 100}
        )
        is_valid, error = constraint.validate(150, 'age')
        assert not is_valid
        assert 'exceeds maximum' in error
    
    def test_pattern_constraint_valid(self):
        """Test pattern constraint with valid value."""
        constraint = Constraint(
            type=ConstraintType.PATTERN,
            params={'pattern': r'^[A-Z]{2}\d{4}$'}
        )
        is_valid, error = constraint.validate('AB1234', 'code')
        assert is_valid
        assert error is None
    
    def test_pattern_constraint_invalid(self):
        """Test pattern constraint with invalid value."""
        constraint = Constraint(
            type=ConstraintType.PATTERN,
            params={'pattern': r'^[A-Z]{2}\d{4}$'}
        )
        is_valid, error = constraint.validate('invalid', 'code')
        assert not is_valid
        assert 'does not match pattern' in error
    
    def test_enum_constraint_valid(self):
        """Test enum constraint with valid value."""
        constraint = Constraint(
            type=ConstraintType.ENUM,
            params={'values': ['red', 'green', 'blue']}
        )
        is_valid, error = constraint.validate('red', 'color')
        assert is_valid
        assert error is None
    
    def test_enum_constraint_invalid(self):
        """Test enum constraint with invalid value."""
        constraint = Constraint(
            type=ConstraintType.ENUM,
            params={'values': ['red', 'green', 'blue']}
        )
        is_valid, error = constraint.validate('yellow', 'color')
        assert not is_valid
        assert 'not in allowed values' in error
    
    def test_length_constraint_valid(self):
        """Test length constraint with valid value."""
        constraint = Constraint(
            type=ConstraintType.LENGTH,
            params={'min': 3, 'max': 10}
        )
        is_valid, error = constraint.validate('hello', 'name')
        assert is_valid
        assert error is None
    
    def test_length_constraint_too_short(self):
        """Test length constraint with value too short."""
        constraint = Constraint(
            type=ConstraintType.LENGTH,
            params={'min': 3, 'max': 10}
        )
        is_valid, error = constraint.validate('ab', 'name')
        assert not is_valid
        assert 'below minimum' in error
    
    def test_length_constraint_too_long(self):
        """Test length constraint with value too long."""
        constraint = Constraint(
            type=ConstraintType.LENGTH,
            params={'min': 3, 'max': 10}
        )
        is_valid, error = constraint.validate('verylongname', 'name')
        assert not is_valid
        assert 'exceeds maximum' in error
    
    def test_required_constraint_with_none(self):
        """Test required constraint with None value."""
        constraint = Constraint(type=ConstraintType.REQUIRED)
        is_valid, error = constraint.validate(None, 'required_field')
        assert not is_valid
        assert 'required' in error.lower()
    
    def test_required_constraint_with_value(self):
        """Test required constraint with valid value."""
        constraint = Constraint(type=ConstraintType.REQUIRED)
        is_valid, error = constraint.validate('value', 'required_field')
        assert is_valid
        assert error is None
    
    def test_constraint_serialization(self):
        """Test constraint to_dict and from_dict."""
        constraint = Constraint(
            type=ConstraintType.RANGE,
            params={'min': 0, 'max': 100}
        )
        data = constraint.to_dict()
        restored = Constraint.from_dict(data)
        
        assert restored.type == constraint.type
        assert restored.params == constraint.params
    
    def test_unique_constraint(self):
        """Test unique constraint validation."""
        constraint = Constraint(type=ConstraintType.UNIQUE)
        # Unique constraint validation happens at dataset level, not individual value
        is_valid, error = constraint.validate('value', 'unique_field')
        assert is_valid
        assert error is None
    
    def test_foreign_key_constraint(self):
        """Test foreign key constraint validation."""
        constraint = Constraint(
            type=ConstraintType.FOREIGN_KEY,
            params={'target_table': 'users', 'target_field': 'id'}
        )
        # Foreign key validation happens at dataset level, not individual value
        is_valid, error = constraint.validate(1, 'user_id')
        assert is_valid
        assert error is None
    
    def test_constraint_with_empty_params(self):
        """Test constraint with empty params."""
        constraint = Constraint(type=ConstraintType.REQUIRED, params={})
        is_valid, error = constraint.validate('value', 'field')
        assert is_valid
        assert error is None
    
    def test_range_constraint_with_only_min(self):
        """Test range constraint with only minimum value."""
        constraint = Constraint(
            type=ConstraintType.RANGE,
            params={'min': 10}
        )
        assert constraint.validate(15, 'field')[0]
        assert not constraint.validate(5, 'field')[0]
    
    def test_range_constraint_with_only_max(self):
        """Test range constraint with only maximum value."""
        constraint = Constraint(
            type=ConstraintType.RANGE,
            params={'max': 100}
        )
        assert constraint.validate(50, 'field')[0]
        assert not constraint.validate(150, 'field')[0]
    
    def test_length_constraint_with_only_min(self):
        """Test length constraint with only minimum length."""
        constraint = Constraint(
            type=ConstraintType.LENGTH,
            params={'min': 3}
        )
        assert constraint.validate('hello', 'field')[0]
        assert not constraint.validate('ab', 'field')[0]
    
    def test_length_constraint_with_only_max(self):
        """Test length constraint with only maximum length."""
        constraint = Constraint(
            type=ConstraintType.LENGTH,
            params={'max': 10}
        )
        assert constraint.validate('hello', 'field')[0]
        assert not constraint.validate('verylongstring', 'field')[0]
    
    def test_pattern_constraint_with_special_characters(self):
        """Test pattern constraint with special regex characters."""
        constraint = Constraint(
            type=ConstraintType.PATTERN,
            params={'pattern': r'^\d{3}-\d{3}-\d{4}$'}
        )
        assert constraint.validate('123-456-7890', 'phone')[0]
        assert not constraint.validate('1234567890', 'phone')[0]
    
    def test_enum_constraint_with_empty_values(self):
        """Test enum constraint with empty allowed values."""
        constraint = Constraint(
            type=ConstraintType.ENUM,
            params={'values': []}
        )
        is_valid, error = constraint.validate('any', 'field')
        assert not is_valid
        assert 'not in allowed values' in error


@pytest.mark.unit
class TestFieldDefinition:
    """Test field definition."""
    
    def test_field_with_constraints(self):
        """Test field definition with constraints."""
        field = FieldDefinition(
            name='age',
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED),
                Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
            ],
            nullable=False
        )
        
        assert field.is_required()
        assert not field.is_unique()
    
    def test_field_validate_valid_value(self):
        """Test field validation with valid value."""
        field = FieldDefinition(
            name='age',
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
            ]
        )
        
        is_valid, errors = field.validate(25)
        assert is_valid
        assert len(errors) == 0
    
    def test_field_validate_invalid_value(self):
        """Test field validation with invalid value."""
        field = FieldDefinition(
            name='age',
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
            ]
        )
        
        is_valid, errors = field.validate(150)
        assert not is_valid
        assert len(errors) > 0
    
    def test_field_validate_null_non_nullable(self):
        """Test field validation with null value on non-nullable field."""
        field = FieldDefinition(
            name='age',
            data_type=DataType.INTEGER,
            nullable=False
        )
        
        is_valid, errors = field.validate(None)
        assert not is_valid
        assert any('cannot be null' in e for e in errors)
    
    def test_field_get_foreign_key(self):
        """Test getting foreign key relationship."""
        field = FieldDefinition(
            name='user_id',
            data_type=DataType.INTEGER,
            constraints=[
                Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    params={'target_table': 'users', 'target_field': 'id'}
                )
            ]
        )
        
        fk = field.get_foreign_key()
        assert fk is not None
        assert fk.source_field == 'user_id'
        assert fk.target_table == 'users'
        assert fk.target_field == 'id'
    
    def test_field_serialization(self):
        """Test field to_dict and from_dict."""
        field = FieldDefinition(
            name='email',
            data_type=DataType.EMAIL,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED),
                Constraint(
                    type=ConstraintType.PATTERN,
                    params={'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$'}
                )
            ],
            nullable=False,
            description='User email address'
        )
        
        data = field.to_dict()
        restored = FieldDefinition.from_dict(data)
        
        assert restored.name == field.name
        assert restored.data_type == field.data_type
        assert len(restored.constraints) == len(field.constraints)
        assert restored.nullable == field.nullable
        assert restored.description == field.description
    
    def test_field_validate_multiple_constraint_violations(self):
        """Test field validation with multiple constraint violations."""
        field = FieldDefinition(
            name='username',
            data_type=DataType.STRING,
            constraints=[
                Constraint(type=ConstraintType.REQUIRED),
                Constraint(type=ConstraintType.LENGTH, params={'min': 5, 'max': 20}),
                Constraint(type=ConstraintType.PATTERN, params={'pattern': r'^[a-zA-Z0-9_]+$'})
            ],
            nullable=False
        )
        
        # Value violates both length and pattern constraints
        is_valid, errors = field.validate('ab!')
        assert not is_valid
        assert len(errors) >= 2
        assert any('below minimum' in e for e in errors)
        assert any('does not match pattern' in e for e in errors)
    
    def test_field_with_default_value(self):
        """Test field with default value."""
        field = FieldDefinition(
            name='status',
            data_type=DataType.STRING,
            default_value='active',
            nullable=True
        )
        
        assert field.default_value == 'active'
        assert field.nullable
    
    def test_field_nullable_with_none_value(self):
        """Test nullable field with None value."""
        field = FieldDefinition(
            name='optional_field',
            data_type=DataType.STRING,
            nullable=True
        )
        
        is_valid, errors = field.validate(None)
        assert is_valid
        assert len(errors) == 0


@pytest.mark.unit
class TestTableSchema:
    """Test table schema."""
    
    def test_table_with_fields(self):
        """Test table schema with multiple fields."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)],
                    nullable=False
                ),
                FieldDefinition(
                    name='email',
                    data_type=DataType.EMAIL,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)],
                    nullable=False
                ),
                FieldDefinition(
                    name='age',
                    data_type=DataType.INTEGER,
                    constraints=[
                        Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                    ]
                )
            ],
            primary_key='id'
        )
        
        assert table.get_field('id') is not None
        assert table.get_field('nonexistent') is None
        assert 'id' in table.get_required_fields()
        assert 'email' in table.get_required_fields()
        assert 'age' not in table.get_required_fields()
    
    def test_table_validate_record_valid(self):
        """Test table record validation with valid record."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)]
                ),
                FieldDefinition(
                    name='age',
                    data_type=DataType.INTEGER,
                    constraints=[
                        Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                    ]
                )
            ]
        )
        
        record = {'id': 1, 'age': 25}
        is_valid, errors = table.validate_record(record)
        assert is_valid
        assert len(errors) == 0
    
    def test_table_validate_record_missing_required(self):
        """Test table record validation with missing required field."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)]
                )
            ]
        )
        
        record = {'age': 25}
        is_valid, errors = table.validate_record(record)
        assert not is_valid
        assert any('required' in e.lower() for e in errors)
    
    def test_table_validate_record_constraint_violation(self):
        """Test table record validation with constraint violation."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='age',
                    data_type=DataType.INTEGER,
                    constraints=[
                        Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                    ]
                )
            ]
        )
        
        record = {'age': 150}
        is_valid, errors = table.validate_record(record)
        assert not is_valid
        assert len(errors) > 0
    
    def test_table_validate_record_unknown_field(self):
        """Test table record validation with unknown field."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(name='id', data_type=DataType.INTEGER)
            ]
        )
        
        record = {'id': 1, 'unknown_field': 'value'}
        is_valid, errors = table.validate_record(record)
        assert not is_valid
        assert any('unknown' in e.lower() for e in errors)
    
    def test_table_get_foreign_keys(self):
        """Test getting foreign key relationships from table."""
        table = TableSchema(
            name='orders',
            fields=[
                FieldDefinition(name='id', data_type=DataType.INTEGER),
                FieldDefinition(
                    name='user_id',
                    data_type=DataType.INTEGER,
                    constraints=[
                        Constraint(
                            type=ConstraintType.FOREIGN_KEY,
                            params={'target_table': 'users', 'target_field': 'id'}
                        )
                    ]
                )
            ]
        )
        
        fks = table.get_foreign_keys()
        assert len(fks) == 1
        assert fks[0].source_field == 'user_id'
        assert fks[0].target_table == 'users'
    
    def test_table_serialization(self):
        """Test table to_dict and from_dict."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)]
                )
            ],
            primary_key='id',
            description='User table'
        )
        
        data = table.to_dict()
        restored = TableSchema.from_dict(data)
        
        assert restored.name == table.name
        assert len(restored.fields) == len(table.fields)
        assert restored.primary_key == table.primary_key
        assert restored.description == table.description
    
    def test_table_validate_record_with_null_nullable_field(self):
        """Test table record validation with null value in nullable field."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)]
                ),
                FieldDefinition(
                    name='optional_field',
                    data_type=DataType.STRING,
                    nullable=True
                )
            ]
        )
        
        record = {'id': 1, 'optional_field': None}
        is_valid, errors = table.validate_record(record)
        assert is_valid
        assert len(errors) == 0
    
    def test_table_validate_record_multiple_errors(self):
        """Test table record validation with multiple errors."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)]
                ),
                FieldDefinition(
                    name='age',
                    data_type=DataType.INTEGER,
                    constraints=[
                        Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                    ]
                ),
                FieldDefinition(
                    name='email',
                    data_type=DataType.EMAIL,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)]
                )
            ]
        )
        
        # Missing required fields and invalid age
        record = {'age': 150, 'unknown': 'value'}
        is_valid, errors = table.validate_record(record)
        assert not is_valid
        assert len(errors) >= 3  # Missing id, missing email, invalid age, unknown field
    
    def test_table_get_unique_fields(self):
        """Test getting unique fields from table."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.UNIQUE)]
                ),
                FieldDefinition(
                    name='email',
                    data_type=DataType.EMAIL,
                    constraints=[Constraint(type=ConstraintType.UNIQUE)]
                ),
                FieldDefinition(
                    name='name',
                    data_type=DataType.STRING
                )
            ]
        )
        
        unique_fields = table.get_unique_fields()
        assert 'id' in unique_fields
        assert 'email' in unique_fields
        assert 'name' not in unique_fields
    
    def test_table_with_no_primary_key(self):
        """Test table without primary key."""
        table = TableSchema(
            name='logs',
            fields=[
                FieldDefinition(name='timestamp', data_type=DataType.DATETIME),
                FieldDefinition(name='message', data_type=DataType.STRING)
            ]
        )
        
        assert table.primary_key is None
    
    def test_table_validate_empty_record(self):
        """Test table validation with empty record."""
        table = TableSchema(
            name='users',
            fields=[
                FieldDefinition(
                    name='id',
                    data_type=DataType.INTEGER,
                    constraints=[Constraint(type=ConstraintType.REQUIRED)]
                )
            ]
        )
        
        record = {}
        is_valid, errors = table.validate_record(record)
        assert not is_valid
        assert any('required' in e.lower() for e in errors)


@pytest.mark.unit
class TestDataSchema:
    """Test data schema."""
    
    def test_schema_with_multiple_tables(self):
        """Test schema with multiple tables."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(name='id', data_type=DataType.INTEGER)
                    ]
                ),
                TableSchema(
                    name='orders',
                    fields=[
                        FieldDefinition(name='id', data_type=DataType.INTEGER)
                    ]
                )
            ]
        )
        
        assert schema.get_table('users') is not None
        assert schema.get_table('orders') is not None
        assert schema.get_table('nonexistent') is None
    
    def test_schema_from_json_file(self, tmp_path):
        """Test loading schema from JSON file."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(
                            name='id',
                            data_type=DataType.INTEGER,
                            constraints=[Constraint(type=ConstraintType.REQUIRED)]
                        )
                    ],
                    primary_key='id'
                )
            ],
            version='1.0',
            description='Test schema'
        )
        
        # Save to file
        file_path = tmp_path / "test_schema.json"
        schema.to_json_file(file_path)
        
        # Load from file
        loaded_schema = DataSchema.from_json_file(file_path)
        
        assert len(loaded_schema.tables) == 1
        assert loaded_schema.tables[0].name == 'users'
        assert loaded_schema.version == '1.0'
        assert loaded_schema.description == 'Test schema'
    
    def test_schema_parse_invalid_json(self):
        """Test parsing invalid JSON raises appropriate error."""
        invalid_json = "{ invalid json }"
        
        with pytest.raises(json.JSONDecodeError):
            DataSchema.from_json(invalid_json)
    
    def test_schema_parse_missing_required_fields(self):
        """Test parsing JSON with missing required fields."""
        # Missing 'tables' field
        invalid_schema = json.dumps({'version': '1.0'})
        
        with pytest.raises(KeyError):
            DataSchema.from_json(invalid_schema)
    
    def test_schema_topological_sort_no_dependencies(self):
        """Test topological sort with no dependencies."""
        schema = DataSchema(
            tables=[
                TableSchema(name='table_a', fields=[]),
                TableSchema(name='table_b', fields=[]),
                TableSchema(name='table_c', fields=[])
            ]
        )
        
        sorted_tables = schema.topological_sort()
        assert len(sorted_tables) == 3
        assert set(sorted_tables) == {'table_a', 'table_b', 'table_c'}
    
    def test_schema_topological_sort_with_dependencies(self):
        """Test topological sort with foreign key dependencies."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='orders',
                    fields=[
                        FieldDefinition(
                            name='user_id',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(
                                    type=ConstraintType.FOREIGN_KEY,
                                    params={'target_table': 'users', 'target_field': 'id'}
                                )
                            ]
                        )
                    ]
                ),
                TableSchema(
                    name='users',
                    fields=[FieldDefinition(name='id', data_type=DataType.INTEGER)]
                )
            ]
        )
        
        sorted_tables = schema.topological_sort()
        # users should come before orders
        assert sorted_tables.index('users') < sorted_tables.index('orders')
    
    def test_schema_topological_sort_circular_dependency(self):
        """Test topological sort with circular dependencies."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='table_a',
                    fields=[
                        FieldDefinition(
                            name='b_id',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(
                                    type=ConstraintType.FOREIGN_KEY,
                                    params={'target_table': 'table_b', 'target_field': 'id'}
                                )
                            ]
                        )
                    ]
                ),
                TableSchema(
                    name='table_b',
                    fields=[
                        FieldDefinition(
                            name='a_id',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(
                                    type=ConstraintType.FOREIGN_KEY,
                                    params={'target_table': 'table_a', 'target_field': 'id'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        
        with pytest.raises(ValueError, match='Circular'):
            schema.topological_sort()
    
    def test_schema_validate_referential_integrity_valid(self):
        """Test referential integrity validation with valid data."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[FieldDefinition(name='id', data_type=DataType.INTEGER)]
                ),
                TableSchema(
                    name='orders',
                    fields=[
                        FieldDefinition(
                            name='user_id',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(
                                    type=ConstraintType.FOREIGN_KEY,
                                    params={'target_table': 'users', 'target_field': 'id'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        
        data = {
            'users': [{'id': 1}, {'id': 2}],
            'orders': [{'user_id': 1}, {'user_id': 2}]
        }
        
        is_valid, errors = schema.validate_referential_integrity(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_schema_validate_referential_integrity_invalid(self):
        """Test referential integrity validation with invalid foreign key."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[FieldDefinition(name='id', data_type=DataType.INTEGER)]
                ),
                TableSchema(
                    name='orders',
                    fields=[
                        FieldDefinition(
                            name='user_id',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(
                                    type=ConstraintType.FOREIGN_KEY,
                                    params={'target_table': 'users', 'target_field': 'id'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        
        data = {
            'users': [{'id': 1}],
            'orders': [{'user_id': 999}]  # Invalid foreign key
        }
        
        is_valid, errors = schema.validate_referential_integrity(data)
        assert not is_valid
        assert len(errors) > 0
        assert any('not found' in e for e in errors)
    
    def test_schema_validate_dataset(self):
        """Test complete dataset validation."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(
                            name='id',
                            data_type=DataType.INTEGER,
                            constraints=[Constraint(type=ConstraintType.REQUIRED)]
                        ),
                        FieldDefinition(
                            name='age',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                            ]
                        )
                    ]
                )
            ]
        )
        
        # Valid data
        data = {
            'users': [
                {'id': 1, 'age': 25},
                {'id': 2, 'age': 30}
            ]
        }
        is_valid, errors = schema.validate_dataset(data)
        assert is_valid
        
        # Invalid data
        data = {
            'users': [
                {'id': 1, 'age': 150}  # Age exceeds maximum
            ]
        }
        is_valid, errors = schema.validate_dataset(data)
        assert not is_valid
    
    def test_schema_serialization(self):
        """Test schema to_dict/from_dict and JSON serialization."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(name='id', data_type=DataType.INTEGER)
                    ]
                )
            ],
            version='1.0',
            description='Test schema'
        )
        
        # Test dict serialization
        data = schema.to_dict()
        restored = DataSchema.from_dict(data)
        assert len(restored.tables) == len(schema.tables)
        assert restored.version == schema.version
        
        # Test JSON serialization
        json_str = schema.to_json()
        restored_from_json = DataSchema.from_json(json_str)
        assert len(restored_from_json.tables) == len(schema.tables)


@pytest.mark.unit
class TestSchemaValidator:
    """Test schema validator."""
    
    def test_validator_validate_schema_structure_valid(self):
        """Test schema structure validation with valid schema."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(name='id', data_type=DataType.INTEGER)
                    ],
                    primary_key='id'
                )
            ]
        )
        
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_schema_structure()
        assert is_valid
        assert len(errors) == 0
    
    def test_validator_validate_schema_empty_tables(self):
        """Test schema structure validation with empty tables list."""
        schema = DataSchema(tables=[])
        
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_schema_structure()
        assert is_valid
        assert len(errors) == 0
    
    def test_validator_validate_schema_duplicate_tables(self):
        """Test schema structure validation with duplicate table names."""
        schema = DataSchema(
            tables=[
                TableSchema(name='users', fields=[]),
                TableSchema(name='users', fields=[])
            ]
        )
        
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_schema_structure()
        assert not is_valid
        assert any('duplicate' in e.lower() for e in errors)
    
    def test_validator_validate_schema_duplicate_fields(self):
        """Test schema structure validation with duplicate field names."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(name='id', data_type=DataType.INTEGER),
                        FieldDefinition(name='id', data_type=DataType.STRING)
                    ]
                )
            ]
        )
        
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_schema_structure()
        assert not is_valid
        assert any('duplicate' in e.lower() for e in errors)
    
    def test_validator_validate_schema_invalid_primary_key(self):
        """Test schema structure validation with invalid primary key."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(name='id', data_type=DataType.INTEGER)
                    ],
                    primary_key='nonexistent'
                )
            ]
        )
        
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_schema_structure()
        assert not is_valid
        assert any('primary key' in e.lower() for e in errors)
    
    def test_validator_validate_schema_invalid_foreign_key_table(self):
        """Test schema structure validation with invalid foreign key table."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='orders',
                    fields=[
                        FieldDefinition(
                            name='user_id',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(
                                    type=ConstraintType.FOREIGN_KEY,
                                    params={'target_table': 'nonexistent', 'target_field': 'id'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_schema_structure()
        assert not is_valid
        assert any('non-existent table' in e for e in errors)
    
    def test_validator_validate_schema_invalid_foreign_key_field(self):
        """Test schema structure validation with invalid foreign key field."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[FieldDefinition(name='id', data_type=DataType.INTEGER)]
                ),
                TableSchema(
                    name='orders',
                    fields=[
                        FieldDefinition(
                            name='user_id',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(
                                    type=ConstraintType.FOREIGN_KEY,
                                    params={'target_table': 'users', 'target_field': 'nonexistent'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_schema_structure()
        assert not is_valid
        assert any('non-existent field' in e for e in errors)
    
    def test_validator_enforce_constraints_on_generation(self):
        """Test constraint enforcement on generated values."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(
                            name='age',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                            ]
                        )
                    ]
                )
            ]
        )
        
        validator = SchemaValidator(schema)
        
        # Valid value
        is_valid, value, error = validator.enforce_constraints_on_generation('users', 'age', 25)
        assert is_valid
        assert error is None
        
        # Invalid value
        is_valid, value, error = validator.enforce_constraints_on_generation('users', 'age', 150)
        assert not is_valid
        assert error is not None
    
    def test_validator_enforce_constraints_nonexistent_table(self):
        """Test constraint enforcement with nonexistent table."""
        schema = DataSchema(tables=[])
        validator = SchemaValidator(schema)
        
        is_valid, value, error = validator.enforce_constraints_on_generation('nonexistent', 'field', 'value')
        assert not is_valid
        assert 'not found in schema' in error
    
    def test_validator_enforce_constraints_nonexistent_field(self):
        """Test constraint enforcement with nonexistent field."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(name='id', data_type=DataType.INTEGER)
                    ]
                )
            ]
        )
        validator = SchemaValidator(schema)
        
        is_valid, value, error = validator.enforce_constraints_on_generation('users', 'nonexistent', 'value')
        assert not is_valid
        assert 'not found in table' in error
    
    def test_validator_validate_data_with_valid_dataset(self):
        """Test data validation with valid dataset."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(
                            name='id',
                            data_type=DataType.INTEGER,
                            constraints=[Constraint(type=ConstraintType.REQUIRED)]
                        ),
                        FieldDefinition(
                            name='email',
                            data_type=DataType.EMAIL,
                            constraints=[Constraint(type=ConstraintType.REQUIRED)]
                        )
                    ]
                )
            ]
        )
        validator = SchemaValidator(schema)
        
        data = {
            'users': [
                {'id': 1, 'email': 'user1@example.com'},
                {'id': 2, 'email': 'user2@example.com'}
            ]
        }
        
        is_valid, errors = validator.validate_data(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_validator_validate_data_with_invalid_dataset(self):
        """Test data validation with invalid dataset."""
        schema = DataSchema(
            tables=[
                TableSchema(
                    name='users',
                    fields=[
                        FieldDefinition(
                            name='id',
                            data_type=DataType.INTEGER,
                            constraints=[Constraint(type=ConstraintType.REQUIRED)]
                        ),
                        FieldDefinition(
                            name='age',
                            data_type=DataType.INTEGER,
                            constraints=[
                                Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                            ]
                        )
                    ]
                )
            ]
        )
        validator = SchemaValidator(schema)
        
        data = {
            'users': [
                {'age': 150}  # Missing required id, age exceeds max
            ]
        }
        
        is_valid, errors = validator.validate_data(data)
        assert not is_valid
        assert len(errors) > 0
        assert any('required' in e.lower() for e in errors)
        assert any('exceeds maximum' in e for e in errors)
