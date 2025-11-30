"""
S3 Security Configuration

Implements S3 bucket security requirements:
- Requirements 12.1: Encryption at rest (AES-256)
- Requirements 12.2: 7-day lifecycle policy
- Requirements 12.5: Block public access
"""
import boto3
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class S3SecurityConfig:
    """S3 bucket security configuration."""
    
    # Encryption settings
    encryption_algorithm: str = 'AES256'
    bucket_key_enabled: bool = True
    
    # Public access settings
    block_public_acls: bool = True
    ignore_public_acls: bool = True
    block_public_policy: bool = True
    restrict_public_buckets: bool = True
    
    # Lifecycle settings
    expiration_days: int = 7
    
    # Versioning
    versioning_enabled: bool = True


def configure_bucket_security(
    bucket_name: str,
    config: Optional[S3SecurityConfig] = None,
    s3_client: Optional[Any] = None
) -> Dict[str, bool]:
    """
    Configure S3 bucket with security settings.
    
    Args:
        bucket_name: Name of the S3 bucket
        config: Security configuration (uses defaults if not provided)
        s3_client: Optional boto3 S3 client (creates one if not provided)
        
    Returns:
        Dictionary with configuration results
        
    Requirements: 12.1, 12.2, 12.5
    """
    if config is None:
        config = S3SecurityConfig()
    
    if s3_client is None:
        s3_client = boto3.client('s3')
    
    results = {
        'encryption': False,
        'public_access_block': False,
        'lifecycle': False,
        'versioning': False
    }
    
    # Configure encryption at rest (AES-256)
    # Requirement 12.1
    try:
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': config.encryption_algorithm
                    },
                    'BucketKeyEnabled': config.bucket_key_enabled
                }]
            }
        )
        results['encryption'] = True
        logger.info(f"Configured encryption for bucket: {bucket_name}")
    except Exception as e:
        logger.error(f"Failed to configure encryption for {bucket_name}: {e}")
        raise
    
    # Block all public access
    # Requirement 12.5
    try:
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': config.block_public_acls,
                'IgnorePublicAcls': config.ignore_public_acls,
                'BlockPublicPolicy': config.block_public_policy,
                'RestrictPublicBuckets': config.restrict_public_buckets
            }
        )
        results['public_access_block'] = True
        logger.info(f"Configured public access block for bucket: {bucket_name}")
    except Exception as e:
        logger.error(f"Failed to configure public access block for {bucket_name}: {e}")
        raise
    
    # Configure lifecycle policy for expiration
    # Requirement 12.2
    try:
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                'Rules': [{
                    'ID': f'DeleteAfter{config.expiration_days}Days',
                    'Status': 'Enabled',
                    'Expiration': {'Days': config.expiration_days},
                    'Filter': {'Prefix': ''}
                }]
            }
        )
        results['lifecycle'] = True
        logger.info(f"Configured lifecycle policy for bucket: {bucket_name}")
    except Exception as e:
        logger.error(f"Failed to configure lifecycle for {bucket_name}: {e}")
        raise
    
    # Enable versioning for data protection
    if config.versioning_enabled:
        try:
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            results['versioning'] = True
            logger.info(f"Enabled versioning for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to enable versioning for {bucket_name}: {e}")
            raise
    
    return results


def verify_bucket_security(
    bucket_name: str,
    s3_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Verify S3 bucket security configuration.
    
    Args:
        bucket_name: Name of the S3 bucket
        s3_client: Optional boto3 S3 client
        
    Returns:
        Dictionary with verification results
        
    Requirements: 12.1, 12.2, 12.5
    """
    if s3_client is None:
        s3_client = boto3.client('s3')
    
    results = {
        'bucket_name': bucket_name,
        'encryption_enabled': False,
        'encryption_algorithm': None,
        'public_access_blocked': False,
        'lifecycle_configured': False,
        'expiration_days': None,
        'versioning_enabled': False,
        'compliant': False,
        'issues': []
    }
    
    # Check encryption
    try:
        encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
        rules = encryption.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
        if rules:
            default_encryption = rules[0].get('ApplyServerSideEncryptionByDefault', {})
            results['encryption_enabled'] = True
            results['encryption_algorithm'] = default_encryption.get('SSEAlgorithm')
    except s3_client.exceptions.ClientError as e:
        if 'ServerSideEncryptionConfigurationNotFoundError' in str(e):
            results['issues'].append('Encryption not configured')
        else:
            raise
    
    # Check public access block
    try:
        public_access = s3_client.get_public_access_block(Bucket=bucket_name)
        config = public_access.get('PublicAccessBlockConfiguration', {})
        all_blocked = all([
            config.get('BlockPublicAcls', False),
            config.get('IgnorePublicAcls', False),
            config.get('BlockPublicPolicy', False),
            config.get('RestrictPublicBuckets', False)
        ])
        results['public_access_blocked'] = all_blocked
        if not all_blocked:
            results['issues'].append('Public access not fully blocked')
    except s3_client.exceptions.ClientError as e:
        if 'NoSuchPublicAccessBlockConfiguration' in str(e):
            results['issues'].append('Public access block not configured')
        else:
            raise
    
    # Check lifecycle configuration
    try:
        lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        rules = lifecycle.get('Rules', [])
        for rule in rules:
            if rule.get('Status') == 'Enabled' and 'Expiration' in rule:
                results['lifecycle_configured'] = True
                results['expiration_days'] = rule['Expiration'].get('Days')
                break
        if not results['lifecycle_configured']:
            results['issues'].append('Lifecycle expiration not configured')
    except s3_client.exceptions.ClientError as e:
        if 'NoSuchLifecycleConfiguration' in str(e):
            results['issues'].append('Lifecycle not configured')
        else:
            raise
    
    # Check versioning
    try:
        versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
        results['versioning_enabled'] = versioning.get('Status') == 'Enabled'
    except Exception:
        results['issues'].append('Could not check versioning status')
    
    # Determine overall compliance
    results['compliant'] = (
        results['encryption_enabled'] and
        results['public_access_blocked'] and
        results['lifecycle_configured'] and
        results['expiration_days'] == 7
    )
    
    return results
