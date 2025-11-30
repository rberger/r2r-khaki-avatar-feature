"""
DynamoDB Security Configuration

Implements DynamoDB security requirements:
- Requirements 12.2: Encryption with AWS managed keys, TTL for cleanup
"""
import boto3
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class DynamoDBSecurityConfig:
    """DynamoDB table security configuration."""
    
    # Encryption settings
    sse_enabled: bool = True
    sse_type: str = 'KMS'  # 'AES256' or 'KMS'
    kms_master_key_id: Optional[str] = None  # None = AWS managed key
    
    # TTL settings
    ttl_enabled: bool = True
    ttl_attribute_name: str = 'ttl'
    
    # Point-in-time recovery
    pitr_enabled: bool = True
    
    # Deletion protection
    deletion_protection_enabled: bool = False  # Enable in production


def configure_table_security(
    table_name: str,
    config: Optional[DynamoDBSecurityConfig] = None,
    dynamodb_client: Optional[Any] = None
) -> Dict[str, bool]:
    """
    Configure DynamoDB table with security settings.
    
    Args:
        table_name: Name of the DynamoDB table
        config: Security configuration (uses defaults if not provided)
        dynamodb_client: Optional boto3 DynamoDB client
        
    Returns:
        Dictionary with configuration results
        
    Requirements: 12.2
    """
    if config is None:
        config = DynamoDBSecurityConfig()
    
    if dynamodb_client is None:
        dynamodb_client = boto3.client('dynamodb')
    
    results = {
        'ttl': False,
        'pitr': False,
        'deletion_protection': False
    }
    
    # Configure TTL for automatic cleanup
    # Requirement 12.2
    if config.ttl_enabled:
        try:
            dynamodb_client.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': config.ttl_attribute_name
                }
            )
            results['ttl'] = True
            logger.info(f"Configured TTL for table: {table_name}")
        except dynamodb_client.exceptions.ResourceNotFoundException:
            logger.error(f"Table not found: {table_name}")
            raise
        except Exception as e:
            # TTL might already be enabled
            if 'TimeToLive is already enabled' in str(e):
                results['ttl'] = True
                logger.info(f"TTL already enabled for table: {table_name}")
            else:
                logger.error(f"Failed to configure TTL for {table_name}: {e}")
                raise
    
    # Configure Point-in-Time Recovery
    if config.pitr_enabled:
        try:
            dynamodb_client.update_continuous_backups(
                TableName=table_name,
                PointInTimeRecoverySpecification={
                    'PointInTimeRecoveryEnabled': True
                }
            )
            results['pitr'] = True
            logger.info(f"Enabled PITR for table: {table_name}")
        except Exception as e:
            logger.warning(f"Could not enable PITR for {table_name}: {e}")
    
    # Configure deletion protection
    if config.deletion_protection_enabled:
        try:
            dynamodb_client.update_table(
                TableName=table_name,
                DeletionProtectionEnabled=True
            )
            results['deletion_protection'] = True
            logger.info(f"Enabled deletion protection for table: {table_name}")
        except Exception as e:
            logger.warning(f"Could not enable deletion protection for {table_name}: {e}")
    
    return results


