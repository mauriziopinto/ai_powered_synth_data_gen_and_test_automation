"""Property-based tests for sensitive field classification.

This module tests that the Data Processor Agent correctly identifies
fields containing PII patterns as sensitive with high confidence.
"""

import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest
from pathlib import Path
import tempfile

from agents.data_processor.agent import DataProcessorAgent


# Custom strategies for generating test data with PII patterns
@composite
def email_strategy(draw):
    """Generate valid email addresses."""
    username = draw(st.text(
        min_size=3, 
        max_size=20,
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='._-')
    ))
    domain = draw(st.text(
        min_size=3,
        max_size=15,
        alphabet=st.characters(whitelist_categories=('Ll',))
    ))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'gov', 'co.uk', 'io']))
    return f"{username}@{domain}.{tld}"


@composite
def phone_strategy(draw):
    """Generate valid phone numbers in various formats."""
    format_type = draw(st.sampled_from(['us_dashes', 'us_dots', 'us_plain', 'international']))
    
    if format_type == 'us_dashes':
        area = draw(st.integers(min_value=200, max_value=999))
        prefix = draw(st.integers(min_value=200, max_value=999))
        line = draw(st.integers(min_value=1000, max_value=9999))
        return f"{area}-{prefix}-{line}"
    elif format_type == 'us_dots':
        area = draw(st.integers(min_value=200, max_value=999))
        prefix = draw(st.integers(min_value=200, max_value=999))
        line = draw(st.integers(min_value=1000, max_value=9999))
        return f"{area}.{prefix}.{line}"
    elif format_type == 'us_plain':
        area = draw(st.integers(min_value=200, max_value=999))
        prefix = draw(st.integers(min_value=200, max_value=999))
        line = draw(st.integers(min_value=1000, max_value=9999))
        return f"{area}{prefix}{line}"
    else:  # international
        country = draw(st.integers(min_value=1, max_value=999))
        area = draw(st.integers(min_value=100, max_value=9999))
        number = draw(st.integers(min_value=100000, max_value=9999999))
        return f"+{country}-{area}-{number}"


@composite
def ssn_strategy(draw):
    """Generate valid SSN patterns."""
    format_type = draw(st.sampled_from(['dashed', 'plain']))
    
    area = draw(st.integers(min_value=100, max_value=899))  # Avoid 000, 666, 900+
    group = draw(st.integers(min_value=10, max_value=99))
    serial = draw(st.integers(min_value=1000, max_value=9999))
    
    if format_type == 'dashed':
        return f"{area}-{group}-{serial}"
    else:
        return f"{area}{group}{serial}"


@composite
def credit_card_strategy(draw):
    """Generate valid credit card patterns."""
    # Generate 4 groups of 4 digits
    groups = [draw(st.integers(min_value=1000, max_value=9999)) for _ in range(4)]
    
    separator = draw(st.sampled_from(['-', ' ', '']))
    return separator.join(str(g) for g in groups)


