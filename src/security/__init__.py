"""
Security Configuration Module

Provides security utilities and configuration for the PetAvatar system.
Implements security requirements from Requirements 6.6, 12.1, 12.2, 12.3, 12.5.
"""
from .s3_security import (
    configure_bucket_security,
    verify_bucket_security,
    S3SecurityConfig,
)
from .api_security import (
    validate_api_key,
    get_api_key_from_secrets,
    APIKeyValidator,
    create_unauthorized_response,
)
from .dynamodb_security import (
    configure_table_security,
    verify_table_security,
    DynamoDBSecurityConfig,
    generate_iam_policy,
    generate_s3_iam_policy,
)
from .api_middleware import (
    require_api_key,
    get_cors_headers,
    handle_cors_preflight,
    add_security_headers,
    create_api_response,
    rate_limit_exceeded_response,
    CORS_HEADERS,
)

__all__ = [
    # S3 Security
    'configure_bucket_security',
    'verify_bucket_security',
    'S3SecurityConfig',
    # API Security
    'validate_api_key',
    'get_api_key_from_secrets',
    'APIKeyValidator',
    'create_unauthorized_response',
    # DynamoDB Security
    'configure_table_security',
    'verify_table_security',
    'DynamoDBSecurityConfig',
    'generate_iam_policy',
    'generate_s3_iam_policy',
    # API Middleware
    'require_api_key',
    'get_cors_headers',
    'handle_cors_preflight',
    'add_security_headers',
    'create_api_response',
    'rate_limit_exceeded_response',
    'CORS_HEADERS',
]
