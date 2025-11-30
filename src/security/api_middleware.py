"""
API Security Middleware

Provides decorators and utilities for API security:
- Requirements 6.6: API key validation
- CORS header management
- Request throttling support
"""
import json
import functools
from typing import Dict, Any, Callable, Optional, List
import logging

from .api_security import validate_api_key, create_unauthorized_response

logger = logging.getLogger(__name__)


# Standard CORS headers for all responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,x-api-key,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Expose-Headers': 'x-request-id',
    'Access-Control-Max-Age': '86400'  # 24 hours
}


def get_cors_headers(
    allowed_origins: Optional[List[str]] = None,
    allowed_methods: Optional[List[str]] = None,
    allowed_headers: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Get CORS headers with optional customization.
    
    Args:
        allowed_origins: List of allowed origins (default: ['*'])
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed headers
        
    Returns:
        Dictionary of CORS headers
    """
    headers = CORS_HEADERS.copy()
    
    if allowed_origins:
        headers['Access-Control-Allow-Origin'] = ','.join(allowed_origins)
    
    if allowed_methods:
        headers['Access-Control-Allow-Methods'] = ','.join(allowed_methods)
    
    if allowed_headers:
        headers['Access-Control-Allow-Headers'] = ','.join(allowed_headers)
    
    return headers


def handle_cors_preflight(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle CORS preflight (OPTIONS) requests.
    
    Args:
        event: Lambda event
        
    Returns:
        Response for OPTIONS request, or None if not a preflight
    """
    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
    
    if http_method.upper() == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    return None


def require_api_key(handler: Callable) -> Callable:
    """
    Decorator to require API key validation.
    
    Validates the x-api-key header and returns 401 if invalid.
    
    Requirement 6.6: Invalid API keys are rejected with 401 Unauthorized
    
    Usage:
        @require_api_key
        def handler(event, context):
            # API key is already validated
            ...
    """
    @functools.wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Handle CORS preflight
        preflight_response = handle_cors_preflight(event)
        if preflight_response:
            return preflight_response
        
        # Extract API key from headers (case-insensitive)
        headers = event.get('headers', {}) or {}
        api_key = headers.get('x-api-key') or headers.get('X-Api-Key')
        
        # Validate API key
        if not validate_api_key(api_key):
            logger.warning("API key validation failed for request")
            return create_unauthorized_response()
        
        # Call the actual handler
        response = handler(event, context)
        
        # Ensure CORS headers are present in response
        if isinstance(response, dict) and 'headers' in response:
            response['headers'] = {**get_cors_headers(), **response.get('headers', {})}
        elif isinstance(response, dict):
            response['headers'] = get_cors_headers()
        
        return response
    
    return wrapper


def add_security_headers(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add security headers to a response.
    
    Args:
        response: Lambda response dictionary
        
    Returns:
        Response with security headers added
    """
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'Pragma': 'no-cache'
    }
    
    if 'headers' not in response:
        response['headers'] = {}
    
    response['headers'].update(security_headers)
    
    return response


def create_api_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API response with security headers.
    
    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Additional headers
        
    Returns:
        Lambda response dictionary
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            **get_cors_headers(),
            **(headers or {})
        },
        'body': json.dumps(body) if not isinstance(body, str) else body
    }
    
    return add_security_headers(response)


def rate_limit_exceeded_response(
    retry_after: int = 60
) -> Dict[str, Any]:
    """
    Create a 429 Too Many Requests response.
    
    Args:
        retry_after: Seconds until client should retry
        
    Returns:
        Lambda response dictionary
    """
    return create_api_response(
        status_code=429,
        body={
            'error': 'TooManyRequests',
            'message': 'Rate limit exceeded. Please try again later.'
        },
        headers={
            'Retry-After': str(retry_after)
        }
    )
