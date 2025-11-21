"""Unit tests for Data Processor Agent."""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime

from agents.data_processor import (
    DataProcessorAgent,
    PatternClassifier,
    NameBasedClassifier,
    ContentAnalysisClassifier,
    ClassificationScore
)


class TestPatternClassifier:
    """Test pattern-based classifier."""
    
    def test_email_detection(self):
        """Test email pattern detection."""
        classifier = PatternClassifier()
        samples = pd.Series(['user@example.com', 'test@test.org', 'admin@company.co.uk'])
        
        result = classifier.classify('email_field', samples, {})
        
        assert result.sensitivity_type == 'email'
        assert result.confidence > 0.8
        assert 'email' in result.reasoning.lower()
    
    def test_phone_detection(self):
        """Test phone number pattern detection."""
        classifier = PatternClassifier()
        samples = pd.Series(['555-123-4567', '555.123.4567', '5551234567'])
        
        result = classifier.classify('phone_field', samples, {})
        
        assert result.sensitivity_type == 'phone'
        assert result.confidence > 0.8
    
    def test_ssn_detection(self):
        """Test SSN pattern detection."""
        classifier = PatternClassifier()
        samples = pd.Series(['123-45-6789', '987-65-4321', '555-12-3456'])
        
        result = classifier.classify('ssn_field', samples, {})
        
        assert result.sensitivity_type == 'ssn'
        assert result.confidence > 0.8
        assert 'ssn' in result.reasoning.lower()
    
    def test_credit_card_detection(self):
        """Test credit card pattern detection."""
        classifier = PatternClassifier()
        samples = pd.Series(['1234-5678-9012-3456', '9876 5432 1098 7654'])
        
        result = classifier.classify('cc_field', samples, {})
        
        assert result.sensitivity_type == 'credit_card'
        assert result.confidence > 0.0
    
    def test_postal_code_detection(self):
        """Test postal code pattern detection."""
        classifier = PatternClassifier()
        samples = pd.Series(['12345', '98765-4321', '12345-6789'])
        
        result = classifier.classify('zip_field', samples, {})
        
        assert result.sensitivity_type == 'postal_code'
        assert result.confidence > 0.0
    
    def test_date_of_birth_detection(self):
        """Test date of birth pattern detection."""
        classifier = PatternClassifier()
        samples = pd.Series(['01/15/1990', '12-25-1985', '1995-06-30'])
        
        result = classifier.classify('dob_field', samples, {})
        
        assert result.sensitivity_type == 'date_of_birth'
        assert result.confidence > 0.0
    
    def test_ip_address_detection(self):
        """Test IP address pattern detection."""
        classifier = PatternClassifier()
        samples = pd.Series(['192.168.1.1', '10.0.0.1', '172.16.0.1'])
        
        result = classifier.classify('ip_field', samples, {})
        
        assert result.sensitivity_type == 'ip_address'
        assert result.confidence > 0.8
    
    def test_partial_match_confidence(self):
        """Test confidence calculation with partial matches."""
        classifier = PatternClassifier()
        # Only 2 out of 4 are emails
        samples = pd.Series(['user@example.com', 'not_an_email', 'test@test.org', 'also_not'])
        
        result = classifier.classify('mixed_field', samples, {})
        
        # Should detect email but with lower confidence
        assert result.sensitivity_type == 'email'
        assert 0.4 < result.confidence < 0.6
    
    def test_empty_samples(self):
        """Test handling of empty sample data."""
        classifier = PatternClassifier()
        samples = pd.Series([None, None, None])
        
        result = classifier.classify('empty_field', samples, {})
        
        assert result.confidence == 0.0
        assert result.sensitivity_type == 'unknown'
        assert 'no non-null values' in result.reasoning.lower()
    
    def test_numeric_column_skipped(self):
        """Test that numeric columns skip pattern matching."""
        classifier = PatternClassifier()
        samples = pd.Series([1234567890, 9876543210, 5551234567], dtype='int64')
        
        result = classifier.classify('numeric_field', samples, {})
        
        assert result.confidence == 0.0
        assert 'numeric column' in result.reasoning.lower()
    
    def test_pattern_matches_captured(self):
        """Test that pattern matches are captured in result."""
        classifier = PatternClassifier()
        samples = pd.Series(['user@example.com', 'test@test.org', 'admin@company.co.uk'])
        
        result = classifier.classify('email_field', samples, {})
        
        assert result.pattern_matches is not None
        assert len(result.pattern_matches) > 0
        assert any('@' in match for match in result.pattern_matches)
    
    def test_no_pattern_match(self):
        """Test when no patterns match."""
        classifier = PatternClassifier()
        samples = pd.Series(['abc', 'def', 'ghi'])
        
        result = classifier.classify('random_field', samples, {})
        
        assert result.confidence == 0.0
        assert result.sensitivity_type == 'unknown'


class TestNameBasedClassifier:
    """Test name-based classifier."""
    
    def test_email_field_name(self):
        """Test email field name detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        result = classifier.classify('email_address', samples, {})
        
        assert result.sensitivity_type == 'email'
        assert result.confidence == 0.85
    
    def test_phone_field_name(self):
        """Test phone field name detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        result = classifier.classify('phone_number', samples, {})
        
        assert result.sensitivity_type == 'phone'
        assert result.confidence == 0.85
    
    def test_name_field_detection(self):
        """Test name field detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        # Test various name field patterns
        for field_name in ['first_name', 'last_name', 'surname', 'full_name']:
            result = classifier.classify(field_name, samples, {})
            assert result.sensitivity_type == 'name'
            assert result.confidence == 0.85
    
    def test_address_field_detection(self):
        """Test address field detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        for field_name in ['address', 'street', 'city', 'postal', 'zip']:
            result = classifier.classify(field_name, samples, {})
            assert result.sensitivity_type == 'address'
            assert result.confidence == 0.85
    
    def test_ssn_field_detection(self):
        """Test SSN field detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        result = classifier.classify('ssn', samples, {})
        
        assert result.sensitivity_type == 'ssn'
        assert result.confidence == 0.85
    
    def test_dob_field_detection(self):
        """Test date of birth field detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        for field_name in ['dob', 'birth_date', 'date_of_birth']:
            result = classifier.classify(field_name, samples, {})
            assert result.sensitivity_type == 'dob'
            assert result.confidence == 0.85
    
    def test_credit_card_field_detection(self):
        """Test credit card field detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        result = classifier.classify('credit_card', samples, {})
        
        assert result.sensitivity_type == 'credit_card'
        assert result.confidence == 0.85
    
    def test_password_field_detection(self):
        """Test password field detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        result = classifier.classify('password', samples, {})
        
        assert result.sensitivity_type == 'password'
        assert result.confidence == 0.85
    
    def test_account_field_detection(self):
        """Test account field detection."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        result = classifier.classify('account_number', samples, {})
        
        assert result.sensitivity_type == 'account'
        assert result.confidence == 0.85
    
    def test_case_insensitive_matching(self):
        """Test that field name matching is case insensitive."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        # Test with different cases
        for field_name in ['EMAIL', 'Email', 'EMAIL_ADDRESS', 'Email_Address']:
            result = classifier.classify(field_name, samples, {})
            assert result.sensitivity_type == 'email'
            assert result.confidence == 0.85
    
    def test_underscore_and_space_handling(self):
        """Test that underscores and spaces are handled correctly."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        # Test with underscores and spaces
        for field_name in ['phone_number', 'phonenumber', 'phone number']:
            result = classifier.classify(field_name, samples, {})
            assert result.sensitivity_type == 'phone'
            assert result.confidence == 0.85
    
    def test_partial_field_name_match(self):
        """Test that partial field name matches work."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        # Field name contains keyword
        result = classifier.classify('customer_email_address', samples, {})
        
        assert result.sensitivity_type == 'email'
        assert result.confidence == 0.85
    
    def test_no_match(self):
        """Test when field name doesn't match."""
        classifier = NameBasedClassifier()
        samples = pd.Series(['value1', 'value2'])
        
        result = classifier.classify('random_column', samples, {})
        
        assert result.confidence == 0.0
        assert result.sensitivity_type == 'unknown'


