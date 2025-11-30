"""
Presigned URL Handler
Generates presigned S3 POST URLs for direct image uploads.
"""
import json
import uuid
import os
import sys
import boto3
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from src.utils import (
    handle_lambda_errors,
    log_error,
    emit_metric,
    create_error_response
)


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key against Secrets Manager.
    
    Args:
        api_key: API key from request header
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    
    try:
        secret_arn = os.environ.get('API_KEY_SECRET_ARN')
        if not secret_arn:
            # For local testing, accept any non-empty key
            return True
        
        secrets_client = boto3.client('secretsmanager')
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        valid_key = json.loads(response['SecretString']).get('api_key')
        
        return api_key == valid_key
    except Exception as e:
        # Log validation errors but don't expose details
        log_error(
            component="presigned-url-handler",
            operation="validate_api_key",
            error=e,
            context={"has_api_key": bool(api_key)}
        )
        # If we can't validate, reject for security
        return False


@handle_lambda_errors
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate presigned S3 URL for pet image upload.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 6.1
    Validates: Requirements 11.1, 11.2, 11.5
    """
    # Validate API key from headers
    api_key = event.get('headers', {}).get('x-api-key')
    if not validate_api_key(api_key):
        emit_metric(
            "APIKeyValidationFailure",
            dimensions={"Component": "presigned-url-handler"}
        )
        return create_error_response(
            status_code=401,
            error_message='Unauthorized: Invalid API key',
            error_type='AuthenticationError'
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Get S3 bucket from environment
    upload_bucket = os.environ.get('S3_UPLOAD_BUCKET')
    if not upload_bucket:
        log_error(
            component="presigned-url-handler",
            operation="get_environment_config",
            error=ValueError('S3_UPLOAD_BUCKET not configured'),
            context={"job_id": job_id}
        )
        emit_metric(
            "ConfigurationError",
            dimensions={"Component": "presigned-url-handler"}
        )
        raise ValueError('S3_UPLOAD_BUCKET environment variable not set')
    
    # Generate S3 key for upload
    s3_key = f'uploads/{job_id}/original'
    
    # Create S3 client
    s3_client = boto3.client('s3')
    
    # Generate presigned POST URL with conditions
    # Requirements: 1.1 (15-minute expiration), 1.2 (format restrictions), 1.3 (50MB limit)
    presigned_post = s3_client.generate_presigned_post(
        Bucket=upload_bucket,
        Key=s3_key,
        Fields={
            'Content-Type': '${filename}'
        },
        Conditions=[
            {'bucket': upload_bucket},
            ['starts-with', '$key', f'uploads/{job_id}/'],
            ['starts-with', '$Content-Type', 'image/'],
            ['content-length-range', 1, 50 * 1024 * 1024],  # 1 byte to 50MB
            # Accept JPEG, PNG, HEIC formats
            ['eq', '$Content-Type', 'image/jpeg'],
            ['eq', '$Content-Type', 'image/png'],
            ['eq', '$Content-Type', 'image/heic']
        ],
        ExpiresIn=900  # 15 minutes
    )
    
    # Emit success metric
    emit_metric(
        "PresignedURLGenerated",
        dimensions={"Component": "presigned-url-handler"}
    )
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps({
            'job_id': job_id,
            'upload_url': presigned_post['url'],
            'upload_fields': presigned_post['fields'],
            'expires_in': 900
        })
    }
