# IAM Policies for PetAvatar

This directory contains IAM policy documents for the PetAvatar service.
These policies implement least-privilege access as required by Requirements 12.2.

## Policy Files

### petavatar-lambda-policy.json

Main policy for Lambda functions. Grants access to:

- **DynamoDB**: Read/write access to the `petavatar-jobs` table
- **S3 Uploads Bucket**: Read access to uploaded pet images
- **S3 Generated Bucket**: Read/write access for storing generated avatars
- **Secrets Manager**: Read access to API key secret
- **SQS**: Send/receive messages for async processing
- **CloudWatch Logs**: Write logs for debugging
- **CloudWatch Metrics**: Emit custom metrics for monitoring
- **Bedrock**: Invoke Claude and Titan models for AI processing

## Usage

These policies are automatically applied by tc-functors during deployment.
For manual deployment or testing, attach the policy to the Lambda execution role:

```bash
# Create the policy
aws iam create-policy \
  --policy-name PetAvatarLambdaPolicy \
  --policy-document file://scripts/iam-policies/petavatar-lambda-policy.json

# Attach to Lambda execution role
aws iam attach-role-policy \
  --role-name petavatar-lambda-role \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/PetAvatarLambdaPolicy
```

## Security Principles

1. **Least Privilege**: Each permission is scoped to specific resources
2. **Resource Constraints**: ARNs are constrained to PetAvatar resources only
3. **Namespace Isolation**: CloudWatch metrics limited to PetAvatar namespace
4. **Model Restrictions**: Bedrock access limited to required models only

## Requirements Mapping

| Requirement | Implementation |
|-------------|----------------|
| 12.2 | DynamoDB encryption, TTL, least privilege IAM |
| 6.6 | Secrets Manager access for API key validation |
| 11.5 | CloudWatch metrics and logs access |
