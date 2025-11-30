"""
S3 Event Handler
Handles S3 upload event notifications and initiates processing.
"""
import json
import os
import re
import sys
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from src.utils import (
    handle_lambda_errors,
    log_error,
    emit_metric
)


def validate_object_key(key: str) -> Optional[str]:
    """
    Validate object key matches expected pattern and extract job ID.
    
    Args:
        key: S3 object key
        
    Returns:
        Job ID if valid, None otherwise
    """
    # Requirement 2.2: Validate object key pattern (uploads/{job_id}/*)
    pattern = r'^uploads/([^/]+)/.+$'
    match = re.match(pattern, key)
    
    if not match:
        return None
    
    job_id = match.group(1)
    return job_id


@handle_lambda_errors
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process S3 upload events and queue for avatar generation.
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    Validates: Requirements 11.1, 11.2, 11.5
    """
    # Get environment variables
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    queue_url = os.environ.get('SQS_QUEUE_URL')
    
    if not table_name or not queue_url:
        log_error(
            component="s3-event-handler",
            operation="get_environment_config",
            error=ValueError('Missing environment variables'),
            context={}
        )
        emit_metric(
            "ConfigurationError",
            dimensions={"Component": "s3-event-handler"}
        )
        raise ValueError('Missing required environment variables')
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    sqs_client = boto3.client('sqs')
    
    processed_count = 0
    error_count = 0
    
    # Requirement 2.1: Process S3 event notification
    for record in event.get('Records', []):
        # Extract S3 information
        s3_info = record.get('s3', {})
        bucket_name = s3_info.get('bucket', {}).get('name')
        object_key = s3_info.get('object', {}).get('key')
        
        if not bucket_name or not object_key:
            log_error(
                component="s3-event-handler",
                operation="parse_s3_event",
                error=ValueError('Invalid S3 event record'),
                context={"record": record}
            )
            emit_metric(
                "InvalidS3Event",
                dimensions={"Component": "s3-event-handler"}
            )
            error_count += 1
            continue
        
        # Validate object key and extract job ID
        job_id = validate_object_key(object_key)
        
        if not job_id:
            # Requirement 2.5: Log invalid events and take no further action
            log_error(
                component="s3-event-handler",
                operation="validate_object_key",
                error=ValueError('Invalid object key pattern'),
                context={"object_key": object_key}
            )
            emit_metric(
                "InvalidObjectKey",
                dimensions={"Component": "s3-event-handler"}
            )
            error_count += 1
            continue
        
        timestamp = datetime.now(timezone.utc).isoformat()
        ttl = int(datetime.now(timezone.utc).timestamp()) + (7 * 24 * 60 * 60)  # 7 days
        
        # Requirement 2.3: Create DynamoDB record if it doesn't exist
        try:
            # Try to get existing item
            response = table.get_item(Key={'job_id': job_id})
            
            if 'Item' not in response:
                # Create new record
                table.put_item(
                    Item={
                        'job_id': job_id,
                        'status': 'queued',
                        'created_at': timestamp,
                        'updated_at': timestamp,
                        's3_upload_key': object_key,
                        'progress': 0,
                        'ttl': ttl
                    }
                )
                emit_metric(
                    "DynamoDBRecordCreated",
                    dimensions={"Component": "s3-event-handler"}
                )
            else:
                # Update existing record
                table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET updated_at = :timestamp, s3_upload_key = :key',
                    ExpressionAttributeValues={
                        ':timestamp': timestamp,
                        ':key': object_key
                    }
                )
                emit_metric(
                    "DynamoDBRecordUpdated",
                    dimensions={"Component": "s3-event-handler"}
                )
        except Exception as e:
            log_error(
                component="s3-event-handler",
                operation="update_dynamodb",
                error=e,
                context={"job_id": job_id, "object_key": object_key}
            )
            emit_metric(
                "DynamoDBError",
                dimensions={"Component": "s3-event-handler"}
            )
            error_count += 1
            continue
        
        # Requirement 2.4: Send message to processing queue
        try:
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({
                    'job_id': job_id,
                    's3_upload_key': object_key,
                    'timestamp': timestamp
                })
            )
            emit_metric(
                "SQSMessageSent",
                dimensions={"Component": "s3-event-handler"}
            )
            processed_count += 1
        except Exception as e:
            log_error(
                component="s3-event-handler",
                operation="send_sqs_message",
                error=e,
                context={"job_id": job_id, "object_key": object_key}
            )
            emit_metric(
                "SQSError",
                dimensions={"Component": "s3-event-handler"}
            )
            error_count += 1
            continue
    
    # Emit summary metrics
    emit_metric(
        "S3EventsProcessed",
        value=processed_count,
        dimensions={"Component": "s3-event-handler"}
    )
    
    if error_count > 0:
        emit_metric(
            "S3EventErrors",
            value=error_count,
            dimensions={"Component": "s3-event-handler"}
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Events processed',
            'processed': processed_count,
            'errors': error_count
        })
    }
