"""Unit tests for the plain-language explanation generator."""

import pytest
from datetime import datetime

from shared.utils.explanation_generator import (
    get_explanation_generator,
    Explanation,
    ExplanationTemplate,
    DataProcessorExplanations,
    SyntheticDataExplanations
)


class TestExplanation:
    """Test the Explanation dataclass."""
    
    def test_explanation_creation(self):
        """Test creating an explanation."""
        exp = Explanation(
            agent_name="Test Agent",
            action="test_action",
            plain_language="This is a test",
            reasoning="Testing the system"
        )
        
        assert exp.agent_name == "Test Agent"
        assert exp.action == "test_action"
        assert exp.plain_language == "This is a test"
        assert exp.reasoning == "Testing the system"
        assert exp.timestamp is not None
        assert isinstance(exp.timestamp, datetime)
    
    def test_explanation_with_states(self):
        """Test explanation with before/after states."""
        before = {'field': 'value1'}
        after = {'field': 'value2'}
        highlights = ['field']
        
        exp = Explanation(
            agent_name="Test Agent",
            action="transform",
            plain_language="Transformed data",
            reasoning="For testing",
            before_state=before,
            after_state=after,
            highlights=highlights
        )
        
        assert exp.before_state == before
        assert exp.after_state == after
        assert exp.highlights == highlights


class TestDataProcessorExplanations:
    """Test Data Processor Agent explanations."""
    
    def test_start_analysis_explanation(self):
        """Test start analysis explanation."""
        template = DataProcessorExplanations()
        exp = template.generate('start_analysis', {
            'num_columns': 50,
            'num_rows': 10000
        })
        
        assert exp.agent_name == "Data Processor Agent"
        assert exp.action == "start_analysis"
        assert "50 columns" in exp.plain_language
        assert "10000 rows" in exp.plain_language
        assert "GDPR" in exp.reasoning
    
    def test_field_classification_explanation(self):
        """Test field classification explanation."""
        template = DataProcessorExplanations()
        exp = template.generate('field_classification', {
            'field_name': 'customer_email'
        })
        
        assert "customer_email" in exp.plain_language
        assert "sensitive personal information" in exp.plain_language
        assert "pattern matching" in exp.reasoning
    
    def test_pattern_detected_explanation(self):
        """Test pattern detected explanation."""
        template = DataProcessorExplanations()
        exp = template.generate('pattern_detected', {
            'pii_type': 'email',
            'field_name': 'customer_email',
            'confidence': 95,
            'match_count': 9500,
            'sample_size': 10000,
            'examples': 'user@example.com, test@test.org'
        })
        
        assert "email" in exp.plain_language
        assert "95%" in exp.plain_language
        assert "9500" in exp.reasoning
        assert "10000" in exp.reasoning


class TestSyntheticDataExplanations:
    """Test Synthetic Data Agent explanations."""
    
    def test_start_generation_explanation(self):
        """Test start generation explanation."""
        template = SyntheticDataExplanations()
        exp = template.generate('start_generation', {
            'num_records': 10000,
            'sdv_model': 'GaussianCopula'
        })
        
        assert "10000 records" in exp.plain_language
        assert "GaussianCopula" in exp.plain_language
        assert "artificial data" in exp.reasoning
    
    def test_bedrock_text_generation_explanation(self):
        """Test Bedrock text generation explanation."""
        template = SyntheticDataExplanations()
        exp = template.generate('bedrock_text_generation', {
            'field_type': 'email',
            'field_name': 'customer_email'
        })
        
        assert "email" in exp.plain_language
        assert "customer_email" in exp.plain_language
        assert "Bedrock" in exp.plain_language
        assert "AI" in exp.reasoning
    
    def test_quality_score_explanation(self):
        """Test quality score explanation."""
        template = SyntheticDataExplanations()
        exp = template.generate('quality_score', {
            'score': 87,
            'interpretation': 'Good quality',
            'col_shapes': 0.92,
            'col_trends': 0.85
        })
        
        assert "87/100" in exp.plain_language
        assert "Good quality" in exp.plain_language
        assert "0.92" in exp.reasoning
        assert "0.85" in exp.reasoning


