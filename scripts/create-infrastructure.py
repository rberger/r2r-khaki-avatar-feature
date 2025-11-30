#!/usr/bin/env python3
"""
Infrastructure Provisioning Script

Creates AWS resources not yet supported by tc-functors:
- DynamoDB table for job tracking
- S3 buckets for uploads and generated avatars
- API key in Secrets Manager

Requirements: 12.1, 12.2, 12.5, 6.6
"""
import boto3
import json
import secrets
import sys
import os
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.security import (
    S3SecurityConfig,
    configure_bucket_security,
    verify_bucket_security,
    DynamoDBSecurityConfig,
    configure_table_security,
    verify_table_security
)


def get_account_id() -> str:
    """Get AWS account ID."""
    sts = boto3.client('sts')
    return sts.get_caller_identity()['Account']


def create_dynamodb_table(table_name: str = 'petavatar-jobs') -> Dict[str, Any]:
    """
    Create DynamoDB table for job tracking.
    
    Requirements: 12.2
    """
    dynamodb = boto3.client('dynamodb')
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'job_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            SSESpecification={
                'Enabled': True,
                'SSEType': 'KMS'
            },
            Tags=[
                {'Key': 'Project', 'Value': 'PetAvatar'},
                {'Key': 'ManagedBy', 'Value': 'create-infrastructure.py'}
            ]
        )
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        # Apply security configuration using the security module
        # Requirements: 12.2 (encryption, TTL, least privilege)
        security_config = DynamoDBSecurityConfig(
            sse_enabled=True,
            sse_type='KMS',
            ttl_enabled=True,
            ttl_attribute_name='ttl',
            pitr_enabled=True,
            deletion_protection_enabled=False  # Enable in production
        )
        
        configure_table_security(table_name, security_config, dynamodb)
        
        # Verify security configuration
        verification = verify_table_security(table_name, dynamodb)
        if verification['compliant']:
            print(f"✓ Created DynamoDB table with security: {table_name}")
        else:
            print(f"⚠ DynamoDB table created but has issues: {verification['issues']}")
        
        return response
    except dynamodb.exceptions.ResourceInUseException:
        print(f"✓ DynamoDB table already exists: {table_name}")
        # Verify existing table security
        verification = verify_table_security(table_name, dynamodb)
        if not verification['compliant']:
            print(f"  ⚠ Applying security configuration...")
            configure_table_security(table_name, DynamoDBSecurityConfig(), dynamodb)
        return {'TableName': table_name}


def create_s3_bucket(bucket_name: str) -> Dict[str, Any]:
    """
    Create S3 bucket with security configurations.
    
    Requirements: 12.1, 12.2, 12.5
    """
    s3 = boto3.client('s3')
    region = boto3.session.Session().region_name or 'us-east-1'
    
    try:
        # Create bucket
        if region == 'us-east-1':
            response = s3.create_bucket(Bucket=bucket_name)
        else:
            response = s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        # Apply security configuration using the security module
        # Requirements: 12.1 (encryption), 12.2 (lifecycle), 12.5 (public access block)
        security_config = S3SecurityConfig(
            encryption_algorithm='AES256',
            bucket_key_enabled=True,
            block_public_acls=True,
            ignore_public_acls=True,
            block_public_policy=True,
            restrict_public_buckets=True,
            expiration_days=7,
            versioning_enabled=True
        )
        
        configure_bucket_security(bucket_name, security_config, s3)
        
        # Add bucket tags
        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {'Key': 'Project', 'Value': 'PetAvatar'},
                    {'Key': 'ManagedBy', 'Value': 'create-infrastructure.py'}
                ]
            }
        )
        
        # Verify security configuration
        verification = verify_bucket_security(bucket_name, s3)
        if verification['compliant']:
            print(f"✓ Created S3 bucket with security: {bucket_name}")
        else:
            print(f"⚠ S3 bucket created but has issues: {verification['issues']}")
        
        return response
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"✓ S3 bucket already exists: {bucket_name}")
        # Verify existing bucket security
        verification = verify_bucket_security(bucket_name, s3)
        if not verification['compliant']:
            print(f"  ⚠ Applying security configuration...")
            configure_bucket_security(bucket_name, S3SecurityConfig(), s3)
        return {'Bucket': bucket_name}
    except s3.exceptions.BucketAlreadyExists:
        print(f"✗ S3 bucket name already taken: {bucket_name}")
        raise


def create_api_key(secret_name: str = 'petavatar-api-key') -> str:
    """
    Create API key and store in Secrets Manager.
    
    Requirements: 6.6
    """
    secretsmanager = boto3.client('secretsmanager')
    
    # Generate secure API key
    api_key = secrets.token_urlsafe(32)
    
    try:
        response = secretsmanager.create_secret(
            Name=secret_name,
            Description='API key for PetAvatar service authentication',
            SecretString=json.dumps({
                'api_key': api_key,
                'created_at': '2024-01-01T00:00:00Z'  # Will be updated by AWS
            }),
            Tags=[
                {'Key': 'Project', 'Value': 'PetAvatar'},
                {'Key': 'ManagedBy', 'Value': 'create-infrastructure.py'}
            ]
        )
        
        print(f"✓ Created API key in Secrets Manager: {secret_name}")
        print(f"  API Key: {api_key}")
        print(f"  ARN: {response['ARN']}")
        return api_key
    except secretsmanager.exceptions.ResourceExistsException:
        # Retrieve existing key
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        api_key = secret_data['api_key']
        print(f"✓ API key already exists: {secret_name}")
        print(f"  API Key: {api_key}")
        return api_key


def main():
    """Main provisioning function."""
    print("PetAvatar Infrastructure Provisioning")
    print("=" * 50)
    
    try:
        # Get AWS account ID
        account_id = get_account_id()
        print(f"AWS Account ID: {account_id}\n")
        
        # Create DynamoDB table
        print("Creating DynamoDB table...")
        create_dynamodb_table()
        print()
        
        # Create S3 buckets
        print("Creating S3 buckets...")
        upload_bucket = f'petavatar-uploads-{account_id}'
        generated_bucket = f'petavatar-generated-{account_id}'
        
        create_s3_bucket(upload_bucket)
        create_s3_bucket(generated_bucket)
        print()
        
        # Create API key
        print("Creating API key...")
        api_key = create_api_key()
        print()
        
        # Summary
        print("=" * 50)
        print("Infrastructure provisioning complete!")
        print()
        print("Resources created:")
        print(f"  - DynamoDB table: petavatar-jobs")
        print(f"  - S3 upload bucket: {upload_bucket}")
        print(f"  - S3 generated bucket: {generated_bucket}")
        print(f"  - API key: {api_key}")
        print()
        print("Next steps:")
        print("  1. Deploy tc-functors topology: tc create")
        print("  2. Deploy Strands Agent: agentcore launch")
        print("  3. Configure Lambda environment variables")
        print("  4. Set up S3 event notifications")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
