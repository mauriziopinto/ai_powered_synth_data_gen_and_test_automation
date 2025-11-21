"""Edge case generation and injection for synthetic data."""

import re
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class EdgeCaseType(Enum):
    """Types of edge cases that can be generated."""
    MALFORMED_EMAIL = "malformed_email"
    INVALID_POSTCODE = "invalid_postcode"
    MALFORMED_PHONE = "malformed_phone"
    MISSING_REQUIRED = "missing_required"
    BOUNDARY_VALUE = "boundary_value"
    INVALID_REFERENCE = "invalid_reference"
    SPECIAL_CHARACTERS = "special_characters"
    WHITESPACE_ONLY = "whitespace_only"
    EMPTY_STRING = "empty_string"
    EXTREMELY_LONG = "extremely_long"
    NEGATIVE_VALUE = "negative_value"
    ZERO_VALUE = "zero_value"
    NULL_VALUE = "null_value"
    INVALID_DATE = "invalid_date"
    FUTURE_DATE = "future_date"
    PAST_DATE = "past_date"


@dataclass
class EdgeCasePattern:
    """Definition of an edge case pattern."""
    name: str
    edge_case_type: EdgeCaseType
    description: str
    generator: Callable[[Any], Any]
    applicable_types: List[str] = field(default_factory=list)
    
    def applies_to(self, field_type: str) -> bool:
        """Check if this pattern applies to a field type.
        
        Args:
            field_type: The data type of the field
            
        Returns:
            True if pattern applies to this field type
        """
        if not self.applicable_types:
            return True
        return field_type in self.applicable_types


