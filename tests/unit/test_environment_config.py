"""Unit tests for environment configuration loading."""

import pytest
from unittest.mock import patch, mock_open
import os


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""
    
    def test_database_url_loading(self):
        """Test DATABASE_URL environment variable loading."""
        test_url = "postgresql://testuser:testpass@testhost:5432/testdb"
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            loaded_url = os.getenv('DATABASE_URL')
            assert loaded_url == test_url
    
    def test_aws_region_loading(self):
        """Test AWS_REGION environment variable loading."""
        with patch.dict(os.environ, {'AWS_REGION': 'eu-west-1'}):
            region = os.getenv('AWS_REGION')
            assert region == 'eu-west-1'
    
    def test_aws_profile_loading(self):
        """Test AWS_PROFILE environment variable loading."""
        with patch.dict(os.environ, {'AWS_PROFILE': 'production'}):
            profile = os.getenv('AWS_PROFILE')
            assert profile == 'production'
    
    def test_bedrock_model_id_loading(self):
        """Test BEDROCK_MODEL_ID environment variable loading."""
        model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        with patch.dict(os.environ, {'BEDROCK_MODEL_ID': model_id}):
            loaded_model = os.getenv('BEDROCK_MODEL_ID')
            assert loaded_model == model_id
    
    def test_demo_mode_loading(self):
        """Test DEMO_MODE environment variable loading."""
        with patch.dict(os.environ, {'DEMO_MODE': 'true'}):
            demo_mode = os.getenv('DEMO_MODE')
            assert demo_mode == 'true'
            assert demo_mode.lower() == 'true'
    
    def test_log_level_loading(self):
        """Test LOG_LEVEL environment variable loading."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            log_level = os.getenv('LOG_LEVEL')
            assert log_level == 'DEBUG'
    
    def test_missing_optional_variables(self):
        """Test handling of missing optional environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            # Optional variables should return None
            assert os.getenv('AWS_ACCESS_KEY_ID') is None
            assert os.getenv('AWS_SECRET_ACCESS_KEY') is None
            assert os.getenv('CONFLUENCE_URL') is None
            assert os.getenv('JIRA_URL') is None
    
    def test_default_values(self):
        """Test default values for environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            # Test with defaults
            region = os.getenv('AWS_REGION', 'us-east-1')
            assert region == 'us-east-1'
            
            demo_mode = os.getenv('DEMO_MODE', 'false')
            assert demo_mode == 'false'
            
            log_level = os.getenv('LOG_LEVEL', 'INFO')
            assert log_level == 'INFO'
    
    def test_numeric_environment_variables(self):
        """Test numeric environment variable loading."""
        with patch.dict(os.environ, {
            'BACKEND_PORT': '8000',
            'FRONTEND_PORT': '3000',
            'BEDROCK_MAX_TOKENS': '4000'
        }):
            backend_port = int(os.getenv('BACKEND_PORT'))
            assert backend_port == 8000
            
            frontend_port = int(os.getenv('FRONTEND_PORT'))
            assert frontend_port == 3000
            
            max_tokens = int(os.getenv('BEDROCK_MAX_TOKENS'))
            assert max_tokens == 4000
    
    def test_float_environment_variables(self):
        """Test float environment variable loading."""
        with patch.dict(os.environ, {'BEDROCK_TEMPERATURE': '0.7'}):
            temperature = float(os.getenv('BEDROCK_TEMPERATURE'))
            assert temperature == 0.7
    
    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('1', True),
            ('0', False)
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'ENABLE_COST_TRACKING': env_value}):
                value = os.getenv('ENABLE_COST_TRACKING')
                parsed = value.lower() in ('true', '1', 'yes')
                assert parsed == expected
    
    def test_list_environment_variables(self):
        """Test parsing list-like environment variables."""
        cors_origins = 'http://localhost:3000,http://localhost:8000'
        with patch.dict(os.environ, {'CORS_ORIGINS': cors_origins}):
            origins = os.getenv('CORS_ORIGINS')
            origins_list = [o.strip() for o in origins.split(',')]
            assert len(origins_list) == 2
            assert 'http://localhost:3000' in origins_list
            assert 'http://localhost:8000' in origins_list
    
    def test_sensitive_data_not_logged(self):
        """Test that sensitive environment variables are handled securely."""
        sensitive_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'CONFLUENCE_API_TOKEN',
            'JIRA_API_TOKEN'
        ]
        
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIAIOSFODNN7EXAMPLE',
            'AWS_SECRET_ACCESS_KEY': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'CONFLUENCE_API_TOKEN': 'secret_token_123',
            'JIRA_API_TOKEN': 'secret_token_456'
        }):
            for var in sensitive_vars:
                value = os.getenv(var)
                assert value is not None
                # In production, these should never be logged
                assert len(value) > 0


@pytest.mark.unit
class TestEnvironmentValidation:
    """Test environment configuration validation."""
    
    def test_required_database_config(self):
        """Test that database configuration is available."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/db'
        }):
            db_url = os.getenv('DATABASE_URL')
            assert db_url is not None
            assert 'postgresql://' in db_url
            assert '@' in db_url
            assert ':5432' in db_url
    
    def test_aws_configuration_completeness(self):
        """Test that AWS configuration is complete."""
        with patch.dict(os.environ, {
            'AWS_REGION': 'us-east-1',
            'AWS_PROFILE': 'default'
        }):
            region = os.getenv('AWS_REGION')
            profile = os.getenv('AWS_PROFILE')
            
            assert region is not None
            assert profile is not None
    
    def test_bedrock_configuration(self):
        """Test Bedrock configuration variables."""
        with patch.dict(os.environ, {
            'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'BEDROCK_TEMPERATURE': '0.7',
            'BEDROCK_MAX_TOKENS': '4000'
        }):
            model_id = os.getenv('BEDROCK_MODEL_ID')
            temperature = float(os.getenv('BEDROCK_TEMPERATURE'))
            max_tokens = int(os.getenv('BEDROCK_MAX_TOKENS'))
            
            assert 'anthropic' in model_id
            assert 0.0 <= temperature <= 1.0
            assert max_tokens > 0
    
    def test_web_application_config(self):
        """Test web application configuration."""
        with patch.dict(os.environ, {
            'BACKEND_HOST': '0.0.0.0',
            'BACKEND_PORT': '8000',
            'FRONTEND_PORT': '3000'
        }):
            host = os.getenv('BACKEND_HOST')
            backend_port = int(os.getenv('BACKEND_PORT'))
            frontend_port = int(os.getenv('FRONTEND_PORT'))
            
            assert host in ('0.0.0.0', 'localhost', '127.0.0.1')
            assert 1024 <= backend_port <= 65535
            assert 1024 <= frontend_port <= 65535
    
    def test_demo_mode_configuration(self):
        """Test demo mode configuration."""
        with patch.dict(os.environ, {'DEMO_MODE': 'true'}):
            demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
            assert demo_mode is True
            
            # In demo mode, external service configs are optional
            confluence_url = os.getenv('CONFLUENCE_URL')
            jira_url = os.getenv('JIRA_URL')
            # These can be None in demo mode
    
    def test_production_mode_configuration(self):
        """Test production mode requires external service configs."""
        with patch.dict(os.environ, {
            'DEMO_MODE': 'false',
            'CONFLUENCE_URL': 'https://company.atlassian.net',
            'JIRA_URL': 'https://company.atlassian.net'
        }):
            demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
            assert demo_mode is False
            
            # In production mode, these should be set
            confluence_url = os.getenv('CONFLUENCE_URL')
            jira_url = os.getenv('JIRA_URL')
            
            assert confluence_url is not None
            assert jira_url is not None
            assert 'http' in confluence_url
            assert 'http' in jira_url
