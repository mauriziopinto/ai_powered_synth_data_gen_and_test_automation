"""Unit tests for Bedrock client wrapper."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from shared.utils.bedrock_client import (
    BedrockClient,
    BedrockConfig,
    RuleBasedTextGenerator
)


class TestBedrockConfig:
    """Tests for BedrockConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BedrockConfig()
        
        assert config.model_id == 'anthropic.claude-3-haiku-20240307-v1:0'
        assert config.temperature == 0.9
        assert config.max_tokens == 2000
        assert config.batch_size == 100
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = BedrockConfig(
            model_id='custom-model',
            temperature=0.5,
            batch_size=50
        )
        
        assert config.model_id == 'custom-model'
        assert config.temperature == 0.5
        assert config.batch_size == 50


class TestBedrockClient:
    """Tests for BedrockClient."""
    
    def test_initialization(self):
        """Test client initialization."""
        mock_client = Mock()
        config = BedrockConfig(batch_size=50)
        
        bedrock_client = BedrockClient(mock_client, config)
        
        assert bedrock_client.client == mock_client
        assert bedrock_client.config.batch_size == 50
    
    def test_invoke_success(self):
        """Test successful Bedrock invocation."""
        mock_client = Mock()
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Generated text'}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response
        
        bedrock_client = BedrockClient(mock_client)
        result = bedrock_client.invoke("Test prompt")
        
        assert result == 'Generated text'
        mock_client.invoke_model.assert_called_once()
    
    def test_invoke_with_retry(self):
        """Test invocation with retry on failure."""
        mock_client = Mock()
        
        # First call fails, second succeeds
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Success'}]
        }).encode()
        
        mock_client.invoke_model.side_effect = [
            Exception("Temporary failure"),
            mock_response
        ]
        
        bedrock_client = BedrockClient(mock_client)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = bedrock_client.invoke("Test prompt")
        
        assert result == 'Success'
        assert mock_client.invoke_model.call_count == 2
    
    def test_invoke_max_retries_exceeded(self):
        """Test that max retries are respected."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("Persistent failure")
        
        config = BedrockConfig(max_retries=2)
        bedrock_client = BedrockClient(mock_client, config)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(Exception, match="Persistent failure"):
                bedrock_client.invoke("Test prompt")
        
        # Should try initial + 2 retries = 3 total
        assert mock_client.invoke_model.call_count == 3
    
    def test_build_prompt_basic(self):
        """Test basic prompt building."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email',
            num_values=10
        )
        
        assert 'email' in prompt
        assert '10' in prompt
        assert 'JSON array' in prompt
    
    def test_build_prompt_with_context(self):
        """Test prompt building with context."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        context = {
            'first_name': ['John', 'Jane'],
            'company': ['Acme Corp']
        }
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email',
            num_values=10,
            context=context
        )
        
        assert 'Context from related fields' in prompt
        assert 'first_name' in prompt
        assert 'company' in prompt
    
    def test_build_prompt_with_constraints(self):
        """Test prompt building with constraints."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        constraints = {
            'pattern': r'^\d{3}-\d{3}-\d{4}$',
            'format': 'US phone number'
        }
        
        prompt = bedrock_client._build_prompt(
            field_name='phone',
            field_type='phone',
            num_values=10,
            constraints=constraints
        )
        
        assert 'Constraints' in prompt
        assert 'pattern' in prompt
        assert 'format' in prompt
    
    def test_parse_response_valid_json(self):
        """Test parsing valid JSON response."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        response = '["value1", "value2", "value3"]'
        values = bedrock_client._parse_response(response, 3)
        
        assert values == ["value1", "value2", "value3"]
    
    def test_parse_response_with_extra_text(self):
        """Test parsing JSON with extra text."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        response = 'Here are the values: ["value1", "value2"] as requested.'
        values = bedrock_client._parse_response(response, 2)
        
        assert values == ["value1", "value2"]
    
    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        response = 'This is not JSON'
        
        with pytest.raises(ValueError, match="Invalid JSON response"):
            bedrock_client._parse_response(response, 2)
    
    def test_generate_text_field_with_fallback(self):
        """Test text field generation with fallback on failure."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("API failure")
        
        bedrock_client = BedrockClient(mock_client)
        
        # Create a simple fallback generator
        def fallback_gen(field_name, field_type, num_values):
            return [f"fallback_{i}" for i in range(num_values)]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            values = bedrock_client.generate_text_field(
                field_name='test_field',
                field_type='name',
                num_values=5,
                fallback_generator=fallback_gen
            )
        
        assert len(values) == 5
        assert all(v.startswith('fallback_') for v in values)
    
    def test_generate_text_field_without_fallback_raises(self):
        """Test that generation without fallback raises on failure."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("API failure")
        
        bedrock_client = BedrockClient(mock_client)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(Exception, match="API failure"):
                bedrock_client.generate_text_field(
                    field_name='test_field',
                    field_type='name',
                    num_values=5,
                    fallback_generator=None
                )


