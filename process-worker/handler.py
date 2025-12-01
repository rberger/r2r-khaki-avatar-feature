"""
Process Worker
Orchestrates avatar generation via Strands Agent.
"""
import json
import os
import base64
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

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


def emit_metric(metric_name: str, value: float = 1.0, unit: str = "Count", dimensions: dict = None) -> None:
    """Emit CloudWatch metric."""
    try:
        cloudwatch = boto3.client('cloudwatch')
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.now(timezone.utc)
        }
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        cloudwatch.put_metric_data(Namespace='PetAvatar', MetricData=[metric_data])
    except Exception:
        pass


def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        return wrapper
    return decorator


def update_job_status(
    table_name: str,
    job_id: str,
    status: str,
    progress: Optional[int] = None,
    error_message: Optional[str] = None,
    results: Optional[dict] = None,
) -> None:
    """Update job status in DynamoDB."""
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
    """Download image from S3."""
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def upload_image_to_s3(bucket: str, key: str, image_data: bytes) -> None:
    """Upload image to S3."""
    s3_client = boto3.client("s3")
    s3_client.put_object(Bucket=bucket, Key=key, Body=image_data, ContentType="image/png")


def generate_mock_results(job_id: str) -> dict:
    """Generate mock results for testing (until AgentCore is deployed)."""
    return {
        "pet_analysis": {
            "species": "dog",
            "breed": "Golden Retriever",
            "expression": "friendly",
            "personality_traits": {
                "confidence": 85,
                "energy_level": 72,
                "sociability": 95,
                "playfulness": 88
            }
        },
        "identity_package": {
            "human_name": "Greg Thompson",
            "job_title": "Senior Product Manager",
            "seniority": "senior",
            "bio": "Greg is a seasoned product leader with a natural ability to bring teams together. His friendly demeanor and high energy make him a favorite among colleagues. He excels at understanding customer needs and translating them into actionable product strategies.",
            "skills": ["Product Strategy", "Team Leadership", "Customer Research", "Agile Methodologies", "Stakeholder Management"],
            "career_trajectory": {
                "past": "Started as a customer success representative, quickly moving into product roles",
                "present": "Currently leading a team of 8 product managers at a growing tech company",
                "future": "Aspiring to become VP of Product within the next 3 years"
            },
            "similarity_score": 87.5
        },
        "avatar_image_base64": ""  # Would be generated by Titan
    }


def process_job(job_id: str, s3_upload_key: str) -> None:
    """Process a single job through the avatar generation pipeline."""
    start_time = time.time()

    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    upload_bucket = os.environ.get("S3_UPLOAD_BUCKET")
    generated_bucket = os.environ.get("S3_GENERATED_BUCKET")

    if not table_name or not upload_bucket or not generated_bucket:
        raise ValueError("Required environment variables not set")

    try:
        update_job_status(table_name, job_id, "processing", progress=10)

        # Download image from S3
        print(f"Downloading image from s3://{upload_bucket}/{s3_upload_key}")
        image_bytes = download_image_from_s3(upload_bucket, s3_upload_key)
        update_job_status(table_name, job_id, "processing", progress=30)

        # For now, use mock results until AgentCore is deployed
        # TODO: Replace with actual agent invocation
        print(f"Generating results for job {job_id}")
        agent_results = generate_mock_results(job_id)
        update_job_status(table_name, job_id, "processing", progress=80)

        # Store avatar key (even if empty for now)
        avatar_key = f"generated/{job_id}/avatar.png"
        
        # Create a placeholder avatar (1x1 PNG)
        placeholder_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        upload_image_to_s3(generated_bucket, avatar_key, placeholder_png)
        update_job_status(table_name, job_id, "processing", progress=90)

        results = {
            "identity_package": agent_results.get("identity_package", {}),
            "pet_analysis": agent_results.get("pet_analysis", {}),
            "s3_avatar_key": avatar_key,
        }

        update_job_status(table_name, job_id, "completed", progress=100, results=results)

        processing_time = time.time() - start_time
        print(f"Successfully completed job {job_id} in {processing_time:.2f}s")

    except Exception as e:
        log_error("process-worker", "process_job", e, {"job_id": job_id})
        error_message = f"{type(e).__name__}: {str(e)}"
        update_job_status(table_name, job_id, "failed", error_message=error_message)
        raise


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process SQS messages and orchestrate avatar generation."""
    try:
        records = event.get("Records", [])

        if not records:
            return {"statusCode": 200, "body": json.dumps({"message": "No records"})}

        for record in records:
            message_body = json.loads(record.get("body", "{}"))
            job_id = message_body.get("job_id")
            s3_upload_key = message_body.get("s3_upload_key")

            if not job_id or not s3_upload_key:
                continue

            print(f"Processing job {job_id}")
            process_job(job_id, s3_upload_key)

        return {"statusCode": 200, "body": json.dumps({"message": "Done"})}

    except Exception as e:
        log_error("process-worker", "handler", e, {})
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
