---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---

## Code Style

- Follow PEP 8 style guide with 88-character line length (Black formatter standard)
- Use snake_case for variables, functions, and module names
- Use PascalCase for classes
- Use UPPER_SNAKE_CASE for constants
- Prefer descriptive names over abbreviations (e.g., `process_request` not `proc_req`)
- Use docstrings for all public functions, classes, and modules (Google or NumPy style)

## Type Hints

- Always use type hints for function parameters and return values
- Import from `typing` module: `Optional`, `Union`, `Dict`, `List`, `Tuple`, `Any`
- Use `Optional[T]` for nullable values, not `Union[T, None]`
- Use `dict[str, Any]` for Python 3.9+ or `Dict[str, Any]` for older versions
- Type hint lambda handler signatures: `def handler(event: dict, context: Any) -> dict:`
- Use `TypedDict` for structured dictionaries with known keys

## Error Handling

- Use specific exception types, never bare `except:`
- Create custom exceptions for domain-specific errors
- Use context managers (`with` statements) for file I/O and resource management
- Log exceptions with context: `logger.exception("Failed to process", extra={"request_id": id})`
- Return structured error responses in Lambda handlers with status codes
- Validate inputs early and fail fast with clear error messages

## Lambda Function Patterns

- Structure handlers with clear separation: validation → processing → response
- Return consistent response format: `{"statusCode": int, "body": str, "headers": dict}`
- Use environment variables for configuration, never hardcode values
- Keep handlers thin, delegate business logic to separate modules
- Handle AWS SDK exceptions specifically (e.g., `ClientError`, `BotoCoreError`)
- Use boto3 clients efficiently, reuse outside handler when possible
- Set appropriate timeouts and implement retry logic for external calls

## Dependency Management

- Use `uv` with `pyproject.toml` for dependency management (preferred)
- Fallback to `poetry` with `pyproject.toml` if `uv` is unavailable
- NEVER use `requirements.txt` with raw `pip` for new projects
- Pin major versions, allow minor/patch updates: `package = "^1.2.3"`
- Separate dev dependencies from production dependencies
- Document any system-level dependencies in README

## Code Organization

- Organize Lambda functions in `functions/<function-name>/handler.py`
- Place shared utilities in `src/utils/` for reuse across functions
- Use `src/agent/` for agent-specific code and tools
- Keep `__init__.py` files minimal, use for package exports only
- One class per file for complex classes, related functions can share files
- Import order: stdlib → third-party → local (separated by blank lines)

## Strands Agents Patterns

- Define tools in separate files under `tools/` directory
- Use `@tool` decorator for tool functions with clear docstrings
- Return structured data from tools, not raw strings
- Use Pydantic models for tool inputs/outputs when appropriate
- Keep tool functions focused on single responsibilities
- Handle tool errors gracefully, return error states not exceptions
- Use async/await for I/O-bound operations in tools

## AWS SDK (boto3) Usage

- Import specific clients: `import boto3; s3 = boto3.client('s3')`
- Use resource-based exceptions: `from botocore.exceptions import ClientError`
- Implement exponential backoff for retries on throttling
- Use pagination for list operations: `paginator = client.get_paginator('list_objects_v2')`
- Close clients explicitly or use context managers when available
- Set explicit regions to avoid ambiguity: `boto3.client('s3', region_name='us-east-1')`

## Testing

- Write unit tests using pytest in `tests/` directory
- Name test files `test_<module>.py` to match source files
- Use descriptive test names: `test_handler_returns_error_when_missing_required_field`
- Mock AWS services with `moto` library for boto3 interactions
- Use pytest fixtures for common setup/teardown
- Run tests quietly: `pytest -q` or `pytest --tb=short -q`
- Filter tests during development: `pytest -k "test_specific_function"`
- Aim for 80%+ coverage on business logic, 100% on critical paths

## Logging

- Use Python's `logging` module, not `print()` statements
- Configure logging at module level: `logger = logging.getLogger(__name__)`
- Use appropriate levels: DEBUG for details, INFO for flow, WARNING for issues, ERROR for failures
- Include context in log messages: `logger.info("Processing request", extra={"user_id": uid})`
- In Lambda functions, logs automatically go to CloudWatch
- Use structured logging (JSON) for production environments

## Performance

- Use list comprehensions for simple transformations, generator expressions for large datasets
- Prefer `dict.get(key, default)` over try/except for missing keys
- Use `set` for membership testing, `dict` for lookups
- Cache expensive computations with `functools.lru_cache`
- Profile before optimizing: `python -m cProfile script.py`
- Use `asyncio` for concurrent I/O operations
- Batch AWS API calls when possible to reduce latency

## Security

- Never log sensitive data (passwords, tokens, PII)
- Validate and sanitize all external inputs
- Use IAM roles for AWS credentials, never hardcode keys
- Use environment variables for secrets, consider AWS Secrets Manager
- Implement least privilege principle for IAM permissions
- Use parameterized queries for database operations
- Sanitize file paths to prevent directory traversal attacks
