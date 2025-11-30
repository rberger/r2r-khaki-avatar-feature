"""
API Security Configuration

Implements API security requirements:
- Requirements 6.6: API key validation
"""
import json
import os
import boto3
from typing import Optional, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """
    API key validator with caching support.
    
    Validates API keys against AWS Secrets Manager.
    Implements Requirement 6.6.
    """
    
    def __init__(
        self,
        secret_arn: Optional[str] = None,
        secrets_client: Optional[Any] = None,
        cache_ttl: int = 300  # 5 minutes
    ):
        """
        Initialize API key validator.
        
        Args:
            secret_arn: ARN of the secret containing the API key
            secrets_client: Optional boto3 Secrets Manager client
            cache_ttl: Cache TTL in seconds (default 5 minutes)
        """
        self.secret_arn = secret_arn or os.environ.get('API_KEY_SECRET_ARN')
        self._secrets_client = secrets_client
        self._cache_ttl = cache_ttl
        self._cached_key: Optional[str] = None
        self._cache_timestamp: float = 0
    
    @property
    def secrets_client(self) -> Any:
        """Get or create Secrets Manager client."""
        if self._secrets_client is None:
            self._secrets_client = boto3.client('secretsmanager')
        return self._secrets_client
    
    def _get_cached_key(self) -> Optional[str]:
        """Get API key from cache or fetch from Secrets Manager."""
        import time
        
        current_time = time.time()
        
        # Check if cache is valid
        if (
            self._cached_key is not None and
            current_time - self._cache_timestamp < self._cache_ttl
        ):
            return self._cached_key
        
        # Fetch from Secrets Manager
        if not self.secret_arn:
            return None
        
        try:
            response = self.secrets_client.get_secret_value(SecretId=self.secret_arn)
            secret_data = json.loads(response['SecretString'])
            self._cached_key = secret_data.get('api_key')
            self._cache_timestamp = current_time
            return self._cached_key
        except Exception as e:
            logger.error(f"Failed to fetch API key from Secrets Manager: {e}")
            return None
    
    def validate(self, api_key: Optional[str]) -> bool:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
            
        Requirement 6.6: Invalid API keys are rejected
        """
        if not api_key:
            logger.warning("API key validation failed: No API key provided")
            return False
        
        # If no secret ARN configured, accept any non-empty key (local testing)
        if not self.secret_arn:
            logger.debug("No secret ARN configured, accepting any non-empty key")
            return True
        
        valid_key = self._get_cached_key()
        
        if valid_key is None:
            logger.error("Could not retrieve valid API key from Secrets Manager")
            return False
        
        is_valid = api_key == valid_key
        
        if not is_valid:
            logger.warning("API key validation failed: Invalid key")
        
        return is_valid
    
    def clear_cache(self) -> None:
        """Clear the cached API key."""
        self._cached_key = None
        self._cache_timestamp = 0


# Global validator instance for convenience
_default_validator: Optional[APIKeyValidator] = None


def get_api_key_validator() -> APIKeyValidator:
    """Get or create the default API key validator."""
    global _default_validator
    if _default_validator is None:
        _default_validator = APIKeyValidator()
    return _default_validator


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate an API key using the default validator.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
        
    Requirement 6.6: Invalid API keys are rejected with 401 Unauthorized
    """
    return get_api_key_validator().validate(api_key)


def get_api_key_from_secrets(
    secret_arn: Optional[str] = None,
    secrets_client: Optional[Any] = None
) -> Optional[str]:
    """
    Retrieve API key from Secrets Manager.
    
    Args:
        secret_arn: ARN of the secret (uses env var if not provided)
        secrets_client: Optional boto3 Secrets Manager client
        
    Returns:
        API key string or None if not found
    """
    arn = secret_arn or os.environ.get('API_KEY_SECRET_ARN')
    
    if not arn:
        return None
    
    client = secrets_client or boto3.client('secretsmanager')
    
    try:
        response = client.get_secret_value(SecretId=arn)
        secret_data = json.loads(response['SecretString'])
        return secret_data.get('api_key')
    except Exception as e:
        logger.error(f"Failed to retrieve API key: {e}")
        return None


def create_unauthorized_response(message: str = 'Unauthorized: Invalid API key') -> dict:
    """
    Create a standardized 401 Unauthorized response.
    
    Args:
        message: Error message to include
        
    Returns:
        API Gateway response dictionary
        
    Requirement 6.6: Invalid API keys return 401 Unauthorized
    """
    return {
        'statusCode': 401,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps({
            'error': 'AuthenticationError',
            'message': message
        })
    }