class TestPromptConstruction:
    """Comprehensive tests for prompt construction."""
    
    def test_prompt_includes_field_name(self):
        """Test that prompt includes the field name."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        prompt = bedrock_client._build_prompt(
            field_name='customer_email',
            field_type='email',
            num_values=5
        )
        
        assert 'customer_email' in prompt
    
    def test_prompt_includes_field_type(self):
        """Test that prompt includes the field type."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email_address',
            num_values=5
        )
        
        assert 'email_address' in prompt
    
    def test_prompt_includes_count(self):
        """Test that prompt includes the requested count."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email',
            num_values=42
        )
        
        assert '42' in prompt
    
    def test_prompt_includes_json_format_instruction(self):
        """Test that prompt includes JSON format instruction."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email',
            num_values=5
        )
        
        assert 'JSON array' in prompt
        assert 'no additional text' in prompt.lower() or 'only' in prompt.lower()
    
    def test_prompt_with_multiple_context_fields(self):
        """Test prompt construction with multiple context fields."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        context = {
            'first_name': ['Alice', 'Bob', 'Charlie'],
            'last_name': ['Smith', 'Jones', 'Brown'],
            'company': ['TechCorp', 'DataInc']
        }
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email',
            num_values=10,
            context=context
        )
        
        assert 'Context from related fields' in prompt
        assert 'first_name' in prompt
        assert 'last_name' in prompt
        assert 'company' in prompt
        assert 'Alice' in prompt or 'Bob' in prompt
    
    def test_prompt_with_empty_context_list(self):
        """Test prompt handles empty context lists gracefully."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        context = {
            'empty_field': [],
            'valid_field': ['value1', 'value2']
        }
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email',
            num_values=5,
            context=context
        )
        
        # Should include valid_field but handle empty_field gracefully
        assert 'valid_field' in prompt
    
    def test_prompt_with_none_context_values(self):
        """Test prompt handles None context values gracefully."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        context = {
            'none_field': None,
            'valid_field': 'value'
        }
        
        prompt = bedrock_client._build_prompt(
            field_name='email',
            field_type='email',
            num_values=5,
            context=context
        )
        
        # Should include valid_field
        assert 'valid_field' in prompt
    
    def test_prompt_with_multiple_constraints(self):
        """Test prompt construction with multiple constraints."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        constraints = {
            'pattern': r'^\d{3}-\d{3}-\d{4}$',
            'format': 'US phone number',
            'example': '555-123-4567'
        }
        
        prompt = bedrock_client._build_prompt(
            field_name='phone',
            field_type='phone',
            num_values=10,
            constraints=constraints
        )
        
        assert 'Constraints' in prompt
        assert 'pattern' in prompt
        assert 'format' in prompt
        assert 'example' in prompt
    
    def test_prompt_with_context_and_constraints(self):
        """Test prompt construction with both context and constraints."""
        mock_client = Mock()
        bedrock_client = BedrockClient(mock_client)
        
        context = {'country': ['USA', 'Canada']}
        constraints = {'format': 'North American format'}
        
        prompt = bedrock_client._build_prompt(
            field_name='phone',
            field_type='phone',
            num_values=10,
            context=context,
            constraints=constraints
        )
        
        assert 'Context from related fields' in prompt
        assert 'country' in prompt
        assert 'Constraints' in prompt
        assert 'format' in prompt


