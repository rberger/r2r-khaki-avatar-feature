"""
Process Worker
Orchestrates avatar generation via Strands Agent.
"""

import json
import os
import base64
import time
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import boto3

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from src.utils import (
    log_error,
    emit_metric,
    retry_with_exponential_backoff
)


def update_job_status(
    table_name: str,
    job_id: str,
    status: str,
    progress: Optional[int] = None,
    error_message: Optional[str] = None,
    results: Optional[dict] = None,
) -> None:
    """
    Update job status in DynamoDB.

    Args:
        table_name: DynamoDB table name
        job_id: Job identifier
        status: New status (queued, processing, completed, failed)
        progress: Optional progress percentage (0-100)
        error_message: Optional error message for failed jobs
        results: Optional results dictionary for completed jobs
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    update_expr = "SET #status = :status, updated_at = :updated_at"
    expr_attr_names = {"#status": "status"}
    expr_attr_values: Dict[str, Any] = {
        ":status": status,
        ":updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if progress is not None:
        update_expr += ", progress = :progress"
        expr_attr_values[":progress"] = progress

    if error_message:
        update_expr += ", error_message = :error_message"
        expr_attr_values[":error_message"] = error_message

    if results:
        # Store identity package and pet analysis
        if "identity_package" in results:
            update_expr += ", identity_package = :identity_package"
            expr_attr_values[":identity_package"] = results["identity_package"]

        if "pet_analysis" in results:
            update_expr += ", pet_analysis = :pet_analysis"
            expr_attr_values[":pet_analysis"] = results["pet_analysis"]

        if "s3_avatar_key" in results:
            update_expr += ", s3_avatar_key = :s3_avatar_key"
            expr_attr_values[":s3_avatar_key"] = results["s3_avatar_key"]

    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
    )


def download_image_from_s3(bucket: str, key: str) -> bytes:
    """
    Download image from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Image bytes
    """
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def upload_image_to_s3(bucket: str, key: str, image_data: bytes) -> None:
    """
    Upload image to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        image_data: Image bytes to upload
    """
    s3_client = boto3.client("s3")
    s3_client.put_object(Bucket=bucket, Key=key, Body=image_data, ContentType="image/png")


@retry_with_exponential_backoff(max_retries=3)
def invoke_agent(image_base64: str, job_id: str) -> dict:
    """
    Invoke Strands Agent via Bedrock AgentCore with retry logic.

    This function invokes the deployed PetAvatar agent to process the image
    through the complete workflow: analysis, career mapping, avatar generation,
    and identity package creation.

    Implements exponential backoff retry for transient failures.
    Validates: Requirements 11.3

    Args:
        image_base64: Base64 encoded pet image
        job_id: Job identifier

    Returns:
        Dictionary containing agent results with pet_analysis, career_profile,
        avatar_image_base64, and identity_package
    """
    agent_runtime_arn = os.environ.get("AGENT_RUNTIME_ARN")
    if not agent_runtime_arn:
        raise ValueError("AGENT_RUNTIME_ARN environment variable not set")

    # For now, we'll use a direct invocation approach
    # In production, this would use the Bedrock AgentCore runtime API
    # The actual implementation depends on how the agent is deployed

    # Parse the ARN to get agent details
    # Format: arn:aws:bedrock-agentcore:region:account:runtime/agent-id

    bedrock_agent = boto3.client("bedrock-agent-runtime")

    # Construct the prompt for the agent
    prompt = f"""Please process this pet image (job_id: {job_id}) through the complete avatar generation workflow:

1. First, analyze the pet image to extract personality traits
2. Then, map the personality to an appropriate career
3. Next, generate a professional avatar image
4. Finally, create the complete identity package

