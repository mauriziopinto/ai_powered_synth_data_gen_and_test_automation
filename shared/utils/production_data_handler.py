"""Production data file handling with quality issue preservation."""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FileFormat(Enum):
    """Supported file formats."""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    UNKNOWN = "unknown"


class DataType(Enum):
    """Detected data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    NULL = "null"
    MIXED = "mixed"


@dataclass
class QualityIssue:
    """Represents a data quality issue."""
    issue_type: str
    field_name: str
    example_value: Any
    frequency: float  # Percentage of records with this issue
    pattern: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'issue_type': self.issue_type,
            'field_name': self.field_name,
            'example_value': str(self.example_value),
            'frequency': self.frequency,
            'pattern': self.pattern
        }


@dataclass
class FieldProfile:
    """Profile of a data field."""
    name: str
    data_type: DataType
    null_count: int
    total_count: int
    unique_count: int
    sample_values: List[Any] = field(default_factory=list)
    quality_issues: List[QualityIssue] = field(default_factory=list)
    is_masked: bool = False
    masking_pattern: Optional[str] = None
    
    @property
    def null_percentage(self) -> float:
        """Calculate null percentage."""
        return (self.null_count / self.total_count * 100) if self.total_count > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'data_type': self.data_type.value,
            'null_count': self.null_count,
            'null_percentage': self.null_percentage,
            'total_count': self.total_count,
            'unique_count': self.unique_count,
            'sample_values': self.sample_values[:5],  # Limit samples
            'quality_issues': [qi.to_dict() for qi in self.quality_issues],
            'is_masked': self.is_masked,
            'masking_pattern': self.masking_pattern
        }


@dataclass
class DataProfile:
    """Complete profile of a dataset."""
    file_path: str
    file_format: FileFormat
    row_count: int
    column_count: int
    field_profiles: List[FieldProfile]
    overall_quality_issues: List[QualityIssue] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'file_format': self.file_format.value,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'field_profiles': [fp.to_dict() for fp in self.field_profiles],
            'overall_quality_issues': [qi.to_dict() for qi in self.overall_quality_issues]
        }


class FormatDetector:
    """Detects file format from file extension and content."""
    
    @staticmethod
    def detect_format(file_path: str) -> FileFormat:
        """Detect file format.
        
        Args:
            file_path: Path to file
        
        Returns:
            Detected file format
        """
        path = Path(file_path)
        
        # Check extension
        extension = path.suffix.lower()
        
        if extension == '.csv':
            return FileFormat.CSV
        elif extension == '.json':
            return FileFormat.JSON
        elif extension == '.parquet':
            return FileFormat.PARQUET
        
        # Try to detect from content
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                
                # Check for JSON
                if first_line.startswith('{') or first_line.startswith('['):
                    return FileFormat.JSON
                
                # Check for CSV (has commas or tabs)
                if ',' in first_line or '\t' in first_line:
                    return FileFormat.CSV
        except Exception:
            pass
        
        return FileFormat.UNKNOWN


class QualityIssueDetector:
    """Detects data quality issues in field values."""
    
    # Email pattern (intentionally loose to catch malformed ones)
    EMAIL_PATTERN = re.compile(r'[^@\s]+@[^@\s]+')
    VALID_EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Phone patterns
    PHONE_PATTERN = re.compile(r'[\d\s\-\(\)\+]{7,}')
    
    # Postcode patterns (UK, US)
    UK_POSTCODE_PATTERN = re.compile(r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$', re.IGNORECASE)
    US_ZIP_PATTERN = re.compile(r'^\d{5}(-\d{4})?$')
    
    # Masking patterns
    MASKING_PATTERNS = [
        (re.compile(r'^X+$'), 'X_MASK'),
        (re.compile(r'^\*+$'), 'STAR_MASK'),
        (re.compile(r'^#+$'), 'HASH_MASK'),
        (re.compile(r'^-+$'), 'DASH_MASK'),
        (re.compile(r'^(XXX|xxx|###|\*\*\*)'), 'PREFIX_MASK')
    ]
    
    @classmethod
    def detect_issues(cls, field_name: str, values: List[Any]) -> List[QualityIssue]:
        """Detect quality issues in field values.
        
        Args:
            field_name: Name of the field
            values: List of field values
        
        Returns:
            List of detected quality issues
        """
        issues = []
        
        # Filter out None values for analysis
        non_null_values = [v for v in values if v is not None and str(v).strip()]
        
        if not non_null_values:
            return issues
        
        # Check for malformed emails
        if 'email' in field_name.lower() or 'mail' in field_name.lower():
            malformed = cls._check_malformed_emails(non_null_values)
            if malformed['count'] > 0:
                issues.append(QualityIssue(
                    issue_type='malformed_email',
                    field_name=field_name,
                    example_value=malformed['example'],
                    frequency=malformed['frequency']
                ))
        
        # Check for invalid postcodes
        if 'postcode' in field_name.lower() or 'zip' in field_name.lower() or 'postal' in field_name.lower():
            invalid = cls._check_invalid_postcodes(non_null_values)
            if invalid['count'] > 0:
                issues.append(QualityIssue(
                    issue_type='invalid_postcode',
                    field_name=field_name,
                    example_value=invalid['example'],
                    frequency=invalid['frequency']
                ))
        
        # Check for inconsistent phone formats
        if 'phone' in field_name.lower() or 'tel' in field_name.lower() or 'mobile' in field_name.lower():
            inconsistent = cls._check_inconsistent_phones(non_null_values)
            if inconsistent['count'] > 0:
                issues.append(QualityIssue(
                    issue_type='inconsistent_phone_format',
                    field_name=field_name,
                    example_value=inconsistent['example'],
                    frequency=inconsistent['frequency'],
                    pattern=inconsistent.get('pattern')
                ))
        
        return issues
    
    @classmethod
    def _check_malformed_emails(cls, values: List[Any]) -> Dict[str, Any]:
        """Check for malformed email addresses."""
        malformed_count = 0
        example = None
        
        for value in values:
            str_value = str(value).strip()
            if cls.EMAIL_PATTERN.search(str_value):
                if not cls.VALID_EMAIL_PATTERN.match(str_value):
                    malformed_count += 1
                    if example is None:
                        example = str_value
        
        return {
            'count': malformed_count,
            'frequency': (malformed_count / len(values) * 100) if values else 0,
            'example': example
        }
    
    @classmethod
    def _check_invalid_postcodes(cls, values: List[Any]) -> Dict[str, Any]:
        """Check for invalid postcodes."""
        invalid_count = 0
        example = None
        
        for value in values:
            str_value = str(value).strip()
            # Check if it looks like a postcode but doesn't match valid patterns
            if len(str_value) >= 3 and len(str_value) <= 10:
                if not cls.UK_POSTCODE_PATTERN.match(str_value) and not cls.US_ZIP_PATTERN.match(str_value):
                    # It might be invalid
                    if any(c.isdigit() for c in str_value):  # Has at least one digit
                        invalid_count += 1
                        if example is None:
                            example = str_value
        
        return {
            'count': invalid_count,
            'frequency': (invalid_count / len(values) * 100) if values else 0,
            'example': example
        }
    
    @classmethod
    def _check_inconsistent_phones(cls, values: List[Any]) -> Dict[str, Any]:
        """Check for inconsistent phone number formats."""
        formats = {}
        
        for value in values:
            str_value = str(value).strip()
            if cls.PHONE_PATTERN.match(str_value):
                # Determine format pattern
                pattern = cls._get_phone_pattern(str_value)
                formats[pattern] = formats.get(pattern, 0) + 1
        
        # If more than 2 different formats, consider it inconsistent
        inconsistent = len(formats) > 2
        
        return {
            'count': len(values) if inconsistent else 0,
            'frequency': 100.0 if inconsistent else 0.0,
            'example': values[0] if values and inconsistent else None,
            'pattern': f"{len(formats)} different formats" if inconsistent else None
        }
    
    @classmethod
    def _get_phone_pattern(cls, phone: str) -> str:
        """Get phone number format pattern."""
        # Replace digits with 'D', keep formatting characters
        pattern = re.sub(r'\d', 'D', phone)
        return pattern
    
    @classmethod
    def detect_masking(cls, values: List[Any]) -> Tuple[bool, Optional[str]]:
        """Detect if field contains masked values.
        
        Args:
            values: List of field values
        
        Returns:
            Tuple of (is_masked, masking_pattern)
        """
        if not values:
            return False, None
        
        # Sample values to check
        sample_size = min(100, len(values))
        sample = [str(v).strip() for v in values[:sample_size] if v is not None]
        
        if not sample:
            return False, None
        
        # Check each masking pattern
        for pattern, pattern_name in cls.MASKING_PATTERNS:
            matches = sum(1 for v in sample if pattern.match(v))
            
            # If more than 50% match, consider it masked
            if matches / len(sample) > 0.5:
                return True, pattern_name
        
        return False, None


class DataTypeDetector:
    """Detects data types from values."""
    
    DATE_PATTERNS = [
        re.compile(r'^\d{4}-\d{2}-\d{2}$'),  # YYYY-MM-DD
        re.compile(r'^\d{2}/\d{2}/\d{4}$'),  # DD/MM/YYYY or MM/DD/YYYY
        re.compile(r'^\d{2}-\d{2}-\d{4}$'),  # DD-MM-YYYY
    ]
    
    DATETIME_PATTERNS = [
        re.compile(r'^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}'),  # ISO format
    ]
    
    @classmethod
    def detect_type(cls, values: List[Any]) -> DataType:
        """Detect data type from values.
        
        Args:
            values: List of values
        
        Returns:
            Detected data type
        """
        if not values:
            return DataType.NULL
        
        # Filter out None values
        non_null = [v for v in values if v is not None]
        
        if not non_null:
            return DataType.NULL
        
        # Sample values for type detection
        sample_size = min(100, len(non_null))
        sample = non_null[:sample_size]
        
        # Count types
        type_counts = {
            DataType.INTEGER: 0,
            DataType.FLOAT: 0,
            DataType.BOOLEAN: 0,
            DataType.DATE: 0,
            DataType.DATETIME: 0,
            DataType.STRING: 0
        }
        
        for value in sample:
            detected = cls._detect_single_value_type(value)
            type_counts[detected] += 1
        
        # Find dominant type (>80% of samples)
        total = len(sample)
        for dtype, count in type_counts.items():
            if count / total > 0.8:
                return dtype
        
        return DataType.MIXED
    
    @classmethod
    def _detect_single_value_type(cls, value: Any) -> DataType:
        """Detect type of a single value."""
        if value is None:
            return DataType.NULL
        
        str_value = str(value).strip().lower()
        
        # Check boolean
        if str_value in ('true', 'false', '1', '0', 'yes', 'no', 't', 'f'):
            return DataType.BOOLEAN
        
        # Check datetime
        for pattern in cls.DATETIME_PATTERNS:
            if pattern.match(str(value)):
                return DataType.DATETIME
        
        # Check date
        for pattern in cls.DATE_PATTERNS:
            if pattern.match(str(value)):
                return DataType.DATE
        
        # Check numeric
        try:
            float_val = float(value)
            if '.' in str(value) or 'e' in str_value:
                return DataType.FLOAT
            else:
                return DataType.INTEGER
        except (ValueError, TypeError):
            pass
        
        return DataType.STRING