class TestBatchingLogic:
    """Comprehensive tests for batching logic."""
    
    def test_single_batch_generation(self):
        """Test generation within single batch size."""
        mock_client = Mock()
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': '["val1", "val2", "val3", "val4", "val5"]'}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response
        
        config = BedrockConfig(batch_size=100)
        bedrock_client = BedrockClient(mock_client, config)
        
        values = bedrock_client.generate_text_field(
            field_name='email',
            field_type='email',
            num_values=5
        )
        
        assert len(values) == 5
        # Should only call once for small batch
        assert mock_client.invoke_model.call_count == 1
    
    def test_multiple_batch_generation(self):
        """Test generation across multiple batches."""
        mock_client = Mock()
        
        # Create responses for multiple batches
        def create_response(batch_num):
            values = [f"value_{batch_num}_{i}" for i in range(10)]
            response = {
                'body': MagicMock()
            }
            response['body'].read.return_value = json.dumps({
                'content': [{'text': json.dumps(values)}]
            }).encode()
            return response
        
        mock_client.invoke_model.side_effect = [
            create_response(1),
            create_response(2),
            create_response(3)
        ]
        
        config = BedrockConfig(batch_size=10)
        bedrock_client = BedrockClient(mock_client, config)
        
        values = bedrock_client.generate_text_field(
            field_name='email',
            field_type='email',
            num_values=25
        )
        
        assert len(values) == 25
        # Should call 3 times: 10 + 10 + 5
        assert mock_client.invoke_model.call_count == 3
    
    def test_exact_batch_size_boundary(self):
        """Test generation at exact batch size boundary."""
        mock_client = Mock()
        
        def create_response():
            values = [f"value_{i}" for i in range(50)]
            response = {
                'body': MagicMock()
            }
            response['body'].read.return_value = json.dumps({
                'content': [{'text': json.dumps(values)}]
            }).encode()
            return response
        
        mock_client.invoke_model.side_effect = [
            create_response(),
            create_response()
        ]
        
        config = BedrockConfig(batch_size=50)
        bedrock_client = BedrockClient(mock_client, config)
        
        values = bedrock_client.generate_text_field(
            field_name='email',
            field_type='email',
            num_values=100
        )
        
        assert len(values) == 100
        # Should call exactly 2 times
        assert mock_client.invoke_model.call_count == 2
    
    def test_batch_with_partial_last_batch(self):
        """Test batching with partial last batch."""
        mock_client = Mock()
        
        def create_response(count):
            values = [f"value_{i}" for i in range(count)]
            response = {
                'body': MagicMock()
            }
            response['body'].read.return_value = json.dumps({
                'content': [{'text': json.dumps(values)}]
            }).encode()
            return response
        
        mock_client.invoke_model.side_effect = [
            create_response(20),
            create_response(20),
            create_response(7)  # Partial last batch
        ]
        
        config = BedrockConfig(batch_size=20)
        bedrock_client = BedrockClient(mock_client, config)
        
        values = bedrock_client.generate_text_field(
            field_name='email',
            field_type='email',
            num_values=47
        )
        
        assert len(values) == 47
        assert mock_client.invoke_model.call_count == 3
    
    def test_batch_failure_with_fallback(self):
        """Test that batch failure triggers fallback for remaining values."""
        mock_client = Mock()
        
        # First batch succeeds, second fails
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': '["val1", "val2", "val3", "val4", "val5"]'}]
        }).encode()
        
        mock_client.invoke_model.side_effect = [
            success_response,
            Exception("Batch 2 failed")
        ]
        
        config = BedrockConfig(batch_size=5)
        bedrock_client = BedrockClient(mock_client, config)
        
        def fallback_gen(field_name, field_type, num_values):
            return [f"fallback_{i}" for i in range(num_values)]
        
        with patch('time.sleep'):
            values = bedrock_client.generate_text_field(
                field_name='email',
                field_type='email',
                num_values=10,
                fallback_generator=fallback_gen
            )
        
        assert len(values) == 10
        # First 5 should be from Bedrock, next 5 from fallback
        assert values[0] == "val1"
        assert values[5].startswith("fallback_")


