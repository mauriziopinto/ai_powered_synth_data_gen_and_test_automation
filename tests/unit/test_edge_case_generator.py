"""Unit tests for edge case generation functionality."""

import pytest
import pandas as pd
import numpy as np

from shared.utils.edge_case_generator import (
    EdgeCaseGenerator,
    EdgeCaseRule,
    EdgeCaseType,
    EdgeCasePattern,
    EdgeCasePatternLibrary,
    EdgeCaseInjectionResult
)


class TestEdgeCasePatternLibrary:
    """Tests for EdgeCasePatternLibrary."""
    
    def test_initialization(self):
        """Test that library initializes with default patterns."""
        library = EdgeCasePatternLibrary()
        assert len(library.patterns) > 0
        assert EdgeCaseType.MALFORMED_EMAIL in library.patterns
        assert EdgeCaseType.INVALID_POSTCODE in library.patterns
        assert EdgeCaseType.NULL_VALUE in library.patterns