@composite
def postal_code_strategy(draw):
    """Generate valid postal code patterns."""
    format_type = draw(st.sampled_from(['us_5', 'us_9', 'uk']))
    
    if format_type == 'us_5':
        return str(draw(st.integers(min_value=10000, max_value=99999)))
    elif format_type == 'us_9':
        zip5 = draw(st.integers(min_value=10000, max_value=99999))
        plus4 = draw(st.integers(min_value=1000, max_value=9999))
        return f"{zip5}-{plus4}"
    else:  # UK postcode
        area = draw(st.text(min_size=1, max_size=2, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        district = draw(st.integers(min_value=1, max_value=99))
        sector = draw(st.integers(min_value=0, max_value=9))
        unit = draw(st.text(min_size=2, max_size=2, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        return f"{area}{district} {sector}{unit}"


@composite
def ip_address_strategy(draw):
    """Generate valid IP addresses."""
    octets = [draw(st.integers(min_value=0, max_value=255)) for _ in range(4)]
    return '.'.join(str(o) for o in octets)


@composite
def date_of_birth_strategy(draw):
    """Generate date of birth patterns."""
    format_type = draw(st.sampled_from(['mdy_slash', 'mdy_dash', 'ymd_dash']))
    
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    year = draw(st.integers(min_value=1940, max_value=2010))
    
    if format_type == 'mdy_slash':
        return f"{month}/{day}/{year}"
    elif format_type == 'mdy_dash':
        return f"{month}-{day}-{year}"
    else:  # ymd_dash
        return f"{year}-{month:02d}-{day:02d}"


@composite
def pii_dataframe_strategy(draw):
    """Generate a DataFrame with PII fields that should be detected."""
    num_rows = draw(st.integers(min_value=10, max_value=100))
    
    # Choose which PII types to include
    include_email = draw(st.booleans())
    include_phone = draw(st.booleans())
    include_ssn = draw(st.booleans())
    include_credit_card = draw(st.booleans())
    include_postal = draw(st.booleans())
    include_ip = draw(st.booleans())
    include_dob = draw(st.booleans())
    
    # Ensure at least one PII field
    assume(any([include_email, include_phone, include_ssn, include_credit_card, 
                include_postal, include_ip, include_dob]))
    
    data = {}
    expected_sensitive = []
    
    if include_email:
        data['email_address'] = [draw(email_strategy()) for _ in range(num_rows)]
        expected_sensitive.append('email_address')
    
    if include_phone:
        data['phone_number'] = [draw(phone_strategy()) for _ in range(num_rows)]
        expected_sensitive.append('phone_number')
    
    if include_ssn:
        data['social_security'] = [draw(ssn_strategy()) for _ in range(num_rows)]
        expected_sensitive.append('social_security')
    
    if include_credit_card:
        data['credit_card_num'] = [draw(credit_card_strategy()) for _ in range(num_rows)]
        expected_sensitive.append('credit_card_num')
    
    if include_postal:
        data['zip_code'] = [draw(postal_code_strategy()) for _ in range(num_rows)]
        expected_sensitive.append('zip_code')
    
    if include_ip:
        data['ip_addr'] = [draw(ip_address_strategy()) for _ in range(num_rows)]
        expected_sensitive.append('ip_addr')
    
    if include_dob:
        data['birth_date'] = [draw(date_of_birth_strategy()) for _ in range(num_rows)]
        expected_sensitive.append('birth_date')
    
    # Add some non-sensitive fields
    data['id'] = list(range(1, num_rows + 1))
    data['amount'] = [draw(st.floats(min_value=0, max_value=10000)) for _ in range(num_rows)]
    
    df = pd.DataFrame(data)
    return df, expected_sensitive


@settings(max_examples=100, deadline=None)
@given(data=pii_dataframe_strategy())
def test_pii_fields_classified_as_sensitive(data):
    """
    Feature: synthetic-data-generator, Property 10: Sensitive Field Classification
    Validates: Requirements 14.2
    
    For any production dataset, all fields containing PII patterns (emails, phones, SSNs, etc.)
    should be classified as sensitive with confidence > 0.7.
    """
    df, expected_sensitive_fields = data
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = Path(f.name)
    
    try:
        # Process the data
        agent = DataProcessorAgent()
        report = agent.process(temp_path)
        
        # Verify all expected PII fields are classified as sensitive
        for field_name in expected_sensitive_fields:
            classification = report.classifications[field_name]
            
            # Assert field is marked as sensitive
            assert classification.is_sensitive, \
                f"Field '{field_name}' should be classified as sensitive but was not. " \
                f"Confidence: {classification.confidence}, Type: {classification.sensitivity_type}, " \
                f"Reasoning: {classification.reasoning}"
            
            # Assert confidence is above threshold
            assert classification.confidence > 0.7, \
                f"Field '{field_name}' has confidence {classification.confidence} which is <= 0.7. " \
                f"Type: {classification.sensitivity_type}, Reasoning: {classification.reasoning}"
            
            # Assert sensitivity type is not 'unknown' or 'non_sensitive'
            assert classification.sensitivity_type not in ['unknown', 'non_sensitive'], \
                f"Field '{field_name}' has invalid sensitivity type: {classification.sensitivity_type}"
        
        # Verify non-PII fields are not classified as sensitive (or have low confidence)
        non_pii_fields = [col for col in df.columns if col not in expected_sensitive_fields]
        for field_name in non_pii_fields:
            classification = report.classifications[field_name]
            
            # Non-PII fields should either be non-sensitive or have low confidence
            if classification.is_sensitive:
                # If marked sensitive, confidence should be low or it's a false positive
                # We allow some false positives but they should have lower confidence
                assert classification.confidence <= 0.85, \
                    f"Non-PII field '{field_name}' incorrectly classified as sensitive with high confidence " \
                    f"{classification.confidence}. Type: {classification.sensitivity_type}"
    
    finally:
        # Clean up temp file
        temp_path.unlink()


@settings(max_examples=100, deadline=None)
@given(
    num_rows=st.integers(min_value=20, max_value=100),
    pii_percentage=st.floats(min_value=0.5, max_value=1.0)
)
def test_mixed_pii_detection(num_rows, pii_percentage):
    """
    Feature: synthetic-data-generator, Property 10: Sensitive Field Classification
    Validates: Requirements 14.2
    
    For datasets with mixed PII and non-PII values in a field, classification should
    be based on the percentage of PII values detected.
    """
    # Generate email field with mixed PII and non-PII
    num_pii = int(num_rows * pii_percentage)
    num_non_pii = num_rows - num_pii
    
    # Generate PII emails
    pii_emails = [f"user{i}@example.com" for i in range(num_pii)]
    
    # Generate non-PII values (random strings that don't look like emails)
    non_pii_values = [f"value_{i}" for i in range(num_non_pii)]
    
    # Combine and shuffle
    all_values = pii_emails + non_pii_values
    import random
    random.shuffle(all_values)
    
    df = pd.DataFrame({
        'mixed_field': all_values,
        'id': list(range(num_rows))
    })
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = Path(f.name)
    
    try:
        # Process the data
        agent = DataProcessorAgent()
        report = agent.process(temp_path)
        
        classification = report.classifications['mixed_field']
        
        # If strong majority are PII (>=75%), should be classified as sensitive
        if pii_percentage >= 0.75:
            assert classification.is_sensitive, \
                f"Field with {pii_percentage:.0%} PII should be sensitive. " \
                f"Confidence: {classification.confidence}"
            
            # Confidence should correlate with PII percentage
            # Higher PII percentage should give higher confidence
            if pii_percentage > 0.8:
                assert classification.confidence > 0.7, \
                    f"Field with {pii_percentage:.0%} PII should have confidence > 0.7, " \
                    f"got {classification.confidence}"
        
        # If moderate majority (60-70%), should have reasonable confidence
        elif pii_percentage >= 0.6:
            # Should at least be detected as the right type
            assert classification.sensitivity_type == 'email', \
                f"Field with {pii_percentage:.0%} email patterns should be typed as email, " \
                f"got {classification.sensitivity_type}"
    
    finally:
        # Clean up temp file
        temp_path.unlink()


@settings(max_examples=50, deadline=None)
@given(
    num_rows=st.integers(min_value=10, max_value=50),
    field_name=st.sampled_from([
        'email', 'email_address', 'user_email', 'contact_email',
        'phone', 'phone_number', 'telephone', 'mobile',
        'ssn', 'social_security_number', 'tax_id',
        'first_name', 'last_name', 'full_name'
    ])
)
def test_name_based_classification(num_rows, field_name):
    """
    Feature: synthetic-data-generator, Property 10: Sensitive Field Classification
    Validates: Requirements 14.2
    
    Fields with PII-indicating names should be classified as sensitive even with
    generic content, as the name itself suggests sensitive data.
    """
    # Generate generic string data (not actual PII patterns)
    df = pd.DataFrame({
        field_name: [f"value_{i}" for i in range(num_rows)],
        'id': list(range(num_rows))
    })
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = Path(f.name)
    
    try:
        # Process the data
        agent = DataProcessorAgent()
        report = agent.process(temp_path)
        
        classification = report.classifications[field_name]
        
        # Field should be classified as sensitive based on name
        # Even without pattern matches, name-based classifier should trigger
        assert classification.is_sensitive or classification.confidence > 0.5, \
            f"Field '{field_name}' should be flagged as potentially sensitive based on name. " \
            f"Confidence: {classification.confidence}, Type: {classification.sensitivity_type}"
    
    finally:
        # Clean up temp file
        temp_path.unlink()


@settings(max_examples=100, deadline=None)
@given(data=pii_dataframe_strategy())
def test_classification_reasoning_provided(data):
    """
    Feature: synthetic-data-generator, Property 10: Sensitive Field Classification
    Validates: Requirements 14.2
    
    For any classified field, the system should provide reasoning explaining
    why it was classified as sensitive or non-sensitive.
    """
    df, expected_sensitive_fields = data
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = Path(f.name)
    
    try:
        # Process the data
        agent = DataProcessorAgent()
        report = agent.process(temp_path)
        
        # Verify all classifications have reasoning
        for field_name, classification in report.classifications.items():
            # Reasoning should not be empty
            assert classification.reasoning, \
                f"Field '{field_name}' has no reasoning provided"
            
            # Reasoning should be a non-empty string
            assert isinstance(classification.reasoning, str), \
                f"Field '{field_name}' reasoning is not a string"
            
            assert len(classification.reasoning) > 10, \
                f"Field '{field_name}' reasoning is too short: '{classification.reasoning}'"
            
            # If sensitive, reasoning should mention why
            if classification.is_sensitive:
                reasoning_lower = classification.reasoning.lower()
                # Should mention pattern, name, or content analysis
                assert any(keyword in reasoning_lower for keyword in 
                          ['pattern', 'name', 'content', 'detected', 'match', 'indicates']), \
                    f"Sensitive field '{field_name}' reasoning doesn't explain detection: " \
                    f"'{classification.reasoning}'"
    
    finally:
        # Clean up temp file
        temp_path.unlink()
