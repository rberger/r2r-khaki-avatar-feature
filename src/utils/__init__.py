"""
Utility modules for PetAvatar system.
"""

from .error_handling import (
    retry_with_exponential_backoff,
    log_error,
    emit_metric,
    create_error_response,
    handle_lambda_errors
)

__all__ = [
    'retry_with_exponential_backoff',
    'log_error',
    'emit_metric',
    'create_error_response',
    'handle_lambda_errors'
]
