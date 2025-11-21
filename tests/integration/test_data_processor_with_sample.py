"""Integration test for Data Processor Agent with sample data."""

import pytest
from pathlib import Path

from agents.data_processor import DataProcessorAgent


def test_process_mgw_sample_data():
    """Test processing the MGW sample data file."""
    # Path to sample data
    sample_file = Path('.kiro/specs/synthetic-data-generator/MGW_File.csv')
    
    if not sample_file.exists():
        pytest.skip('Sample data file not found')
    
    # Create agent and process
    agent = DataProcessorAgent()
    report = agent.process(sample_file)
    
    # Verify report was generated
    assert report is not None
    assert report.total_fields > 0
    
    # Print summary for verification
    print(f"\n=== Sensitivity Report Summary ===")
    print(f"Total fields: {report.total_fields}")
    print(f"Sensitive fields: {report.sensitive_fields}")
    print(f"Confidence distribution: {report.confidence_distribution}")
    
    print(f"\n=== Sensitive Fields ===")
    for field_name in report.get_sensitive_fields():
        classification = report.classifications[field_name]
        print(f"  {field_name}:")
        print(f"    Type: {classification.sensitivity_type}")
        print(f"    Confidence: {classification.confidence:.2f}")
        print(f"    Strategy: {classification.recommended_strategy}")
        print(f"    Reasoning: {classification.reasoning[:100]}...")
    
    # Verify expected sensitive fields are detected
    sensitive_fields = report.get_sensitive_fields()
    
    # Email should be detected
    assert 'Email' in sensitive_fields, "Email field should be classified as sensitive"
    
    # Phone numbers should be detected
    assert 'primary_contact_number' in sensitive_fields, "Phone field should be classified as sensitive"
    
    # Names should be detected
    assert 'first_name' in sensitive_fields or 'last_name' in sensitive_fields, "Name fields should be classified as sensitive"
    
    # Birth date should be detected
    if 'birth_dt' in report.classifications:
        birth_classification = report.classifications['birth_dt']
        # Should have some confidence even if not marked as highly sensitive
        assert birth_classification.confidence > 0.0
    
    # Verify email classification details
    email_classification = report.classifications['Email']
    assert email_classification.is_sensitive
    assert email_classification.sensitivity_type == 'email'
    assert email_classification.confidence > 0.7
    assert email_classification.recommended_strategy == 'bedrock_text'
    
    # Verify phone classification details
    phone_classification = report.classifications['primary_contact_number']
    assert phone_classification.is_sensitive
    assert phone_classification.sensitivity_type == 'phone'
    assert phone_classification.confidence > 0.7
    
    # Verify non-sensitive fields
    non_sensitive = report.get_non_sensitive_fields()
    assert len(non_sensitive) > 0
    
    # Fields like 'batch' should not be sensitive
    if 'batch' in report.classifications:
        batch_classification = report.classifications['batch']
        # Batch might have low confidence but shouldn't be highly sensitive
        assert batch_classification.confidence < 0.8 or not batch_classification.is_sensitive


if __name__ == '__main__':
    test_process_mgw_sample_data()
