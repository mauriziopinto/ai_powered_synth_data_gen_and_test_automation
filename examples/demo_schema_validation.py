"""Demo script for schema validation and constraint enforcement."""

from shared.models.schema import (
    DataType,
    ConstraintType,
    Constraint,
    FieldDefinition,
    TableSchema,
    DataSchema,
    SchemaValidator
)


def demo_basic_schema():
    """Demonstrate basic schema definition and validation."""
    print("=" * 80)
    print("DEMO: Basic Schema Definition and Validation")
    print("=" * 80)
    
    # Define a simple user table schema
    user_table = TableSchema(
        name='users',
        fields=[
            FieldDefinition(
                name='id',
                data_type=DataType.INTEGER,
                constraints=[Constraint(type=ConstraintType.REQUIRED)],
                nullable=False,
                description='User ID'
            ),
            FieldDefinition(
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
            ),
            FieldDefinition(
                name='age',
                data_type=DataType.INTEGER,
                constraints=[
                    Constraint(type=ConstraintType.RANGE, params={'min': 0, 'max': 120})
                ],
                description='User age'
            ),
            FieldDefinition(
                name='status',
                data_type=DataType.STRING,
                constraints=[
                    Constraint(
                        type=ConstraintType.ENUM,
                        params={'values': ['active', 'inactive', 'suspended']}
                    )
                ],
                description='User account status'
            )
        ],
        primary_key='id',
        description='User accounts table'
    )
    
    # Create schema
    schema = DataSchema(
        tables=[user_table],
        version='1.0',
        description='Demo schema for user management'
    )
    
    # Validate schema structure
    validator = SchemaValidator(schema)
    is_valid, errors = validator.validate_schema_structure()
    print(f"\nSchema structure valid: {is_valid}")
    if errors:
        print("Errors:", errors)
    
    # Test valid record
    print("\n" + "-" * 80)
    print("Testing VALID record:")
    valid_record = {
        'id': 1,
        'email': 'user@example.com',
        'age': 25,
        'status': 'active'
    }
    print(f"Record: {valid_record}")
    is_valid, errors = user_table.validate_record(valid_record)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:", errors)
    
    # Test invalid record - missing required field
    print("\n" + "-" * 80)
    print("Testing INVALID record (missing required field):")
    invalid_record1 = {
        'age': 25,
        'status': 'active'
    }
    print(f"Record: {invalid_record1}")
    is_valid, errors = user_table.validate_record(invalid_record1)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Test invalid record - constraint violation
    print("\n" + "-" * 80)
    print("Testing INVALID record (age exceeds maximum):")
    invalid_record2 = {
        'id': 2,
        'email': 'user2@example.com',
        'age': 150,
        'status': 'active'
    }
    print(f"Record: {invalid_record2}")
    is_valid, errors = user_table.validate_record(invalid_record2)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Test invalid record - invalid enum value
    print("\n" + "-" * 80)
    print("Testing INVALID record (invalid status value):")
    invalid_record3 = {
        'id': 3,
        'email': 'user3@example.com',
        'age': 30,
        'status': 'deleted'  # Not in allowed values
    }
    print(f"Record: {invalid_record3}")
    is_valid, errors = user_table.validate_record(invalid_record3)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")


def demo_foreign_keys():
    """Demonstrate foreign key relationships and referential integrity."""
    print("\n\n" + "=" * 80)
    print("DEMO: Foreign Key Relationships and Referential Integrity")
    print("=" * 80)
    
    # Define users table
    users_table = TableSchema(
        name='users',
        fields=[
            FieldDefinition(
                name='id',
                data_type=DataType.INTEGER,
                constraints=[Constraint(type=ConstraintType.REQUIRED)],
                nullable=False
            ),
            FieldDefinition(
                name='name',
                data_type=DataType.STRING,
                constraints=[Constraint(type=ConstraintType.REQUIRED)]
            )
        ],
        primary_key='id'
    )
    
    # Define orders table with foreign key to users
    orders_table = TableSchema(
        name='orders',
        fields=[
            FieldDefinition(
                name='id',
                data_type=DataType.INTEGER,
                constraints=[Constraint(type=ConstraintType.REQUIRED)],
                nullable=False
            ),
            FieldDefinition(
                name='user_id',
                data_type=DataType.INTEGER,
                constraints=[
                    Constraint(type=ConstraintType.REQUIRED),
                    Constraint(
                        type=ConstraintType.FOREIGN_KEY,
                        params={'target_table': 'users', 'target_field': 'id'}
                    )
                ],
                nullable=False
            ),
            FieldDefinition(
                name='amount',
                data_type=DataType.FLOAT,
                constraints=[
                    Constraint(type=ConstraintType.RANGE, params={'min': 0})
                ]
            )
        ],
        primary_key='id'
    )
    
    # Create schema
    schema = DataSchema(
        tables=[users_table, orders_table],
        version='1.0',
        description='Demo schema with foreign keys'
    )
    
    # Get topological sort
    print("\nTopological sort (dependency order):")
    sorted_tables = schema.topological_sort()
    print(f"  {' -> '.join(sorted_tables)}")
    print("  (Tables should be loaded in this order to respect foreign keys)")
    
    # Test valid referential integrity
    print("\n" + "-" * 80)
    print("Testing VALID referential integrity:")
    valid_data = {
        'users': [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ],
        'orders': [
            {'id': 101, 'user_id': 1, 'amount': 99.99},
            {'id': 102, 'user_id': 2, 'amount': 149.99}
        ]
    }
    print("Data:")
    for table_name, records in valid_data.items():
        print(f"  {table_name}: {records}")
    
    is_valid, errors = schema.validate_referential_integrity(valid_data)
    print(f"\nReferential integrity valid: {is_valid}")
    if errors:
        print("Errors:", errors)
    
    # Test invalid referential integrity
    print("\n" + "-" * 80)
    print("Testing INVALID referential integrity (foreign key not found):")
    invalid_data = {
        'users': [
            {'id': 1, 'name': 'Alice'}
        ],
        'orders': [
            {'id': 101, 'user_id': 1, 'amount': 99.99},
            {'id': 102, 'user_id': 999, 'amount': 149.99}  # Invalid foreign key
        ]
    }
    print("Data:")
    for table_name, records in invalid_data.items():
        print(f"  {table_name}: {records}")
    
    is_valid, errors = schema.validate_referential_integrity(invalid_data)
    print(f"\nReferential integrity valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")


