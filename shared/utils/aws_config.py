"""AWS configuration and credential management."""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AWSConfig:
    """Manages AWS service clients and configuration."""
    
    def __init__(
        self,
        region_name: str = None,
        profile_name: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        """Initialize AWS configuration.
        
        Args:
            region_name: AWS region (defaults to us-east-1)
            profile_name: AWS profile name from ~/.aws/credentials
            aws_access_key_id: AWS access key (overrides profile)
            aws_secret_access_key: AWS secret key (overrides profile)
        """
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        self.profile_name = profile_name or os.getenv('AWS_PROFILE')
        
        # Build session kwargs
        session_kwargs = {'region_name': self.region_name}
        
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs['aws_access_key_id'] = aws_access_key_id
            session_kwargs['aws_secret_access_key'] = aws_secret_access_key
        elif self.profile_name:
            session_kwargs['profile_name'] = self.profile_name
        
        self.session = boto3.Session(**session_kwargs)
        
        # Default config for all clients
        self.config = Config(
            region_name=self.region_name,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
    
    def get_bedrock_client(self):
        """Get Amazon Bedrock runtime client.
        
        Returns:
            boto3 Bedrock runtime client
        """
        return self.session.client(
            'bedrock-runtime',
            config=self.config
        )
    
    def get_s3_client(self):
        """Get S3 client.
        
        Returns:
            boto3 S3 client
        """
        return self.session.client('s3', config=self.config)
    
    def get_secrets_manager_client(self):
        """Get Secrets Manager client.
        
        Returns:
            boto3 Secrets Manager client
        """
        return self.session.client('secretsmanager', config=self.config)
    
    def verify_credentials(self) -> bool:
        """Verify AWS credentials are valid.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            sts = self.session.client('sts', config=self.config)
            identity = sts.get_caller_identity()
            logger.info(f"AWS credentials verified for account: {identity['Account']}")
            return True
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"AWS credential verification failed: {e}")
            return False
    
    def verify_bedrock_access(self) -> bool:
        """Verify access to Amazon Bedrock.
        
        Returns:
            True if Bedrock is accessible, False otherwise
        """
        try:
            bedrock = self.session.client('bedrock', config=self.config)
            # List foundation models to verify access
            bedrock.list_foundation_models(byProvider='anthropic')
            logger.info("Amazon Bedrock access verified")
            return True
        except ClientError as e:
            logger.error(f"Amazon Bedrock access verification failed: {e}")
            return False


def get_secret(secret_name: str, region_name: str = None) -> dict:
    """Retrieve a secret from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret
        region_name: AWS region (optional)
    
    Returns:
        Secret value as dictionary
    
    Raises:
        ClientError: If secret cannot be retrieved
    """
    aws_config = AWSConfig(region_name=region_name)
    client = aws_config.get_secrets_manager_client()
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        import json
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise
