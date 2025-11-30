"""
Error handling utilities for PetAvatar system.

This module provides utilities for retry logic, structured error logging,
and CloudWatch metrics emission.
"""

import time
import logging
import json
from datetime import datetime
from typing import Callable, Any, Optional, Dict
from functools import wraps
import boto3
from botocore.exceptions import ClientError


# Configure structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# CloudWatch client for metrics
cloudwatch = boto3.client("cloudwatch")


def retry_with_exponential_backoff(
    func: Optional[Callable] = None,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: int = 2,
) -> Any:
    """
    Retry a function with exponential backoff.

    Can be used as a decorator or called directly with a function.
    Implements exponential backoff with delays: 1s, 2s, 4s (by default).

    Args:
        func: Function to retry (when used as decorator)
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 60.0)
        exponential_base: Base for exponential calculation (default: 2)

    Returns:
        Decorated function or decorator

    Example:
        @retry_with_exponential_backoff(max_retries=3)
        def call_bedrock_api():
            return bedrock.invoke_model(...)

        # Or use directly:
        result = retry_with_exponential_backoff(
            lambda: bedrock.invoke_model(...),
            max_retries=3
        )

    Validates: Requirements 11.3
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Don't retry on the last attempt
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Function {f.__name__} failed after {max_retries} attempts",
                            extra={
                                "function": f.__name__,
                                "attempts": max_retries,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {f.__name__}, "
                        f"retrying in {delay}s",
                        extra={
                            "function": f.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "delay": delay,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )

                    time.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry failed without exception")

        return wrapper

    # Support both @decorator and @decorator() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_error(
    component: str,
    operation: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR,
) -> None:
    """
    Log error with structured context for debugging and monitoring.

    Creates a structured log entry with component name, operation,
    error details, and additional context. This enables better
    debugging and monitoring in CloudWatch Logs.

    Args:
        component: Name of the component where error occurred
                  (e.g., "upload-handler", "pet-analysis-tool")
        operation: Operation being performed when error occurred
                  (e.g., "validate_image", "invoke_bedrock")
        error: The exception that was raised
        context: Additional context information (job_id, user_id, etc.)
        level: Logging level (default: logging.ERROR)

    Example:
        try:
            result = bedrock.invoke_model(...)
        except ClientError as e:
            log_error(
                component="analyze-pet-tool",
                operation="invoke_bedrock_vision",
                error=e,
                context={
                    "job_id": job_id,
                    "model_id": "anthropic.claude-3-5-sonnet",
                    "image_size": len(image_data)
                }
            )
            raise

    Validates: Requirements 11.1
    """
    if context is None:
        context = {}

    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "component": component,
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
    }

    # Add additional error details for AWS ClientError
    if isinstance(error, ClientError):
        log_data["aws_error_code"] = error.response.get("Error", {}).get("Code")
        log_data["aws_request_id"] = error.response.get("ResponseMetadata", {}).get(
            "RequestId"
        )

    logger.log(level, json.dumps(log_data))


def emit_metric(
    metric_name: str,
    value: float = 1.0,
    unit: str = "Count",
    dimensions: Optional[Dict[str, str]] = None,
    namespace: str = "PetAvatar",
) -> None:
    """
    Emit CloudWatch metric for monitoring and alerting.

    Sends custom metrics to CloudWatch for tracking system health,
    performance, and business metrics.

    Args:
        metric_name: Name of the metric (e.g., "UploadSuccess", "ProcessingFailure")
        value: Metric value (default: 1.0)
        unit: CloudWatch unit type (default: 'Count')
              Valid units: Count, Seconds, Milliseconds, Bytes, etc.
        dimensions: Additional dimensions for filtering
                   (e.g., {"Component": "upload-handler", "Status": "success"})
        namespace: CloudWatch namespace (default: 'PetAvatar')

    Example:
        # Track successful uploads
        emit_metric("UploadSuccess", dimensions={"Component": "upload-handler"})

        # Track processing time
        emit_metric(
            "ProcessingTime",
            value=45.2,
            unit="Seconds",
            dimensions={"Component": "process-worker"}
        )

        # Track errors
        emit_metric(
            "BedrockAPIError",
            dimensions={"Component": "pet-analysis", "ErrorType": "ThrottlingException"}
        )

    Validates: Requirements 11.5
    """
    try:
        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Timestamp": datetime.utcnow(),
        }

        # Add dimensions if provided
        if dimensions:
            metric_data["Dimensions"] = [
                {"Name": key, "Value": value} for key, value in dimensions.items()
            ]

        cloudwatch.put_metric_data(Namespace=namespace, MetricData=[metric_data])

        logger.debug(
            f"Emitted metric: {namespace}/{metric_name}={value}",
            extra={
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "dimensions": dimensions,
            },
        )
    except Exception as e:
        # Don't fail the operation if metric emission fails
        logger.warning(
            f"Failed to emit metric {metric_name}: {str(e)}",
            extra={
                "metric_name": metric_name,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


def create_error_response(
    status_code: int,
    error_message: str,
    error_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create standardized error response for API handlers.

    Generates consistent error response format across all Lambda handlers
    for better client error handling.

    Args:
        status_code: HTTP status code (400, 401, 404, 500, etc.)
        error_message: Human-readable error message
        error_type: Error type identifier (e.g., "ValidationError", "NotFoundError")
        details: Additional error details

    Returns:
        Dictionary with statusCode, headers, and body for Lambda response

    Example:
        return create_error_response(
            status_code=400,
            error_message="Invalid image format. Supported formats: JPEG, PNG, HEIC",
            error_type="ValidationError",
            details={"format": "gif", "supported": ["jpeg", "png", "heic"]}
        )

    Validates: Requirements 11.2
    """
    error_body: Dict[str, Any] = {
        "error": error_message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if error_type:
        error_body["error_type"] = error_type

    if details:
        error_body["details"] = details

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,x-api-key",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(error_body),
    }