class TestRetryMechanism:
    """Comprehensive tests for retry mechanism."""
    
    def test_retry_with_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        mock_client = Mock()
        
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Success'}]
        }).encode()
        
        # Fail twice, then succeed
        mock_client.invoke_model.side_effect = [
            Exception("Failure 1"),
            Exception("Failure 2"),
            success_response
        ]
        
        config = BedrockConfig(
            max_retries=3,
            initial_retry_delay=1.0,
            max_retry_delay=16.0
        )
        bedrock_client = BedrockClient(mock_client, config)
        
        with patch('time.sleep') as mock_sleep:
            result = bedrock_client.invoke("Test prompt")
        
        assert result == 'Success'
        assert mock_client.invoke_model.call_count == 3
        
        # Check that sleep was called with increasing delays
        assert mock_sleep.call_count == 2
        # First retry delay should be around 1.0 (with jitter)
        first_delay = mock_sleep.call_args_list[0][0][0]
        assert 0.5 <= first_delay <= 1.5
        
        # Second retry delay should be around 2.0 (with jitter)
        second_delay = mock_sleep.call_args_list[1][0][0]
        assert 1.0 <= second_delay <= 3.0
    
    def test_retry_respects_max_delay(self):
        """Test that retry delay respects max_retry_delay."""
        mock_client = Mock()
        
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Success'}]
        }).encode()
        
        # Fail multiple times to test max delay
        mock_client.invoke_model.side_effect = [
            Exception("Failure 1"),
            Exception("Failure 2"),
            Exception("Failure 3"),
            success_response
        ]
        
        config = BedrockConfig(
            max_retries=4,
            initial_retry_delay=2.0,
            max_retry_delay=5.0  # Cap at 5 seconds
        )
        bedrock_client = BedrockClient(mock_client, config)
        
        with patch('time.sleep') as mock_sleep:
            result = bedrock_client.invoke("Test prompt")
        
        assert result == 'Success'
        
        # Check that no delay exceeds max_retry_delay
        for call in mock_sleep.call_args_list:
            delay = call[0][0]
            assert delay <= 5.0 * 1.5  # Account for jitter
    
    def test_retry_with_jitter(self):
        """Test that retry adds jitter to prevent thundering herd."""
        mock_client = Mock()
        
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Success'}]
        }).encode()
        
        mock_client.invoke_model.side_effect = [
            Exception("Failure"),
            success_response
        ]
        
        config = BedrockConfig(
            max_retries=2,
            initial_retry_delay=2.0
        )
        bedrock_client = BedrockClient(mock_client, config)
        
        with patch('time.sleep') as mock_sleep:
            with patch('random.random', return_value=0.75):  # Mock jitter
                result = bedrock_client.invoke("Test prompt")
        
        assert result == 'Success'
        
        # Delay should be: 2.0 * (0.5 + 0.75 * 0.5) = 2.0 * 0.875 = 1.75
        delay = mock_sleep.call_args[0][0]
        assert abs(delay - 1.75) < 0.01
    
    def test_retry_exhaustion_raises_last_exception(self):
        """Test that exhausting retries raises the last exception."""
        mock_client = Mock()
        
        exceptions = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3 - final")
        ]
        mock_client.invoke_model.side_effect = exceptions
        
        config = BedrockConfig(max_retries=2)
        bedrock_client = BedrockClient(mock_client, config)
        
        with patch('time.sleep'):
            with pytest.raises(Exception, match="Error 3 - final"):
                bedrock_client.invoke("Test prompt")
    
    def test_no_retry_on_first_success(self):
        """Test that no retry occurs when first attempt succeeds."""
        mock_client = Mock()
        
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Success'}]
        }).encode()
        
        mock_client.invoke_model.return_value = success_response
        
        config = BedrockConfig(max_retries=3)
        bedrock_client = BedrockClient(mock_client, config)
        
        with patch('time.sleep') as mock_sleep:
            result = bedrock_client.invoke("Test prompt")
        
        assert result == 'Success'
        assert mock_client.invoke_model.call_count == 1
        assert mock_sleep.call_count == 0  # No sleep on success
    
    def test_retry_with_different_exception_types(self):
        """Test retry works with different exception types."""
        mock_client = Mock()
        
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Success'}]
        }).encode()
        
        mock_client.invoke_model.side_effect = [
            ConnectionError("Network error"),
            TimeoutError("Request timeout"),
            success_response
        ]
        
        config = BedrockConfig(max_retries=3)
        bedrock_client = BedrockClient(mock_client, config)
        
        with patch('time.sleep'):
            result = bedrock_client.invoke("Test prompt")
        
        assert result == 'Success'
        assert mock_client.invoke_model.call_count == 3