class TestContentAnalysisClassifier:
    """Test content analysis classifier."""
    
    def test_high_cardinality_numeric_detection(self):
        """Test detection of high cardinality numeric fields (identifiers)."""
        classifier = ContentAnalysisClassifier()
        # Create unique numeric values
        samples = pd.Series(range(100), dtype='int64')
        
        result = classifier.classify('id_field', samples, {})
        
        assert result.confidence > 0.0
        assert result.sensitivity_type == 'identifier'
        assert 'cardinality' in result.reasoning.lower()
    
    def test_high_cardinality_string_detection(self):
        """Test detection of high cardinality string fields."""
        classifier = ContentAnalysisClassifier()
        # Create unique string values
        samples = pd.Series([f'value_{i}' for i in range(100)])
        
        result = classifier.classify('id_field', samples, {})
        
        assert result.confidence > 0.0
        assert 'identifier' in result.sensitivity_type or 'text_pii' in result.sensitivity_type
    
    def test_text_pii_detection(self):
        """Test detection of potential text PII (high uniqueness + special chars)."""
        classifier = ContentAnalysisClassifier()
        # Create unique strings with special characters
        samples = pd.Series([f'user_{i}@example.com' for i in range(100)])
        
        result = classifier.classify('text_field', samples, {})
        
        assert result.confidence > 0.0
        assert 'text_pii' in result.sensitivity_type
        assert 'special characters' in result.reasoning.lower()
    
    def test_low_cardinality_ignored(self):
        """Test that low cardinality fields are not flagged."""
        classifier = ContentAnalysisClassifier()
        # Create repeated values
        samples = pd.Series(['value1'] * 50 + ['value2'] * 50)
        
        result = classifier.classify('category_field', samples, {})
        
        assert result.confidence == 0.0
        assert result.sensitivity_type == 'unknown'
    
    def test_numeric_low_uniqueness(self):
        """Test numeric fields with low uniqueness."""
        classifier = ContentAnalysisClassifier()
        # Create numeric values with low uniqueness
        samples = pd.Series([1, 2, 3, 1, 2, 3, 1, 2, 3] * 10, dtype='int64')
        
        result = classifier.classify('category_field', samples, {})
        
        assert result.confidence == 0.0
    
    def test_string_without_special_chars(self):
        """Test high uniqueness strings without special characters."""
        classifier = ContentAnalysisClassifier()
        # Create unique strings without special characters
        samples = pd.Series([f'value{i}' for i in range(100)])
        
        result = classifier.classify('text_field', samples, {})
        
        # Should detect as identifier due to high uniqueness
        assert result.confidence > 0.0
        assert result.sensitivity_type == 'identifier'
    
    def test_long_strings_with_special_chars(self):
        """Test long strings with special characters."""
        classifier = ContentAnalysisClassifier()
        # Create long unique strings with special characters
        samples = pd.Series([f'this_is_a_long_string_with_special_chars_{i}@#$' for i in range(100)])
        
        result = classifier.classify('text_field', samples, {})
        
        assert result.confidence > 0.0
        assert result.sensitivity_type == 'text_pii'
    
    def test_empty_values(self):
        """Test handling of empty values."""
        classifier = ContentAnalysisClassifier()
        samples = pd.Series([None, None, None])
        
        result = classifier.classify('empty_field', samples, {})
        
        assert result.confidence == 0.0
        assert 'no non-null values' in result.reasoning.lower()
    
    def test_mixed_null_and_values(self):
        """Test handling of mixed null and non-null values."""
        classifier = ContentAnalysisClassifier()
        # Half nulls, half unique values
        samples = pd.Series([None] * 50 + [f'value_{i}' for i in range(50)])
        
        result = classifier.classify('mixed_field', samples, {})
        
        # Should still detect based on non-null values
        assert result.confidence > 0.0


