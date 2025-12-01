#!/bin/bash
# Set Lambda environment variables after tc deploy
# Run this after each `tc update` or `tc create`

export AWS_PROFILE=rob-berger

echo "Setting Lambda environment variables..."

aws lambda update-function-configuration \
  --function-name petavatar_presigned-url-handler_rberger \
  --environment "Variables={S3_UPLOAD_BUCKET=petavatar-uploads-456773209430}" \
  --no-cli-pager --query "FunctionName" --output text

aws lambda update-function-configuration \
  --function-name petavatar_status-handler_rberger \
  --environment "Variables={DYNAMODB_TABLE_NAME=petavatar-jobs}" \
  --no-cli-pager --query "FunctionName" --output text

aws lambda update-function-configuration \
  --function-name petavatar_result-handler_rberger \
  --environment "Variables={DYNAMODB_TABLE_NAME=petavatar-jobs,S3_GENERATED_BUCKET=petavatar-generated-456773209430}" \
  --no-cli-pager --query "FunctionName" --output text

aws lambda update-function-configuration \
  --function-name petavatar_process-handler_rberger \
  --environment "Variables={DYNAMODB_TABLE_NAME=petavatar-jobs,SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/456773209430/processing-queue}" \
  --no-cli-pager --query "FunctionName" --output text

aws lambda update-function-configuration \
  --function-name petavatar_s3-event-handler_rberger \
  --environment "Variables={DYNAMODB_TABLE_NAME=petavatar-jobs,SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/456773209430/processing-queue}" \
  --no-cli-pager --query "FunctionName" --output text

aws lambda update-function-configuration \
  --function-name petavatar_process-worker_rberger \
  --environment "Variables={DYNAMODB_TABLE_NAME=petavatar-jobs,S3_UPLOAD_BUCKET=petavatar-uploads-456773209430,S3_GENERATED_BUCKET=petavatar-generated-456773209430}" \
  --no-cli-pager --query "FunctionName" --output text

echo "Done!"