def verify_table_security(
    table_name: str,
    dynamodb_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Verify DynamoDB table security configuration.
    
    Args:
        table_name: Name of the DynamoDB table
        dynamodb_client: Optional boto3 DynamoDB client
        
    Returns:
        Dictionary with verification results
        
    Requirements: 12.2
    """
    if dynamodb_client is None:
        dynamodb_client = boto3.client('dynamodb')
    
    issues: List[str] = []
    
    results: Dict[str, Any] = {
        'table_name': table_name,
        'encryption_enabled': False,
        'encryption_type': None,
        'ttl_enabled': False,
        'ttl_attribute': None,
        'pitr_enabled': False,
        'deletion_protection': False,
        'compliant': False,
        'issues': issues
    }
    
    # Check table description for encryption
    try:
        table_desc = dynamodb_client.describe_table(TableName=table_name)
        table = table_desc.get('Table', {})
        
        # Check SSE
        sse_desc = table.get('SSEDescription', {})
        if sse_desc.get('Status') == 'ENABLED':
            results['encryption_enabled'] = True
            results['encryption_type'] = sse_desc.get('SSEType')
        else:
            issues.append('Server-side encryption not enabled')
        
        # Check deletion protection
        results['deletion_protection'] = table.get('DeletionProtectionEnabled', False)
        
    except dynamodb_client.exceptions.ResourceNotFoundException:
        issues.append('Table not found')
        return results
    except Exception as e:
        issues.append(f'Error describing table: {e}')
        return results
    
    # Check TTL
    try:
        ttl_desc = dynamodb_client.describe_time_to_live(TableName=table_name)
        ttl_spec = ttl_desc.get('TimeToLiveDescription', {})
        if ttl_spec.get('TimeToLiveStatus') == 'ENABLED':
            results['ttl_enabled'] = True
            results['ttl_attribute'] = ttl_spec.get('AttributeName')
        else:
            issues.append('TTL not enabled')
    except Exception as e:
        issues.append(f'Error checking TTL: {e}')
    
    # Check PITR
    try:
        backup_desc = dynamodb_client.describe_continuous_backups(TableName=table_name)
        pitr_desc = backup_desc.get('ContinuousBackupsDescription', {})
        pitr_status = pitr_desc.get('PointInTimeRecoveryDescription', {})
        results['pitr_enabled'] = pitr_status.get('PointInTimeRecoveryStatus') == 'ENABLED'
    except Exception as e:
        issues.append(f'Error checking PITR: {e}')
    
    # Determine overall compliance
    results['compliant'] = (
        results['encryption_enabled'] and
        results['ttl_enabled']
    )
    
    return results


def generate_iam_policy(
    table_arn: str,
    actions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate least-privilege IAM policy for DynamoDB access.
    
    Args:
        table_arn: ARN of the DynamoDB table
        actions: List of allowed actions (uses defaults if not provided)
        
    Returns:
        IAM policy document
        
    Requirements: 12.2 (least privilege access)
    """
    if actions is None:
        # Default actions for PetAvatar handlers
        actions = [
            'dynamodb:GetItem',
            'dynamodb:PutItem',
            'dynamodb:UpdateItem',
            'dynamodb:Query'
        ]
    
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'DynamoDBTableAccess',
                'Effect': 'Allow',
                'Action': actions,
                'Resource': [
                    table_arn,
                    f'{table_arn}/index/*'  # Include GSI access
                ]
            }
        ]
    }


def generate_s3_iam_policy(
    upload_bucket_arn: str,
    generated_bucket_arn: str
) -> Dict[str, Any]:
    """
    Generate least-privilege IAM policy for S3 access.
    
    Args:
        upload_bucket_arn: ARN of the uploads bucket
        generated_bucket_arn: ARN of the generated bucket
        
    Returns:
        IAM policy document
        
    Requirements: 12.1, 12.5 (least privilege access)
    """
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'S3UploadBucketRead',
                'Effect': 'Allow',
                'Action': [
                    's3:GetObject',
                    's3:HeadObject'
                ],
                'Resource': f'{upload_bucket_arn}/*'
            },
            {
                'Sid': 'S3GeneratedBucketReadWrite',
                'Effect': 'Allow',
                'Action': [
                    's3:GetObject',
                    's3:PutObject',
                    's3:HeadObject'
                ],
                'Resource': f'{generated_bucket_arn}/*'
            },
            {
                'Sid': 'S3PresignedURLGeneration',
                'Effect': 'Allow',
                'Action': [
                    's3:GetObject',
                    's3:PutObject'
                ],
                'Resource': [
                    f'{upload_bucket_arn}/*',
                    f'{generated_bucket_arn}/*'
                ]
            }
        ]
    }