class TestDataProcessorAgent:
    """Test Data Processor Agent."""
    
    def test_load_csv(self, tmp_path):
        """Test loading CSV file."""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com'],
            'name': ['John Doe', 'Jane Smith'],
            'age': [25, 30]
        })
        df.to_csv(csv_file, index=False)
        
        agent = DataProcessorAgent()
        loaded_df = agent.load_data(csv_file)
        
        assert len(loaded_df) == 2
        assert 'email' in loaded_df.columns
    
    def test_load_json(self, tmp_path):
        """Test loading JSON file."""
        json_file = tmp_path / "test.json"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com'],
            'name': ['John Doe', 'Jane Smith']
        })
        df.to_json(json_file, orient='records')
        
        agent = DataProcessorAgent()
        loaded_df = agent.load_data(json_file)
        
        assert len(loaded_df) == 2
        assert 'email' in loaded_df.columns
    
    @pytest.mark.skipif(
        not any([
            __import__('importlib').util.find_spec('pyarrow'),
            __import__('importlib').util.find_spec('fastparquet')
        ]),
        reason="Parquet support requires pyarrow or fastparquet"
    )
    def test_load_parquet(self, tmp_path):
        """Test loading Parquet file."""
        parquet_file = tmp_path / "test.parquet"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com'],
            'name': ['John Doe', 'Jane Smith']
        })
        df.to_parquet(parquet_file)
        
        agent = DataProcessorAgent()
        loaded_df = agent.load_data(parquet_file)
        
        assert len(loaded_df) == 2
        assert 'email' in loaded_df.columns
    
    def test_load_unsupported_format(self, tmp_path):
        """Test loading unsupported file format."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("some text")
        
        agent = DataProcessorAgent()
        
        with pytest.raises(ValueError, match='Unsupported file format'):
            agent.load_data(txt_file)
    
    def test_profile_data(self):
        """Test data profiling."""
        df = pd.DataFrame({
            'numeric': [1, 2, 3, 4, 5],
            'text': ['a', 'b', 'c', 'd', 'e'],
            'with_nulls': [1, None, 3, None, 5]
        })
        
        agent = DataProcessorAgent()
        profile = agent.profile_data(df)
        
        assert 'numeric' in profile
        assert 'text' in profile
        assert 'with_nulls' in profile
        
        # Check numeric stats
        assert 'mean' in profile['numeric']
        assert profile['numeric']['mean'] == 3.0
        assert 'std' in profile['numeric']
        assert 'min' in profile['numeric']
        assert 'max' in profile['numeric']
        
        # Check null stats
        assert profile['with_nulls']['null_count'] == 2
        assert profile['with_nulls']['null_percentage'] == 0.4
        
        # Check unique stats
        assert profile['text']['unique_count'] == 5
        assert profile['text']['unique_percentage'] == 1.0
    
    def test_profile_data_string_stats(self):
        """Test data profiling for string columns."""
        df = pd.DataFrame({
            'short': ['a', 'b', 'c'],
            'long': ['hello world', 'this is longer', 'short']
        })
        
        agent = DataProcessorAgent()
        profile = agent.profile_data(df)
        
        # Check string stats
        assert 'avg_length' in profile['short']
        assert 'max_length' in profile['short']
        assert 'min_length' in profile['short']
        
        assert profile['short']['avg_length'] == 1.0
        assert profile['short']['max_length'] == 1
        assert profile['short']['min_length'] == 1
    
    def test_aggregate_scores_high_confidence_pattern(self):
        """Test score aggregation with high confidence pattern match."""
        agent = DataProcessorAgent()
        
        scores = {
            'pattern': ClassificationScore(
                confidence=0.9,
                sensitivity_type='email',
                reasoning='Pattern match'
            ),
            'name': ClassificationScore(
                confidence=0.8,
                sensitivity_type='email',
                reasoning='Name match'
            ),
            'content': ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='No match'
            )
        }
        
        result = agent.aggregate_scores(scores)
        
        assert result.confidence > 0.7
        assert result.sensitivity_type == 'email'
        assert 'pattern' in result.reasoning.lower()
    
    def test_aggregate_scores_name_based_priority(self):
        """Test score aggregation prioritizing name-based classification."""
        agent = DataProcessorAgent()
        
        scores = {
            'pattern': ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='No pattern match'
            ),
            'name': ClassificationScore(
                confidence=0.85,
                sensitivity_type='email',
                reasoning='Field name indicates email'
            ),
            'content': ClassificationScore(
                confidence=0.4,
                sensitivity_type='identifier',
                reasoning='High uniqueness'
            )
        }
        
        result = agent.aggregate_scores(scores)
        
        # Name-based should be weighted heavily
        assert result.confidence >= 0.7
        assert result.sensitivity_type == 'email'
    
    def test_aggregate_scores_all_zero(self):
        """Test score aggregation when all classifiers return zero confidence."""
        agent = DataProcessorAgent()
        
        scores = {
            'pattern': ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='No match'
            ),
            'name': ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='No match'
            ),
            'content': ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='No match'
            )
        }
        
        result = agent.aggregate_scores(scores)
        
        assert result.confidence == 0.0
        assert result.sensitivity_type == 'non_sensitive'
    
    def test_aggregate_scores_weighted_average(self):
        """Test score aggregation using weighted average."""
        agent = DataProcessorAgent()
        
        scores = {
            'pattern': ClassificationScore(
                confidence=0.5,
                sensitivity_type='phone',
                reasoning='Partial pattern match'
            ),
            'name': ClassificationScore(
                confidence=0.6,
                sensitivity_type='phone',
                reasoning='Name suggests phone'
            ),
            'content': ClassificationScore(
                confidence=0.3,
                sensitivity_type='identifier',
                reasoning='Some uniqueness'
            )
        }
        
        result = agent.aggregate_scores(scores)
        
        # Should use weighted average
        assert result.confidence > 0.0
        assert result.sensitivity_type == 'phone'
    
    def test_aggregate_scores_pattern_matches_combined(self):
        """Test that pattern matches are combined from all classifiers."""
        agent = DataProcessorAgent()
        
        scores = {
            'pattern': ClassificationScore(
                confidence=0.8,
                sensitivity_type='email',
                reasoning='Pattern match',
                pattern_matches=['user@test.com', 'admin@test.com']
            ),
            'name': ClassificationScore(
                confidence=0.7,
                sensitivity_type='email',
                reasoning='Name match',
                pattern_matches=['contact@example.org']
            )
        }
        
        result = agent.aggregate_scores(scores)
        
        assert result.pattern_matches is not None
        assert len(result.pattern_matches) > 0
    
    def test_select_strategy_email(self):
        """Test strategy selection for email."""
        agent = DataProcessorAgent()
        
        score = ClassificationScore(
            confidence=0.9,
            sensitivity_type='email',
            reasoning='Test'
        )
        strategy = agent.select_strategy(score)
        assert strategy == 'bedrock_text'
    
    def test_select_strategy_phone(self):
        """Test strategy selection for phone."""
        agent = DataProcessorAgent()
        
        score = ClassificationScore(
            confidence=0.9,
            sensitivity_type='phone',
            reasoning='Test'
        )
        strategy = agent.select_strategy(score)
        assert strategy == 'rule_based_phone'
    
    def test_select_strategy_ssn(self):
        """Test strategy selection for SSN."""
        agent = DataProcessorAgent()
        
        score = ClassificationScore(
            confidence=0.9,
            sensitivity_type='ssn',
            reasoning='Test'
        )
        strategy = agent.select_strategy(score)
        assert strategy == 'rule_based_ssn'
    
    def test_select_strategy_name(self):
        """Test strategy selection for name."""
        agent = DataProcessorAgent()
        
        score = ClassificationScore(
            confidence=0.9,
            sensitivity_type='name',
            reasoning='Test'
        )
        strategy = agent.select_strategy(score)
        assert strategy == 'bedrock_text'
    
    def test_select_strategy_address(self):
        """Test strategy selection for address."""
        agent = DataProcessorAgent()
        
        score = ClassificationScore(
            confidence=0.9,
            sensitivity_type='address',
            reasoning='Test'
        )
        strategy = agent.select_strategy(score)
        assert strategy == 'bedrock_text'
    
    def test_select_strategy_identifier(self):
        """Test strategy selection for identifier."""
        agent = DataProcessorAgent()
        
        score = ClassificationScore(
            confidence=0.6,
            sensitivity_type='identifier',
            reasoning='Test'
        )
        strategy = agent.select_strategy(score)
        assert strategy == 'sdv_preserve_distribution'
    
    def test_select_strategy_unknown(self):
        """Test strategy selection for unknown type."""
        agent = DataProcessorAgent()
        
        score = ClassificationScore(
            confidence=0.3,
            sensitivity_type='unknown_type',
            reasoning='Test'
        )
        strategy = agent.select_strategy(score)
        assert strategy == 'sdv_preserve_distribution'
    
    def test_process_with_sample_data(self, tmp_path):
        """Test processing sample data."""
        # Create test CSV with various field types
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com', 'contact@example.org'],
            'phone': ['555-123-4567', '555-987-6543', '555-111-2222'],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'age': [25, 30, 35],
            'city': ['New York', 'Los Angeles', 'Chicago']
        })
        df.to_csv(csv_file, index=False)
        
        agent = DataProcessorAgent()
        report = agent.process(csv_file)
        
        # Verify report structure
        assert report.total_fields == 5
        assert report.sensitive_fields >= 2  # At least email and phone
        assert len(report.classifications) == 5
        
        # Verify email classification
        email_classification = report.classifications['email']
        assert email_classification.is_sensitive
        assert email_classification.sensitivity_type == 'email'
        assert email_classification.confidence > 0.7
        
        # Verify phone classification
        phone_classification = report.classifications['phone']
        assert phone_classification.is_sensitive
        assert phone_classification.sensitivity_type == 'phone'
        
        # Verify non-sensitive fields
        age_classification = report.classifications['age']
        # Age might be classified as identifier due to uniqueness, but shouldn't be highly sensitive
        assert age_classification.confidence < 0.9
    
    def test_process_generates_sensitivity_report(self, tmp_path):
        """Test that process generates a complete sensitivity report."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com'],
            'ssn': ['123-45-6789', '987-65-4321'],
            'random': ['abc', 'def']
        })
        df.to_csv(csv_file, index=False)
        
        agent = DataProcessorAgent()
        report = agent.process(csv_file)
        
        # Verify report has all required fields
        assert hasattr(report, 'classifications')
        assert hasattr(report, 'data_profile')
        assert hasattr(report, 'timestamp')
        assert hasattr(report, 'total_fields')
        assert hasattr(report, 'sensitive_fields')
        assert hasattr(report, 'confidence_distribution')
        
        # Verify timestamp is recent
        assert isinstance(report.timestamp, datetime)
        
        # Verify data profile exists for all fields
        assert len(report.data_profile) == 3
        assert 'email' in report.data_profile
        assert 'ssn' in report.data_profile
        assert 'random' in report.data_profile
    
    def test_process_identifies_multiple_pii_types(self, tmp_path):
        """Test that process correctly identifies multiple PII types."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com'],
            'phone': ['555-123-4567', '555-987-6543'],
            'ssn': ['123-45-6789', '987-65-4321'],
            'dob': ['01/15/1990', '12/25/1985'],
            'credit_card': ['1234-5678-9012-3456', '9876-5432-1098-7654']
        })
        df.to_csv(csv_file, index=False)
        
        agent = DataProcessorAgent()
        report = agent.process(csv_file)
        
        # All fields should be identified as sensitive
        assert report.sensitive_fields == 5
        
        # Verify each type is correctly identified
        assert report.classifications['email'].sensitivity_type == 'email'
        assert report.classifications['phone'].sensitivity_type == 'phone'
        assert report.classifications['ssn'].sensitivity_type == 'ssn'
        assert report.classifications['dob'].sensitivity_type == 'date_of_birth'
        assert report.classifications['credit_card'].sensitivity_type == 'credit_card'
    
    def test_confidence_distribution(self, tmp_path):
        """Test confidence distribution calculation."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com'],
            'random': ['abc', 'def']
        })
        df.to_csv(csv_file, index=False)
        
        agent = DataProcessorAgent()
        report = agent.process(csv_file)
        
        # Check confidence distribution
        assert 'high' in report.confidence_distribution
        assert 'medium' in report.confidence_distribution
        assert 'low' in report.confidence_distribution
        
        # Should have at least one high confidence (email)
        assert report.confidence_distribution['high'] >= 1
        
        # Total should equal total fields
        total = sum(report.confidence_distribution.values())
        assert total == report.total_fields
    
    def test_process_with_empty_dataframe(self, tmp_path):
        """Test processing an empty dataframe."""
        csv_file = tmp_path / "empty.csv"
        # Create a CSV with headers but no data
        df = pd.DataFrame(columns=['col1', 'col2'])
        df.to_csv(csv_file, index=False)
        
        agent = DataProcessorAgent()
        report = agent.process(csv_file)
        
        # Should have columns but no sensitive fields detected
        assert report.total_fields == 2
        assert len(report.classifications) == 2
        # All fields should have low confidence due to no data
        for classification in report.classifications.values():
            assert classification.confidence < 0.5
    
    def test_process_with_all_null_column(self, tmp_path):
        """Test processing data with all-null columns."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            'email': ['user@test.com', 'admin@test.com'],
            'all_null': [None, None]
        })
        df.to_csv(csv_file, index=False)
        
        agent = DataProcessorAgent()
        report = agent.process(csv_file)
        
        # Should still process all columns
        assert report.total_fields == 2
        
        # All-null column should have low confidence
        assert report.classifications['all_null'].confidence < 0.5
