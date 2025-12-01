"""
Result Handler
Returns completed identity package with presigned URLs.
"""
import json
import os
import logging
import functools
from datetime import datetime, timezone
from typing import Dict, Any, Callable

import boto3

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def log_error(component: str, operation: str, error: Exception, context: dict) -> None:
    """Log error with structured context."""
    logger.error(json.dumps({
        "component": component,
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))


def emit_metric(metric_name: str, value: float = 1.0, dimensions: dict = None) -> None:
    """Emit CloudWatch metric."""
    try:
        cloudwatch = boto3.client('cloudwatch')
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': 'Count',
            'Timestamp': datetime.now(timezone.utc)
        }
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        cloudwatch.put_metric_data(Namespace='PetAvatar', MetricData=[metric_data])
    except Exception:
        pass


def create_error_response(status_code: int, error_message: str, error_type: str = "Error") -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps({
            'error': error_message,
            'error_type': error_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }


def handle_lambda_errors(func: Callable) -> Callable:
    """Decorator to handle Lambda errors consistently."""
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return func(event, context)
        except Exception as e:
            log_error(
                component=func.__name__,
                operation="handler_execution",
                error=e,
                context={"event_keys": list(event.keys()) if event else []}
            )
            emit_metric("HandlerError", dimensions={"Component": func.__name__})
            return create_error_response(500, str(e), type(e).__name__)
    return wrapper


@handle_lambda_errors
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Retrieve completed avatar results."""
    # Extract job_id from path parameters
    path_params = event.get('pathParameters') or {}
    job_id = path_params.get('job_id')
    
    if not job_id:
        return create_error_response(400, 'Missing job_id parameter', 'ValidationError')
    
    # Get environment variables
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    generated_bucket = os.environ.get('S3_GENERATED_BUCKET')
    
    if not table_name:
        raise ValueError('DYNAMODB_TABLE_NAME environment variable not set')
    if not generated_bucket:
        raise ValueError('S3_GENERATED_BUCKET environment variable not set')
    
    # Query DynamoDB for job
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    response = table.get_item(Key={'job_id': job_id})
    
    if 'Item' not in response:
        return create_error_response(404, f'Job not found: {job_id}', 'NotFoundError')
    
    item = response['Item']
    
    # Check status is "completed"
    if item.get('status') != 'completed':
        return create_error_response(
            409,
            f'Job not completed. Current status: {item.get("status")}',
            'ConflictError'
        )
    
    # Generate presigned URL for avatar (1 hour expiration)
    s3_client = boto3.client('s3')
    avatar_key = item.get('s3_avatar_key')
    
    if not avatar_key:
        return create_error_response(500, 'Avatar image not found', 'InternalError')
    
    avatar_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': generated_bucket, 'Key': avatar_key},
        ExpiresIn=3600
    )
    
    result = {
        'job_id': job_id,
        'avatar_url': avatar_url,
        'identity': item.get('identity_package', {}),
        'pet_analysis': item.get('pet_analysis', {})
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(result)
    }
