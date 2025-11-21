"""Unit tests for AWS configuration and credential management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError
import os
from shared.utils.aws_config import AWSConfig, get_secret


class TestAWSConfig:
    """Test AWSConfig class."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = AWSConfig()
            
            assert config.region_name == 'us-east-1'
            assert config.profile_name is None
            assert config.session is not None
            assert config.config is not None
    
    def test_init_with_region_from_env(self):
        """Test initialization with region from environment variable."""
        with patch.dict(os.environ, {'AWS_REGION': 'eu-west-1'}):
            config = AWSConfig()
            assert config.region_name == 'eu-west-1'
    
    def test_init_with_explicit_region(self):
        """Test initialization with explicit region parameter."""
        config = AWSConfig(region_name='ap-southeast-1')
        assert config.region_name == 'ap-southeast-1'
    
    @patch('boto3.Session')
    def test_init_with_profile_from_env(self, mock_session_class):
        """Test initialization with profile from environment variable."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        with patch.dict(os.environ, {'AWS_PROFILE': 'test-profile'}):
            config = AWSConfig()
            assert config.profile_name == 'test-profile'
    
    @patch('boto3.Session')
    def test_init_with_explicit_profile(self, mock_session_class):
        """Test initialization with explicit profile parameter."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        config = AWSConfig(profile_name='my-profile')
        assert config.profile_name == 'my-profile'
    
    def test_init_with_access_keys(self):
        """Test initialization with explicit access keys."""
        config = AWSConfig(
            aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
            aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        )
        
        assert config.session is not None
        # Access keys should take precedence over profile
    
    def test_config_retry_settings(self):
        """Test that boto3 config has retry settings."""
        config = AWSConfig()
        
        assert config.config.retries is not None
        assert config.config.retries['max_attempts'] == 3
        assert config.config.retries['mode'] == 'adaptive'
    
    @patch('boto3.Session')
    def test_get_bedrock_client(self, mock_session_class):
        """Test getting Bedrock runtime client."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        client = config.get_bedrock_client()
        
        mock_session.client.assert_called_once()
        call_args = mock_session.client.call_args
        assert call_args[0][0] == 'bedrock-runtime'
        assert client == mock_client
    
    @patch('boto3.Session')
    def test_get_s3_client(self, mock_session_class):
        """Test getting S3 client."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        client = config.get_s3_client()
        
        mock_session.client.assert_called_once()
        call_args = mock_session.client.call_args
        assert call_args[0][0] == 's3'
        assert client == mock_client
    
    @patch('boto3.Session')
    def test_get_secrets_manager_client(self, mock_session_class):
        """Test getting Secrets Manager client."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        client = config.get_secrets_manager_client()
        
        mock_session.client.assert_called_once()
        call_args = mock_session.client.call_args
        assert call_args[0][0] == 'secretsmanager'
        assert client == mock_client
    
    @patch('boto3.Session')
    def test_verify_credentials_success(self, mock_session_class):
        """Test successful credential verification."""
        mock_session = MagicMock()
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {
            'Account': '123456789012',
            'UserId': 'AIDAI...',
            'Arn': 'arn:aws:iam::123456789012:user/test'
        }
        mock_session.client.return_value = mock_sts
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        result = config.verify_credentials()
        
        assert result is True
        mock_sts.get_caller_identity.assert_called_once()
    
    @patch('boto3.Session')
    def test_verify_credentials_failure_no_credentials(self, mock_session_class):
        """Test credential verification with no credentials."""
        mock_session = MagicMock()
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.side_effect = NoCredentialsError()
        mock_session.client.return_value = mock_sts
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        result = config.verify_credentials()
        
        assert result is False
    
    @patch('boto3.Session')
    def test_verify_credentials_failure_client_error(self, mock_session_class):
        """Test credential verification with client error."""
        mock_session = MagicMock()
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.side_effect = ClientError(
            {'Error': {'Code': 'InvalidClientTokenId', 'Message': 'Invalid token'}},
            'GetCallerIdentity'
        )
        mock_session.client.return_value = mock_sts
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        result = config.verify_credentials()
        
        assert result is False
    
    @patch('boto3.Session')
    def test_verify_bedrock_access_success(self, mock_session_class):
        """Test successful Bedrock access verification."""
        mock_session = MagicMock()
        mock_bedrock = MagicMock()
        mock_bedrock.list_foundation_models.return_value = {
            'modelSummaries': [
                {'modelId': 'anthropic.claude-3-sonnet-20240229-v1:0'}
            ]
        }
        mock_session.client.return_value = mock_bedrock
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        result = config.verify_bedrock_access()
        
        assert result is True
        mock_bedrock.list_foundation_models.assert_called_once_with(byProvider='anthropic')
    
    @patch('boto3.Session')
    def test_verify_bedrock_access_failure(self, mock_session_class):
        """Test Bedrock access verification failure."""
        mock_session = MagicMock()
        mock_bedrock = MagicMock()
        mock_bedrock.list_foundation_models.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
            'ListFoundationModels'
        )
        mock_session.client.return_value = mock_bedrock
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        result = config.verify_bedrock_access()
        
        assert result is False


class TestGetSecret:
    """Test get_secret function."""
    
    @patch('shared.utils.aws_config.AWSConfig')
    def test_get_secret_success(self, mock_aws_config_class):
        """Test successful secret retrieval."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "secret123"}'
        }
        mock_config.get_secrets_manager_client.return_value = mock_client
        mock_aws_config_class.return_value = mock_config
        
        result = get_secret('my-secret')
        
        assert result == {"username": "admin", "password": "secret123"}
        mock_client.get_secret_value.assert_called_once_with(SecretId='my-secret')
    
    @patch('shared.utils.aws_config.AWSConfig')
    def test_get_secret_with_region(self, mock_aws_config_class):
        """Test secret retrieval with specific region."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"key": "value"}'
        }
        mock_config.get_secrets_manager_client.return_value = mock_client
        mock_aws_config_class.return_value = mock_config
        
        result = get_secret('my-secret', region_name='eu-west-1')
        
        mock_aws_config_class.assert_called_once_with(region_name='eu-west-1')
        assert result == {"key": "value"}
    
    @patch('shared.utils.aws_config.AWSConfig')
    def test_get_secret_failure(self, mock_aws_config_class):
        """Test secret retrieval failure."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )
        mock_config.get_secrets_manager_client.return_value = mock_client
        mock_aws_config_class.return_value = mock_config
        
        with pytest.raises(ClientError):
            get_secret('nonexistent-secret')


