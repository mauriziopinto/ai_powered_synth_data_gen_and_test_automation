"""Validation utilities for synthetic data generation."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def validate_column_order(
    original_columns: List[str],
    synthetic_columns: List[str]
) -> Dict[str, Any]:
    """Validate that column order is preserved between original and synthetic data.
    
    Args:
        original_columns: Original column order from production data
        synthetic_columns: Synthetic data column order
        
    Returns:
        Validation report dictionary with the following keys:
        - order_preserved: bool indicating if orders match exactly
        - original_order: list of original column names
        - synthetic_order: list of synthetic column names
        - original_count: number of original columns
        - synthetic_count: number of synthetic columns
        - mismatches: list of position mismatches (if any)
        - missing_columns: columns in original but not in synthetic (if any)
        - extra_columns: columns in synthetic but not in original (if any)
    """
    matches = original_columns == synthetic_columns
    
    report = {
        'order_preserved': matches,
        'original_order': original_columns,
        'synthetic_order': synthetic_columns,
        'original_count': len(original_columns),
        'synthetic_count': len(synthetic_columns)
    }
    
    if not matches:
        # Find position mismatches
        mismatches = []
        max_len = max(len(original_columns), len(synthetic_columns))
        
        for i in range(max_len):
            orig = original_columns[i] if i < len(original_columns) else None
            synth = synthetic_columns[i] if i < len(synthetic_columns) else None
            
            if orig != synth:
                mismatches.append({
                    'position': i,
                    'expected': orig,
                    'actual': synth
                })
        
        report['mismatches'] = mismatches
        
        # Find missing and extra columns
        missing = [col for col in original_columns if col not in synthetic_columns]
        extra = [col for col in synthetic_columns if col not in original_columns]
        
        if missing:
            report['missing_columns'] = missing
            logger.warning(f"Missing columns in synthetic data: {missing}")
        
        if extra:
            report['extra_columns'] = extra
            logger.warning(f"Extra columns in synthetic data: {extra}")
        
        logger.info(
            f"Column order validation failed: {len(mismatches)} mismatches, "
            f"{len(missing)} missing, {len(extra)} extra"
        )
    else:
        logger.info("Column order validation passed: orders match exactly")
    
    return report


def validate_column_order_or_raise(
    original_columns: List[str],
    synthetic_columns: List[str],
    strict: bool = False
) -> None:
    """Validate column order and optionally raise error on mismatch.
    
    Args:
        original_columns: Expected column order
        synthetic_columns: Actual column order
        strict: If True, raise error on mismatch; if False, log warning
        
    Raises:
        ColumnOrderError: If strict=True and columns don't match
    """
    report = validate_column_order(original_columns, synthetic_columns)
    
    if not report['order_preserved']:
        message = (
            f"Column order mismatch detected.\n"
            f"Expected: {original_columns}\n"
            f"Got: {synthetic_columns}\n"
            f"Mismatches: {report.get('mismatches', [])}"
        )
        
        if strict:
            raise ColumnOrderError(message)
        else:
            logger.warning(message)


class ColumnOrderError(Exception):
    """Raised when column order cannot be preserved."""
    pass