class TestFallbackBehavior:
    """Comprehensive tests for fallback behavior."""
    
    def test_fallback_called_on_bedrock_failure(self):
        """Test that fallback is called when Bedrock fails."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("Bedrock unavailable")
        
        bedrock_client = BedrockClient(mock_client)
        
        fallback_called = {'count': 0}
        
        def fallback_gen(field_name, field_type, num_values):
            fallback_called['count'] += 1
            return [f"fallback_{i}" for i in range(num_values)]
        
        with patch('time.sleep'):
            values = bedrock_client.generate_text_field(
                field_name='email',
                field_type='email',
                num_values=10,
                fallback_generator=fallback_gen
            )
        
        assert fallback_called['count'] == 1
        assert len(values) == 10
        assert all(v.startswith('fallback_') for v in values)
    
    def test_fallback_receives_correct_parameters(self):
        """Test that fallback receives correct parameters."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("Bedrock unavailable")
        
        bedrock_client = BedrockClient(mock_client)
        
        received_params = {}
        
        def fallback_gen(field_name, field_type, num_values):
            received_params['field_name'] = field_name
            received_params['field_type'] = field_type
            received_params['num_values'] = num_values
            return [f"val_{i}" for i in range(num_values)]
        
        with patch('time.sleep'):
            bedrock_client.generate_text_field(
                field_name='customer_email',
                field_type='email',
                num_values=15,
                fallback_generator=fallback_gen
            )
        
        assert received_params['field_name'] == 'customer_email'
        assert received_params['field_type'] == 'email'
        assert received_params['num_values'] == 15
    
    def test_fallback_for_partial_batch_failure(self):
        """Test fallback handles partial batch failures correctly."""
        mock_client = Mock()
        
        # First batch succeeds, second batch fails
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': '["val1", "val2", "val3"]'}]
        }).encode()
        
        mock_client.invoke_model.side_effect = [
            success_response,
            Exception("Second batch failed")
        ]
        
        config = BedrockConfig(batch_size=3)
        bedrock_client = BedrockClient(mock_client, config)
        
        def fallback_gen(field_name, field_type, num_values):
            return [f"fallback_{i}" for i in range(num_values)]
        
        with patch('time.sleep'):
            values = bedrock_client.generate_text_field(
                field_name='email',
                field_type='email',
                num_values=7,
                fallback_generator=fallback_gen
            )
        
        assert len(values) == 7
        # First 3 from Bedrock
        assert values[0] == "val1"
        assert values[1] == "val2"
        assert values[2] == "val3"
        # Remaining 4 from fallback
        assert values[3].startswith("fallback_")
        assert values[6].startswith("fallback_")
    
    def test_no_fallback_raises_exception(self):
        """Test that without fallback, exception is raised."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("Bedrock unavailable")
        
        bedrock_client = BedrockClient(mock_client)
        
        with patch('time.sleep'):
            with pytest.raises(Exception, match="Bedrock unavailable"):
                bedrock_client.generate_text_field(
                    field_name='email',
                    field_type='email',
                    num_values=10,
                    fallback_generator=None
                )
    
    def test_fallback_not_called_on_success(self):
        """Test that fallback is not called when Bedrock succeeds."""
        mock_client = Mock()
        
        success_response = {
            'body': MagicMock()
        }
        success_response['body'].read.return_value = json.dumps({
            'content': [{'text': '["val1", "val2", "val3"]'}]
        }).encode()
        
        mock_client.invoke_model.return_value = success_response
        
        bedrock_client = BedrockClient(mock_client)
        
        fallback_called = {'count': 0}
        
        def fallback_gen(field_name, field_type, num_values):
            fallback_called['count'] += 1
            return [f"fallback_{i}" for i in range(num_values)]
        
        values = bedrock_client.generate_text_field(
            field_name='email',
            field_type='email',
            num_values=3,
            fallback_generator=fallback_gen
        )
        
        assert fallback_called['count'] == 0
        assert values == ["val1", "val2", "val3"]
    
    def test_fallback_returns_exact_count(self):
        """Test that fallback returns exactly the requested number of values."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("Bedrock unavailable")
        
        bedrock_client = BedrockClient(mock_client)
        
        def fallback_gen(field_name, field_type, num_values):
            # Return more than requested to test truncation
            return [f"val_{i}" for i in range(num_values + 10)]
        
        with patch('time.sleep'):
            values = bedrock_client.generate_text_field(
                field_name='email',
                field_type='email',
                num_values=5,
                fallback_generator=fallback_gen
            )
        
        # Should return exactly 5 values
        assert len(values) == 5