def demo_constraint_enforcement():
    """Demonstrate constraint enforcement during generation."""
    print("\n\n" + "=" * 80)
    print("DEMO: Constraint Enforcement During Generation")
    print("=" * 80)
    
    # Define a product table with various constraints
    product_table = TableSchema(
        name='products',
        fields=[
            FieldDefinition(
                name='sku',
                data_type=DataType.STRING,
                constraints=[
                    Constraint(type=ConstraintType.REQUIRED),
                    Constraint(
                        type=ConstraintType.PATTERN,
                        params={'pattern': r'^[A-Z]{3}-\d{4}$'}
                    )
                ],
                description='Product SKU (format: ABC-1234)'
            ),
            FieldDefinition(
                name='price',
                data_type=DataType.FLOAT,
                constraints=[
                    Constraint(type=ConstraintType.RANGE, params={'min': 0.01, 'max': 9999.99})
                ],
                description='Product price'
            ),
            FieldDefinition(
                name='category',
                data_type=DataType.STRING,
                constraints=[
                    Constraint(
                        type=ConstraintType.ENUM,
                        params={'values': ['electronics', 'clothing', 'food', 'books']}
                    )
                ]
            )
        ]
    )
    
    schema = DataSchema(tables=[product_table])
    validator = SchemaValidator(schema)
    
    # Test constraint enforcement on generated values
    test_cases = [
        ('sku', 'ABC-1234', True, 'Valid SKU format'),
        ('sku', 'invalid', False, 'Invalid SKU format'),
        ('price', 99.99, True, 'Valid price'),
        ('price', -10.00, False, 'Negative price'),
        ('price', 10000.00, False, 'Price exceeds maximum'),
        ('category', 'electronics', True, 'Valid category'),
        ('category', 'furniture', False, 'Invalid category'),
    ]
    
    print("\nTesting constraint enforcement on generated values:")
    print("-" * 80)
    
    for field_name, value, expected_valid, description in test_cases:
        is_valid, corrected_value, error = validator.enforce_constraints_on_generation(
            'products', field_name, value
        )
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"\n{status} {description}")
        print(f"  Field: {field_name}")
        print(f"  Value: {value}")
        print(f"  Valid: {is_valid}")
        if error:
            print(f"  Error: {error}")


def demo_serialization():
    """Demonstrate schema serialization to/from JSON."""
    print("\n\n" + "=" * 80)
    print("DEMO: Schema Serialization")
    print("=" * 80)
    
    # Create a simple schema
    schema = DataSchema(
        tables=[
            TableSchema(
                name='customers',
                fields=[
                    FieldDefinition(
                        name='id',
                        data_type=DataType.INTEGER,
                        constraints=[Constraint(type=ConstraintType.REQUIRED)]
                    ),
                    FieldDefinition(
                        name='email',
                        data_type=DataType.EMAIL,
                        constraints=[
                            Constraint(
                                type=ConstraintType.PATTERN,
                                params={'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$'}
                            )
                        ]
                    )
                ],
                primary_key='id'
            )
        ],
        version='1.0',
        description='Customer schema'
    )
    
    # Serialize to JSON
    json_str = schema.to_json()
    print("\nSerialized schema to JSON:")
    print(json_str)
    
    # Deserialize from JSON
    restored_schema = DataSchema.from_json(json_str)
    print("\nDeserialized schema:")
    print(f"  Version: {restored_schema.version}")
    print(f"  Description: {restored_schema.description}")
    print(f"  Tables: {[t.name for t in restored_schema.tables]}")
    print(f"  Fields in 'customers': {[f.name for f in restored_schema.tables[0].fields]}")


if __name__ == '__main__':
    demo_basic_schema()
    demo_foreign_keys()
    demo_constraint_enforcement()
    demo_serialization()
    
    print("\n\n" + "=" * 80)
    print("All demos completed successfully!")
    print("=" * 80)