class TestExplanationGenerator:
    """Test the main ExplanationGenerator class."""
    
    def test_singleton_pattern(self):
        """Test that get_explanation_generator returns the same instance."""
        gen1 = get_explanation_generator()
        gen2 = get_explanation_generator()
        
        assert gen1 is gen2
    
    def test_generate_for_data_processor(self):
        """Test generating explanation for data processor."""
        generator = get_explanation_generator()
        exp = generator.generate('data_processor', 'start_analysis', {
            'num_columns': 50,
            'num_rows': 10000
        })
        
        assert exp.agent_name == "Data Processor Agent"
        assert "50 columns" in exp.plain_language
    
    def test_generate_for_synthetic_data(self):
        """Test generating explanation for synthetic data agent."""
        generator = get_explanation_generator()
        exp = generator.generate('synthetic_data', 'start_generation', {
            'num_records': 10000,
            'sdv_model': 'GaussianCopula'
        })
        
        assert exp.agent_name == "Synthetic Data Agent"
        assert "10000 records" in exp.plain_language
    
    def test_generate_for_unknown_agent(self):
        """Test generating explanation for unknown agent."""
        generator = get_explanation_generator()
        exp = generator.generate('unknown_agent', 'unknown_action', {})
        
        assert exp.agent_name == "unknown_agent"
        assert exp.action == "unknown_action"
        assert "No detailed explanation" in exp.reasoning
    
    def test_generate_progress_message(self):
        """Test generating progress message."""
        generator = get_explanation_generator()
        msg = generator.generate_progress_message(
            'data_processor',
            0.50,
            'field_classification',
            {'field_name': 'customer_email'}
        )
        
        assert "[50%]" in msg
        assert "customer_email" in msg
    
    def test_generate_comparison(self):
        """Test generating before/after comparison."""
        generator = get_explanation_generator()
        
        before = {
            'email': 'john@example.com',
            'phone': '555-1234',
            'balance': 100.0
        }
        
        after = {
            'email': 'synthetic@test.com',
            'phone': '555-5678',
            'balance': 100.0
        }
        
        comparison = generator.generate_comparison(before, after)
        
        assert comparison['before'] == before
        assert comparison['after'] == after
        assert 'email' in comparison['highlights']
        assert 'phone' in comparison['highlights']
        assert 'balance' not in comparison['highlights']  # Unchanged
        
        # Check changes
        assert len(comparison['changes']) == 2  # email and phone changed
        email_change = next(c for c in comparison['changes'] if c['field'] == 'email')
        assert email_change['change_type'] == 'modified'
        assert email_change['before_value'] == 'john@example.com'
        assert email_change['after_value'] == 'synthetic@test.com'
    
    def test_generate_comparison_with_explicit_highlights(self):
        """Test generating comparison with explicit highlights."""
        generator = get_explanation_generator()
        
        before = {'a': 1, 'b': 2, 'c': 3}
        after = {'a': 10, 'b': 2, 'c': 30}
        
        comparison = generator.generate_comparison(before, after, highlights=['a'])
        
        assert comparison['highlights'] == ['a']
        assert len(comparison['changes']) == 1
        assert comparison['changes'][0]['field'] == 'a'
    
    def test_classify_change_types(self):
        """Test change type classification."""
        generator = get_explanation_generator()
        
        assert generator._classify_change(None, 'value') == 'added'
        assert generator._classify_change('value', None) == 'removed'
        assert generator._classify_change('old', 'new') == 'modified'
        assert generator._classify_change('same', 'same') == 'unchanged'
    
    def test_format_decision_reasoning(self):
        """Test formatting decision reasoning."""
        generator = get_explanation_generator()
        
        reasoning = generator.format_decision_reasoning(
            decision="Classify as sensitive",
            factors=[
                {'classifier': 'Pattern', 'confidence': 0.95, 'reasoning': 'Found pattern'},
                {'classifier': 'Name', 'confidence': 0.85, 'reasoning': 'Name matches'}
            ],
            conclusion="High confidence classification"
        )
        
        assert reasoning['decision'] == "Classify as sensitive"
        assert len(reasoning['factors']) == 2
        assert reasoning['factors'][0]['classifier'] == 'Pattern'
        assert reasoning['factors'][0]['confidence'] == 0.95
        assert reasoning['conclusion'] == "High confidence classification"
        assert 'timestamp' in reasoning


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