class TestRuleBasedTextGenerator:
    """Tests for RuleBasedTextGenerator."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = RuleBasedTextGenerator()
        
        assert generator.faker is not None
        assert 'name' in generator.generators
        assert 'email' in generator.generators
    
    def test_generate_names(self):
        """Test generating names."""
        generator = RuleBasedTextGenerator()
        
        values = generator.generate('name_field', 'name', 10)
        
        assert len(values) == 10
        assert all(isinstance(v, str) for v in values)
        assert all(len(v) > 0 for v in values)
    
    def test_generate_emails(self):
        """Test generating emails."""
        generator = RuleBasedTextGenerator()
        
        values = generator.generate('email_field', 'email', 10)
        
        assert len(values) == 10
        assert all('@' in v for v in values)
    
    def test_generate_unknown_type(self):
        """Test generating unknown field type uses default."""
        generator = RuleBasedTextGenerator()
        
        values = generator.generate('unknown_field', 'unknown_type', 5)
        
        assert len(values) == 5
        assert all(isinstance(v, str) for v in values)
    
    def test_generate_with_error_fallback(self):
        """Test that errors in generation are handled."""
        generator = RuleBasedTextGenerator()
        
        # Mock a generator that fails
        def failing_generator():
            raise Exception("Generation failed")
        
        generator.generators['failing_type'] = failing_generator
        
        values = generator.generate('test_field', 'failing_type', 3)
        
        # Should still return values (using simple fallback)
        assert len(values) == 3
        assert all(isinstance(v, str) for v in values)
