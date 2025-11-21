"""Schema definition and validation models."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
import re
import json
from pathlib import Path


class DataType(Enum):
    """Supported data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    UUID = "uuid"


class ConstraintType(Enum):
    """Types of constraints."""
    RANGE = "range"
    PATTERN = "pattern"
    ENUM = "enum"
    LENGTH = "length"
    REQUIRED = "required"
    UNIQUE = "unique"
    FOREIGN_KEY = "foreign_key"


@dataclass
class Constraint:
    """A constraint on a field."""
    type: ConstraintType
    params: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, value: Any, field_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a value against this constraint.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            if self.type == ConstraintType.REQUIRED:
                return False, f"Field '{field_name}' is required but got None"
            return True, None
        
        if self.type == ConstraintType.RANGE:
            min_val = self.params.get('min')
            max_val = self.params.get('max')
            
            if min_val is not None and value < min_val:
                return False, f"Field '{field_name}' value {value} is below minimum {min_val}"
            if max_val is not None and value > max_val:
                return False, f"Field '{field_name}' value {value} exceeds maximum {max_val}"
            return True, None
        
        elif self.type == ConstraintType.PATTERN:
            pattern = self.params.get('pattern')
            if pattern and not re.match(pattern, str(value)):
                return False, f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
            return True, None
        
        elif self.type == ConstraintType.ENUM:
            allowed_values = self.params.get('values', [])
            if value not in allowed_values:
                return False, f"Field '{field_name}' value '{value}' not in allowed values {allowed_values}"
            return True, None
        
        elif self.type == ConstraintType.LENGTH:
            min_len = self.params.get('min')
            max_len = self.params.get('max')
            length = len(str(value))
            
            if min_len is not None and length < min_len:
                return False, f"Field '{field_name}' length {length} is below minimum {min_len}"
            if max_len is not None and length > max_len:
                return False, f"Field '{field_name}' length {length} exceeds maximum {max_len}"
            return True, None
        
        elif self.type == ConstraintType.REQUIRED:
            # Already handled None case above
            return True, None
        
        elif self.type == ConstraintType.UNIQUE:
            # Uniqueness is validated at dataset level, not individual value
            return True, None
        
        elif self.type == ConstraintType.FOREIGN_KEY:
            # Foreign key validation requires context of other tables
            return True, None
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': self.type.value,
            'params': self.params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Constraint':
        """Create from dictionary."""
        return cls(
            type=ConstraintType(data['type']),
            params=data.get('params', {})
        )