class EdgeCasePatternLibrary:
    """Library of edge case patterns for different data types."""
    
    def __init__(self):
        """Initialize the edge case pattern library."""
        self.patterns: Dict[EdgeCaseType, EdgeCasePattern] = {}
        self._register_default_patterns()
    
    def _register_default_patterns(self):
        """Register default edge case patterns."""
        
        # Email patterns
        self.register_pattern(EdgeCasePattern(
            name="Malformed Email - Missing @",
            edge_case_type=EdgeCaseType.MALFORMED_EMAIL,
            description="Email address missing @ symbol",
            generator=lambda val: str(val).replace('@', '') if '@' in str(val) else 'userexample.com',
            applicable_types=['email', 'string']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Malformed Email - Double @",
            edge_case_type=EdgeCaseType.MALFORMED_EMAIL,
            description="Email address with double @ symbol",
            generator=lambda val: str(val).replace('@', '@@', 1) if '@' in str(val) else 'user@@example.com',
            applicable_types=['email', 'string']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Malformed Email - Missing Domain",
            edge_case_type=EdgeCaseType.MALFORMED_EMAIL,
            description="Email address missing domain part",
            generator=lambda val: str(val).split('@')[0] + '@' if '@' in str(val) else 'user@',
            applicable_types=['email', 'string']
        ))
        
        # Postcode patterns
        self.register_pattern(EdgeCasePattern(
            name="Invalid Postcode - Wrong Format",
            edge_case_type=EdgeCaseType.INVALID_POSTCODE,
            description="Postcode with invalid format",
            generator=lambda val: 'XXXXX' if val else 'XXXXX',
            applicable_types=['postcode', 'postal_code', 'zip', 'string']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Invalid Postcode - Too Short",
            edge_case_type=EdgeCaseType.INVALID_POSTCODE,
            description="Postcode that is too short",
            generator=lambda val: str(val)[:2] if val and len(str(val)) > 2 else '12',
            applicable_types=['postcode', 'postal_code', 'zip', 'string']
        ))
        
        # Phone patterns
        self.register_pattern(EdgeCasePattern(
            name="Malformed Phone - Invalid Characters",
            edge_case_type=EdgeCaseType.MALFORMED_PHONE,
            description="Phone number with invalid characters",
            generator=lambda val: str(val).replace('0', 'O').replace('1', 'I') if val else 'OOOO-OOOO',
            applicable_types=['phone', 'phone_number', 'string']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Malformed Phone - Too Short",
            edge_case_type=EdgeCaseType.MALFORMED_PHONE,
            description="Phone number that is too short",
            generator=lambda val: str(val)[:5] if val and len(str(val)) > 5 else '12345',
            applicable_types=['phone', 'phone_number', 'string']
        ))
        
        # String patterns
        self.register_pattern(EdgeCasePattern(
            name="Empty String",
            edge_case_type=EdgeCaseType.EMPTY_STRING,
            description="Empty string value",
            generator=lambda val: '',
            applicable_types=['string', 'text']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Whitespace Only",
            edge_case_type=EdgeCaseType.WHITESPACE_ONLY,
            description="String containing only whitespace",
            generator=lambda val: '   ',
            applicable_types=['string', 'text']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Special Characters",
            edge_case_type=EdgeCaseType.SPECIAL_CHARACTERS,
            description="String with special characters",
            generator=lambda val: f"<script>{val}</script>" if val else "<script>alert('test')</script>",
            applicable_types=['string', 'text']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Extremely Long String",
            edge_case_type=EdgeCaseType.EXTREMELY_LONG,
            description="String that exceeds typical length limits",
            generator=lambda val: str(val) * 100 if val else 'X' * 1000,
            applicable_types=['string', 'text']
        ))
        
        # Numeric patterns
        self.register_pattern(EdgeCasePattern(
            name="Negative Value",
            edge_case_type=EdgeCaseType.NEGATIVE_VALUE,
            description="Negative numeric value where positive expected",
            generator=lambda val: -abs(float(val)) if val is not None else -1,
            applicable_types=['integer', 'float', 'number']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Zero Value",
            edge_case_type=EdgeCaseType.ZERO_VALUE,
            description="Zero value",
            generator=lambda val: 0,
            applicable_types=['integer', 'float', 'number']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Boundary Value - Max",
            edge_case_type=EdgeCaseType.BOUNDARY_VALUE,
            description="Maximum boundary value",
            generator=lambda val: 2147483647,  # Max 32-bit int
            applicable_types=['integer', 'number']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Boundary Value - Min",
            edge_case_type=EdgeCaseType.BOUNDARY_VALUE,
            description="Minimum boundary value",
            generator=lambda val: -2147483648,  # Min 32-bit int
            applicable_types=['integer', 'number']
        ))
        
        # Null/Missing patterns
        self.register_pattern(EdgeCasePattern(
            name="Null Value",
            edge_case_type=EdgeCaseType.NULL_VALUE,
            description="Null/None value",
            generator=lambda val: None,
            applicable_types=['string', 'integer', 'float', 'date', 'boolean']
        ))
        
        # Date patterns
        self.register_pattern(EdgeCasePattern(
            name="Invalid Date Format",
            edge_case_type=EdgeCaseType.INVALID_DATE,
            description="Date in invalid format",
            generator=lambda val: '99/99/9999',
            applicable_types=['date', 'datetime']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Future Date",
            edge_case_type=EdgeCaseType.FUTURE_DATE,
            description="Date far in the future",
            generator=lambda val: '2099-12-31',
            applicable_types=['date', 'datetime']
        ))
        
        self.register_pattern(EdgeCasePattern(
            name="Past Date",
            edge_case_type=EdgeCaseType.PAST_DATE,
            description="Date far in the past",
            generator=lambda val: '1900-01-01',
            applicable_types=['date', 'datetime']
        ))
    
    def register_pattern(self, pattern: EdgeCasePattern):
        """Register an edge case pattern.
        
        Args:
            pattern: EdgeCasePattern to register
        """
        self.patterns[pattern.edge_case_type] = pattern
        logger.debug(f"Registered edge case pattern: {pattern.name}")
    
    def get_pattern(self, edge_case_type: EdgeCaseType) -> Optional[EdgeCasePattern]:
        """Get a pattern by type.
        
        Args:
            edge_case_type: Type of edge case
            
        Returns:
            EdgeCasePattern if found, None otherwise
        """
        return self.patterns.get(edge_case_type)
    
    def get_applicable_patterns(self, field_type: str) -> List[EdgeCasePattern]:
        """Get all patterns applicable to a field type.
        
        Args:
            field_type: Data type of the field
            
        Returns:
            List of applicable EdgeCasePatterns
        """
        return [
            pattern for pattern in self.patterns.values()
            if pattern.applies_to(field_type)
        ]


@dataclass
class EdgeCaseRule:
    """Rule for injecting edge cases into a specific field."""
    field_name: str
    edge_case_types: List[EdgeCaseType]
    frequency: float  # 0.0 to 1.0
    field_type: Optional[str] = None
    
    def __post_init__(self):
        """Validate the rule after initialization."""
        if not 0.0 <= self.frequency <= 1.0:
            raise ValueError(f"Frequency must be between 0.0 and 1.0, got {self.frequency}")
        
        if not self.edge_case_types:
            raise ValueError("At least one edge case type must be specified")