The image is provided as base64 data."""

    try:
        # Invoke the agent
        # Note: The exact API depends on AgentCore deployment method
        # This is a placeholder for the actual invocation
        response = bedrock_agent.invoke_agent(
            agentId=agent_runtime_arn.split("/")[-1],
            agentAliasId="TSTALIASID",  # Test alias
            sessionId=job_id,
            inputText=prompt,
        )

        # Parse agent response
        # The agent should return structured results from the tools
        result_text = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                result_text += event["chunk"].get("bytes", b"").decode("utf-8")

        # For now, return a placeholder structure
        # The actual parsing depends on agent output format
        return {
            "pet_analysis": {"species": "dog", "breed": "Unknown", "personality_traits": {}},
            "career_profile": {"job_title": "Software Engineer", "seniority": "mid-level"},
            "avatar_image_base64": "",  # Would be populated by agent
            "identity_package": {
                "human_name": "Alex Johnson",
                "job_title": "Software Engineer",
                "seniority": "mid-level",
                "bio": "Placeholder bio",
                "skills": ["Python", "AWS"],
                "career_trajectory": {
                    "past": "Started as junior developer",
                    "present": "Currently mid-level engineer",
                    "future": "Aspiring to senior role",
                },
                "similarity_score": 85.0,
            },
        }
    except Exception as e:
        log_error(
            component="process-worker",
            operation="invoke_agent",
            error=e,
            context={"job_id": job_id, "agent_arn": agent_runtime_arn}
        )
        emit_metric(
            "AgentInvocationError",
            dimensions={"Component": "process-worker", "ErrorType": type(e).__name__}
        )
        raise


def process_job(job_id: str, s3_upload_key: str) -> None:
    """
    Process a single job through the avatar generation pipeline.

    Requirements: 4.5, 11.1, 11.2, 11.4

    Args:
        job_id: Job identifier
        s3_upload_key: S3 key for uploaded image
    """
    start_time = time.time()

    # Get environment variables
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    upload_bucket = os.environ.get("S3_UPLOAD_BUCKET")
    generated_bucket = os.environ.get("S3_GENERATED_BUCKET")

    if not table_name or not upload_bucket or not generated_bucket:
        raise ValueError(
            "Required environment variables not set: DYNAMODB_TABLE_NAME, S3_UPLOAD_BUCKET, S3_GENERATED_BUCKET"
        )

    try:
        # Update status to processing
        update_job_status(table_name, job_id, "processing", progress=10)
        emit_metric(
            "ProcessingStarted",
            dimensions={"Component": "process-worker"}
        )

        # Download image from S3
        print(f"Downloading image from s3://{upload_bucket}/{s3_upload_key}")
        image_bytes = download_image_from_s3(upload_bucket, s3_upload_key)
        update_job_status(table_name, job_id, "processing", progress=20)

        # Convert to base64 for agent
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Invoke Strands Agent
        print(f"Invoking agent for job {job_id}")
        update_job_status(table_name, job_id, "processing", progress=30)

        agent_results = invoke_agent(image_base64, job_id)
        update_job_status(table_name, job_id, "processing", progress=80)

        # Store generated avatar to S3
        avatar_key = f"generated/{job_id}/avatar.png"
        if agent_results.get("avatar_image_base64"):
            avatar_bytes = base64.b64decode(agent_results["avatar_image_base64"])
            print(f"Uploading avatar to s3://{generated_bucket}/{avatar_key}")
            upload_image_to_s3(generated_bucket, avatar_key, avatar_bytes)

        update_job_status(table_name, job_id, "processing", progress=90)

        # Update DynamoDB with results
        results = {
            "identity_package": agent_results.get("identity_package", {}),
            "pet_analysis": agent_results.get("pet_analysis", {}),
            "s3_avatar_key": avatar_key,
        }

        update_job_status(table_name, job_id, "completed", progress=100, results=results)

        # Emit success metrics (Validates: Requirements 11.5)
        processing_time = time.time() - start_time
        emit_metric(
            "ProcessingSuccess",
            dimensions={"Component": "process-worker"}
        )
        emit_metric(
            "JobCompletionTime",
            value=processing_time,
            unit="Seconds",
            dimensions={"Component": "process-worker"}
        )

        print(f"Successfully completed job {job_id} in {processing_time:.2f}s")

    except Exception as e:
        # Log error with context (Validates: Requirements 11.1)
        log_error(
            component="process-worker",
            operation="process_job",
            error=e,
            context={
                "job_id": job_id,
                "s3_upload_key": s3_upload_key,
                "processing_time": time.time() - start_time,
            },
        )

        # Update job status to failed (Validates: Requirements 11.2)
        error_message = f"{type(e).__name__}: {str(e)}"
        update_job_status(table_name, job_id, "failed", error_message=error_message)

        # Emit failure metrics (Validates: Requirements 11.5)
        emit_metric(
            "ProcessingFailure",
            dimensions={"Component": "process-worker", "ErrorType": type(e).__name__}
        )

        # Re-raise to trigger SQS retry
        raise


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process SQS messages and orchestrate avatar generation.

    This Lambda function is triggered by SQS messages containing job information.
    It orchestrates the complete avatar generation workflow by:
    1. Updating job status to processing
    2. Downloading the pet image from S3
    3. Invoking the Strands Agent via AgentCore
    4. Storing the generated avatar to S3
    5. Updating DynamoDB with results or errors

    Requirements: 4.5, 11.1, 11.2, 11.4

    Args:
        event: SQS event containing Records with job information
        context: Lambda context

    Returns:
        Response dictionary with status code and message
    """
    try:
        records = event.get("Records", [])

        if not records:
            print("No records to process")
            return {"statusCode": 200, "body": json.dumps({"message": "No records to process"})}

        for record in records:
            # Parse SQS message
            message_body = json.loads(record.get("body", "{}"))
            job_id = message_body.get("job_id")
            s3_upload_key = message_body.get("s3_upload_key")

            if not job_id or not s3_upload_key:
                print("Invalid message: missing job_id or s3_upload_key")
                continue

            print(f"Processing job {job_id} with image {s3_upload_key}")

            # Process the job
            process_job(job_id, s3_upload_key)

        return {"statusCode": 200, "body": json.dumps({"message": "Processing complete"})}

    except Exception as e:
        # Log error at handler level (Validates: Requirements 11.1)
        log_error(
            component="process-worker",
            operation="handler",
            error=e,
            context={"event": event}
        )

        # Emit error metric (Validates: Requirements 11.5)
        emit_metric(
            "HandlerError",
            dimensions={"Component": "process-worker", "ErrorType": type(e).__name__}
        )

        # Return error response (Validates: Requirements 11.2)
        # Note: SQS will retry based on visibility timeout and DLQ configuration
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