@pytest.mark.unit
class TestAWSConfigIntegration:
    """Integration-style tests for AWS configuration."""
    
    def test_multiple_client_creation(self):
        """Test creating multiple clients from same config."""
        config = AWSConfig()
        
        # Should be able to create multiple clients
        bedrock_client = config.get_bedrock_client()
        s3_client = config.get_s3_client()
        secrets_client = config.get_secrets_manager_client()
        
        assert bedrock_client is not None
        assert s3_client is not None
        assert secrets_client is not None
    
    def test_config_immutability(self):
        """Test that config settings are properly set."""
        config = AWSConfig(region_name='us-west-2')
        
        # Region should be set correctly
        assert config.region_name == 'us-west-2'
        assert config.config.region_name == 'us-west-2'
    
    @patch('boto3.Session')
    @patch.dict(os.environ, {
        'AWS_REGION': 'eu-central-1',
        'AWS_PROFILE': 'production'
    })
    def test_environment_variable_precedence(self, mock_session_class):
        """Test that environment variables are used correctly."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        config = AWSConfig()
        
        assert config.region_name == 'eu-central-1'
        assert config.profile_name == 'production'
    
    @patch('boto3.Session')
    def test_explicit_parameters_override_env(self, mock_session_class):
        """Test that explicit parameters override environment variables."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        with patch.dict(os.environ, {
            'AWS_REGION': 'us-east-1',
            'AWS_PROFILE': 'default'
        }):
            config = AWSConfig(
                region_name='ap-south-1',
                profile_name='custom'
            )
            
            assert config.region_name == 'ap-south-1'
            assert config.profile_name == 'custom'