def handle_lambda_errors(func: Callable) -> Callable:
    """
    Decorator to wrap Lambda handlers with standardized error handling.

    Catches exceptions, logs them with context, emits metrics,
    and returns appropriate HTTP error responses.

    Args:
        func: Lambda handler function to wrap

    Returns:
        Wrapped handler with error handling

    Example:
        @handle_lambda_errors
        def lambda_handler(event, context):
            # Handler logic
            return {
                'statusCode': 200,
                'body': json.dumps({'result': 'success'})
            }

    Validates: Requirements 11.1, 11.2, 11.5
    """

    @wraps(func)
    def wrapper(event, context):
        component = context.function_name if context else "unknown"

        try:
            return func(event, context)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            log_error(
                component=component,
                operation=func.__name__,
                error=e,
                context={
                    "event": event,
                    "aws_error_code": error_code,
                    "request_id": context.aws_request_id if context else None,
                },
            )

            emit_metric(
                "LambdaError",
                dimensions={
                    "Component": component,
                    "ErrorType": "ClientError",
                    "ErrorCode": error_code,
                },
            )

            # Map AWS errors to HTTP status codes
            status_code = 500
            if error_code in ["AccessDenied", "UnauthorizedException"]:
                status_code = 403
            elif error_code in ["ResourceNotFoundException", "NoSuchKey"]:
                status_code = 404
            elif error_code in ["ThrottlingException", "TooManyRequestsException"]:
                status_code = 429

            return create_error_response(
                status_code=status_code,
                error_message=f"AWS service error: {error_code}",
                error_type="AWSError",
                details={"error_code": error_code},
            )

        except ValueError as e:
            log_error(
                component=component,
                operation=func.__name__,
                error=e,
                context={
                    "event": event,
                    "request_id": context.aws_request_id if context else None,
                },
            )

            emit_metric(
                "LambdaError",
                dimensions={"Component": component, "ErrorType": "ValueError"},
            )

            return create_error_response(
                status_code=400, error_message=str(e), error_type="ValidationError"
            )

        except Exception as e:
            log_error(
                component=component,
                operation=func.__name__,
                error=e,
                context={
                    "event": event,
                    "request_id": context.aws_request_id if context else None,
                },
                level=logging.CRITICAL,
            )

            emit_metric(
                "LambdaError",
                dimensions={"Component": component, "ErrorType": type(e).__name__},
            )

            return create_error_response(
                status_code=500,
                error_message="Internal server error",
                error_type="InternalError",
            )

    return wrapper