@dataclass
class EdgeCaseInjectionResult:
    """Result of edge case injection."""
    total_records: int
    injected_count: int
    injected_indices: List[int]
    edge_case_tags: Dict[int, List[EdgeCaseType]]
    frequency_achieved: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_records': self.total_records,
            'injected_count': self.injected_count,
            'injected_indices': self.injected_indices,
            'edge_case_tags': {
                idx: [ect.value for ect in types]
                for idx, types in self.edge_case_tags.items()
            },
            'frequency_achieved': self.frequency_achieved
        }


class EdgeCaseGenerator:
    """Generator for injecting edge cases into synthetic data."""
    
    def __init__(self, pattern_library: Optional[EdgeCasePatternLibrary] = None):
        """Initialize edge case generator.
        
        Args:
            pattern_library: Optional custom pattern library
        """
        self.pattern_library = pattern_library or EdgeCasePatternLibrary()
        logger.info("Initialized EdgeCaseGenerator")
    
    def inject_edge_cases(
        self,
        data: pd.DataFrame,
        rules: List[EdgeCaseRule],
        seed: Optional[int] = None,
        tag_column: str = '_edge_case_tags'
    ) -> tuple[pd.DataFrame, EdgeCaseInjectionResult]:
        """Inject edge cases into a DataFrame according to rules.
        
        Args:
            data: DataFrame to inject edge cases into
            rules: List of EdgeCaseRules defining what to inject
            seed: Random seed for reproducibility
            tag_column: Name of column to store edge case tags
            
        Returns:
            Tuple of (modified DataFrame, EdgeCaseInjectionResult)
        """
        if seed is not None:
            np.random.seed(seed)
        
        logger.info(f"Injecting edge cases into {len(data)} records with {len(rules)} rules")
        
        # Create a copy to avoid modifying original
        result_df = data.copy()
        
        # Initialize tag column if it doesn't exist
        if tag_column not in result_df.columns:
            result_df[tag_column] = [[] for _ in range(len(result_df))]
        
        total_injected = 0
        all_injected_indices = set()
        edge_case_tags = {}
        
        # Process each rule
        for rule in rules:
            if rule.field_name not in result_df.columns:
                logger.warning(f"Field '{rule.field_name}' not found in DataFrame, skipping rule")
                continue
            
            # Calculate number of records to inject
            num_to_inject = int(len(result_df) * rule.frequency)
            
            if num_to_inject == 0:
                logger.debug(f"Frequency {rule.frequency} too low to inject any edge cases for '{rule.field_name}'")
                continue
            
            # Randomly select indices to inject
            available_indices = list(range(len(result_df)))
            selected_indices = np.random.choice(
                available_indices,
                size=min(num_to_inject, len(available_indices)),
                replace=False
            )
            
            logger.info(
                f"Injecting {len(selected_indices)} edge cases into field '{rule.field_name}' "
                f"(target frequency: {rule.frequency:.2%})"
            )
            
            # Inject edge cases at selected indices
            for idx in selected_indices:
                # Randomly select an edge case type from the rule
                edge_case_type = np.random.choice(rule.edge_case_types)
                
                # Get the pattern
                pattern = self.pattern_library.get_pattern(edge_case_type)
                
                if pattern is None:
                    logger.warning(f"Pattern not found for edge case type: {edge_case_type}")
                    continue
                
                # Check if pattern applies to field type
                if rule.field_type and not pattern.applies_to(rule.field_type):
                    logger.debug(
                        f"Pattern '{pattern.name}' does not apply to field type '{rule.field_type}', "
                        "selecting another pattern"
                    )
                    # Try to find an applicable pattern
                    applicable_types = [
                        ect for ect in rule.edge_case_types
                        if self.pattern_library.get_pattern(ect) and
                        self.pattern_library.get_pattern(ect).applies_to(rule.field_type)
                    ]
                    if applicable_types:
                        edge_case_type = np.random.choice(applicable_types)
                        pattern = self.pattern_library.get_pattern(edge_case_type)
                    else:
                        logger.warning(
                            f"No applicable patterns found for field type '{rule.field_type}', "
                            "using pattern anyway"
                        )
                
                # Get original value
                original_value = result_df.at[idx, rule.field_name]
                
                # Generate edge case value
                try:
                    edge_case_value = pattern.generator(original_value)
                    result_df.at[idx, rule.field_name] = edge_case_value
                    
                    # Tag the record
                    if idx not in edge_case_tags:
                        edge_case_tags[idx] = []
                    edge_case_tags[idx].append(edge_case_type)
                    
                    # Update tag column
                    current_tags = result_df.at[idx, tag_column]
                    if not isinstance(current_tags, list):
                        current_tags = []
                    current_tags.append({
                        'field': rule.field_name,
                        'type': edge_case_type.value,
                        'description': pattern.description
                    })
                    result_df.at[idx, tag_column] = current_tags
                    
                    all_injected_indices.add(idx)
                    total_injected += 1
                    
                    logger.debug(
                        f"Injected edge case at index {idx}, field '{rule.field_name}': "
                        f"{pattern.name} (original: {original_value}, new: {edge_case_value})"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to generate edge case for field '{rule.field_name}' "
                        f"at index {idx}: {e}"
                    )
        
        # Calculate achieved frequency
        frequency_achieved = len(all_injected_indices) / len(result_df) if len(result_df) > 0 else 0.0
        
        result = EdgeCaseInjectionResult(
            total_records=len(result_df),
            injected_count=len(all_injected_indices),
            injected_indices=sorted(list(all_injected_indices)),
            edge_case_tags=edge_case_tags,
            frequency_achieved=frequency_achieved
        )
        
        logger.info(
            f"Edge case injection complete: {result.injected_count} records modified "
            f"({result.frequency_achieved:.2%} of total)"
        )
        
        return result_df, result
    
    def validate_frequency(
        self,
        result: EdgeCaseInjectionResult,
        target_frequency: float,
        tolerance: float = 0.05
    ) -> bool:
        """Validate that achieved frequency is within tolerance of target.
        
        Args:
            result: EdgeCaseInjectionResult from injection
            target_frequency: Target frequency (0.0 to 1.0)
            tolerance: Acceptable deviation (default 0.05 = ±5%)
            
        Returns:
            True if frequency is within tolerance, False otherwise
        """
        deviation = abs(result.frequency_achieved - target_frequency)
        is_valid = deviation <= tolerance
        
        if is_valid:
            logger.info(
                f"Frequency validation passed: achieved {result.frequency_achieved:.2%}, "
                f"target {target_frequency:.2%}, deviation {deviation:.2%}"
            )
        else:
            logger.warning(
                f"Frequency validation failed: achieved {result.frequency_achieved:.2%}, "
                f"target {target_frequency:.2%}, deviation {deviation:.2%} "
                f"(tolerance: ±{tolerance:.2%})"
            )
        
        return is_valid
    
    def create_rules_from_config(
        self,
        field_configs: Dict[str, Dict[str, Any]]
    ) -> List[EdgeCaseRule]:
        """Create edge case rules from configuration dictionary.
        
        Args:
            field_configs: Dictionary mapping field names to config dicts with keys:
                - 'edge_case_types': List of EdgeCaseType enum values or strings
                - 'frequency': Float between 0.0 and 1.0
                - 'field_type': Optional string indicating field type
                
        Returns:
            List of EdgeCaseRules
        """
        rules = []
        
        for field_name, config in field_configs.items():
            # Parse edge case types
            edge_case_types = []
            for ect in config.get('edge_case_types', []):
                if isinstance(ect, EdgeCaseType):
                    edge_case_types.append(ect)
                elif isinstance(ect, str):
                    try:
                        edge_case_types.append(EdgeCaseType(ect))
                    except ValueError:
                        logger.warning(f"Unknown edge case type: {ect}")
                else:
                    logger.warning(f"Invalid edge case type: {ect}")
            
            if not edge_case_types:
                logger.warning(f"No valid edge case types for field '{field_name}', skipping")
                continue
            
            # Create rule
            rule = EdgeCaseRule(
                field_name=field_name,
                edge_case_types=edge_case_types,
                frequency=config.get('frequency', 0.05),
                field_type=config.get('field_type')
            )
            rules.append(rule)
            
            logger.debug(f"Created edge case rule for field '{field_name}'")
        
        logger.info(f"Created {len(rules)} edge case rules from configuration")
        return rules