@dataclass
class ForeignKeyRelationship:
    """Foreign key relationship between fields."""
    source_field: str
    target_table: str
    target_field: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForeignKeyRelationship':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FieldDefinition:
    """Definition of a single field in the schema."""
    name: str
    data_type: DataType
    constraints: List[Constraint] = field(default_factory=list)
    nullable: bool = True
    default_value: Optional[Any] = None
    description: Optional[str] = None
    
    def is_required(self) -> bool:
        """Check if field is required."""
        return any(c.type == ConstraintType.REQUIRED for c in self.constraints)
    
    def is_unique(self) -> bool:
        """Check if field must be unique."""
        return any(c.type == ConstraintType.UNIQUE for c in self.constraints)
    
    def get_foreign_key(self) -> Optional[ForeignKeyRelationship]:
        """Get foreign key relationship if exists."""
        for constraint in self.constraints:
            if constraint.type == ConstraintType.FOREIGN_KEY:
                return ForeignKeyRelationship(
                    source_field=self.name,
                    target_table=constraint.params.get('target_table'),
                    target_field=constraint.params.get('target_field')
                )
        return None
    
    def validate(self, value: Any) -> Tuple[bool, List[str]]:
        """
        Validate a value against all field constraints.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check nullable
        if value is None:
            if not self.nullable and not self.is_required():
                errors.append(f"Field '{self.name}' cannot be null")
            # If nullable or has required constraint, let constraint validation handle it
        
        # Validate against each constraint
        for constraint in self.constraints:
            is_valid, error = constraint.validate(value, self.name)
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'data_type': self.data_type.value,
            'constraints': [c.to_dict() for c in self.constraints],
            'nullable': self.nullable,
            'default_value': self.default_value,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldDefinition':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            data_type=DataType(data['data_type']),
            constraints=[Constraint.from_dict(c) for c in data.get('constraints', [])],
            nullable=data.get('nullable', True),
            default_value=data.get('default_value'),
            description=data.get('description')
        )


@dataclass
class TableSchema:
    """Schema definition for a table."""
    name: str
    fields: List[FieldDefinition]
    primary_key: Optional[str] = None
    description: Optional[str] = None
    
    def get_field(self, field_name: str) -> Optional[FieldDefinition]:
        """Get field definition by name."""
        for field_def in self.fields:
            if field_def.name == field_name:
                return field_def
        return None
    
    def get_required_fields(self) -> List[str]:
        """Get list of required field names."""
        return [f.name for f in self.fields if f.is_required()]
    
    def get_unique_fields(self) -> List[str]:
        """Get list of unique field names."""
        return [f.name for f in self.fields if f.is_unique()]
    
    def get_foreign_keys(self) -> List[ForeignKeyRelationship]:
        """Get all foreign key relationships."""
        fks = []
        for field_def in self.fields:
            fk = field_def.get_foreign_key()
            if fk:
                fks.append(fk)
        return fks
    
    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a record against the schema.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for required fields
        for field_name in self.get_required_fields():
            if field_name not in record or record[field_name] is None:
                errors.append(f"Required field '{field_name}' is missing or null")
        
        # Validate each field in the record
        for field_name, value in record.items():
            field_def = self.get_field(field_name)
            if field_def is None:
                errors.append(f"Unknown field '{field_name}' not in schema")
                continue
            
            is_valid, field_errors = field_def.validate(value)
            if not is_valid:
                errors.extend(field_errors)
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'fields': [f.to_dict() for f in self.fields],
            'primary_key': self.primary_key,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableSchema':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            fields=[FieldDefinition.from_dict(f) for f in data['fields']],
            primary_key=data.get('primary_key'),
            description=data.get('description')
        )


@dataclass
class DataSchema:
    """Complete data schema with multiple tables."""
    tables: List[TableSchema]
    version: str = "1.0"
    description: Optional[str] = None
    
    def get_table(self, table_name: str) -> Optional[TableSchema]:
        """Get table schema by name."""
        for table in self.tables:
            if table.name == table_name:
                return table
        return None
    
    def get_foreign_key_dependencies(self) -> Dict[str, Set[str]]:
        """
        Get foreign key dependencies between tables.
        
        Returns:
            Dictionary mapping table names to set of tables they depend on
        """
        dependencies = {table.name: set() for table in self.tables}
        
        for table in self.tables:
            for fk in table.get_foreign_keys():
                dependencies[table.name].add(fk.target_table)
        
        return dependencies
    
    def topological_sort(self) -> List[str]:
        """
        Sort tables in topological order based on foreign key dependencies.
        Tables with no dependencies come first.
        
        Returns:
            List of table names in dependency order
            
        Raises:
            ValueError: If circular dependencies detected
        """
        dependencies = self.get_foreign_key_dependencies()
        
        # Kahn's algorithm for topological sort
        # in_degree represents how many tables depend on this table
        in_degree = {table: 0 for table in dependencies}
        
        # Count incoming edges (tables that reference this table)
        for table, deps in dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Start with tables that have no incoming edges (no one depends on them)
        queue = [table for table, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            table = queue.pop(0)
            result.append(table)
            
            # For each table that this table depends on, decrement its in-degree
            for dep in dependencies[table]:
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        
        if len(result) != len(dependencies):
            # Circular dependency detected
            remaining = set(dependencies.keys()) - set(result)
            raise ValueError(f"Circular foreign key dependencies detected in tables: {remaining}")
        
        # Reverse to get correct order: tables with no dependencies first
        return list(reversed(result))
    
    def validate_referential_integrity(
        self, 
        data: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[bool, List[str]]:
        """
        Validate referential integrity across all tables.
        
        Args:
            data: Dictionary mapping table names to lists of records
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        for table in self.tables:
            table_data = data.get(table.name, [])
            
            for fk in table.get_foreign_keys():
                target_table_data = data.get(fk.target_table, [])
                
                # Build set of valid target values
                valid_targets = {
                    record.get(fk.target_field)
                    for record in target_table_data
                    if record.get(fk.target_field) is not None
                }
                
                # Check each record's foreign key value
                for i, record in enumerate(table_data):
                    fk_value = record.get(fk.source_field)
                    if fk_value is not None and fk_value not in valid_targets:
                        errors.append(
                            f"Table '{table.name}' record {i}: "
                            f"Foreign key '{fk.source_field}' value '{fk_value}' "
                            f"not found in '{fk.target_table}.{fk.target_field}'"
                        )
        
        return len(errors) == 0, errors
    
    def validate_dataset(
        self, 
        data: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[bool, List[str]]:
        """
        Validate entire dataset against schema.
        
        Args:
            data: Dictionary mapping table names to lists of records
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        all_errors = []
        
        # Validate each table's records
        for table in self.tables:
            table_data = data.get(table.name, [])
            
            for i, record in enumerate(table_data):
                is_valid, errors = table.validate_record(record)
                if not is_valid:
                    for error in errors:
                        all_errors.append(f"Table '{table.name}' record {i}: {error}")
        
        # Validate referential integrity
        is_valid, ref_errors = self.validate_referential_integrity(data)
        all_errors.extend(ref_errors)
        
        return len(all_errors) == 0, all_errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tables': [t.to_dict() for t in self.tables],
            'version': self.version,
            'description': self.description
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSchema':
        """Create from dictionary."""
        return cls(
            tables=[TableSchema.from_dict(t) for t in data['tables']],
            version=data.get('version', '1.0'),
            description=data.get('description')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DataSchema':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_json_file(cls, file_path: Path) -> 'DataSchema':
        """Load schema from JSON file."""
        with open(file_path, 'r') as f:
            return cls.from_json(f.read())
    
    def to_json_file(self, file_path: Path) -> None:
        """Save schema to JSON file."""
        with open(file_path, 'w') as f:
            f.write(self.to_json())


class SchemaValidator:
    """Validator for schema definitions and data."""
    
    def __init__(self, schema: DataSchema):
        """Initialize validator with schema."""
        self.schema = schema
    
    def validate_schema_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate the schema structure itself.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for duplicate table names
        table_names = [t.name for t in self.schema.tables]
        if len(table_names) != len(set(table_names)):
            duplicates = [name for name in table_names if table_names.count(name) > 1]
            errors.append(f"Duplicate table names found: {set(duplicates)}")
        
        # Validate each table
        for table in self.schema.tables:
            # Check for duplicate field names
            field_names = [f.name for f in table.fields]
            if len(field_names) != len(set(field_names)):
                duplicates = [name for name in field_names if field_names.count(name) > 1]
                errors.append(
                    f"Table '{table.name}' has duplicate field names: {set(duplicates)}"
                )
            
            # Validate primary key exists
            if table.primary_key:
                if not table.get_field(table.primary_key):
                    errors.append(
                        f"Table '{table.name}' primary key '{table.primary_key}' "
                        f"not found in fields"
                    )
            
            # Validate foreign key references
            for fk in table.get_foreign_keys():
                target_table = self.schema.get_table(fk.target_table)
                if not target_table:
                    errors.append(
                        f"Table '{table.name}' foreign key references "
                        f"non-existent table '{fk.target_table}'"
                    )
                elif not target_table.get_field(fk.target_field):
                    errors.append(
                        f"Table '{table.name}' foreign key references "
                        f"non-existent field '{fk.target_table}.{fk.target_field}'"
                    )
        
        # Check for circular dependencies
        try:
            self.schema.topological_sort()
        except ValueError as e:
            errors.append(str(e))
        
        return len(errors) == 0, errors
    
    def validate_data(
        self, 
        data: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[bool, List[str]]:
        """
        Validate data against schema.
        
        Args:
            data: Dictionary mapping table names to lists of records
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return self.schema.validate_dataset(data)
    
    def enforce_constraints_on_generation(
        self,
        table_name: str,
        field_name: str,
        generated_value: Any
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Enforce constraints on a generated value, potentially modifying it.
        
        Args:
            table_name: Name of the table
            field_name: Name of the field
            generated_value: The generated value to validate/enforce
            
        Returns:
            Tuple of (is_valid, corrected_value, error_message)
        """
        table = self.schema.get_table(table_name)
        if not table:
            return False, generated_value, f"Table '{table_name}' not found in schema"
        
        field_def = table.get_field(field_name)
        if not field_def:
            return False, generated_value, f"Field '{field_name}' not found in table '{table_name}'"
        
        # Validate the value
        is_valid, errors = field_def.validate(generated_value)
        
        if is_valid:
            return True, generated_value, None
        else:
            return False, generated_value, "; ".join(errors)
