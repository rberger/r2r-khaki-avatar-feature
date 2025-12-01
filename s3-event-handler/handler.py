"""
S3 Event Handler
Handles S3 upload event notifications and initiates processing.
"""
import json
import os
import re
import logging
import functools
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable

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


def handle_lambda_errors(func: Callable) -> Callable:
    """Decorator to handle Lambda errors consistently."""
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return func(event, context)
        except Exception as e:
            log_error(func.__name__, "handler_execution", e, {})
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
    return wrapper


def validate_object_key(key: str) -> Optional[str]:
    """Validate object key matches expected pattern and extract job ID."""
    pattern = r'^uploads/([^/]+)/.+'
    match = re.match(pattern, key)
    return match.group(1) if match else None


@handle_lambda_errors
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process S3 upload events and queue for avatar generation."""
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    queue_url = os.environ.get('SQS_QUEUE_URL')
    
    if not table_name or not queue_url:
        raise ValueError('Missing required environment variables')
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    sqs_client = boto3.client('sqs')
    
    processed_count = 0
    error_count = 0
    
    for record in event.get('Records', []):
        s3_info = record.get('s3', {})
        bucket_name = s3_info.get('bucket', {}).get('name')
        object_key = s3_info.get('object', {}).get('key')
        
        if not bucket_name or not object_key:
            error_count += 1
            continue
        
        job_id = validate_object_key(object_key)
        if not job_id:
            error_count += 1
            continue
        
        timestamp = datetime.now(timezone.utc).isoformat()
        ttl = int(datetime.now(timezone.utc).timestamp()) + (7 * 24 * 60 * 60)
        
        try:
            response = table.get_item(Key={'job_id': job_id})
            if 'Item' not in response:
                table.put_item(Item={
                    'job_id': job_id,
                    'status': 'queued',
                    'created_at': timestamp,
                    'updated_at': timestamp,
                    's3_upload_key': object_key,
                    'progress': 0,
                    'ttl': ttl
                })
            else:
                table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET updated_at = :timestamp, s3_upload_key = :key',
                    ExpressionAttributeValues={':timestamp': timestamp, ':key': object_key}
                )
        except Exception as e:
            log_error("s3-event-handler", "update_dynamodb", e, {"job_id": job_id})
            error_count += 1
            continue
        
        try:
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({
                    'job_id': job_id,
                    's3_upload_key': object_key,
                    'timestamp': timestamp
                })
            )
            processed_count += 1
        except Exception as e:
            log_error("s3-event-handler", "send_sqs_message", e, {"job_id": job_id})
            error_count += 1
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Events processed',
            'processed': processed_count,
            'errors': error_count
        })
    }
