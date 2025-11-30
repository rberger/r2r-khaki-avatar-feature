---
inclusion: fileMatch
fileMatchPattern: "*.py"
---

# Technology Stack

## Language & Runtime

- **Python**: 3.10+ (currently using 3.13)
- **Package Manager**: `uv` (Astral's fast Python package manager)
- **Build System**: Hatchling
- **Strands SDK** (`strands-agents`) - Main framework for building AI agents
- **Strands Tools** (`strands-agents-tools`) - Pre-built tools library (calculator, file operations, web search, etc.)

## Core Dependencies

- **Data Validation**: `pydantic>=2.10.6` - Type validation and settings management
- **AWS SDK**: `boto3` - AWS service integration
- **Logging**: `loguru>=0.7.0` - Structured logging
- **HTTP Client**: `httpx>=0.27.0` - Async HTTP requests
- **uv** - Fast Python package manager used in some samples

## AWS Integration

- **boto3/botocore** - AWS SDK for Python
- **Amazon Bedrock** - Primary LLM provider (Claude models)
- **Amazon DynamoDB** - NoSQL database for agent state
- **Amazon Bedrock Knowledge Bases** - RAG capabilities
- **AWS Lambda & Fargate** - Deployment targets

## Model Providers

- Amazon Bedrock (primary) - Claude Sonnet, Haiku models
- OpenAI - GPT-4 and other models
- Ollama - Local model execution

## Additional Technologies

- **MCP (Model Context Protocol)** - Tool integration standard
- **Jupyter Notebooks** - Interactive tutorials (.ipynb files)
- **CDK (Cloud Development Kit)** - Infrastructure as code (TypeScript/Python)
- **OpenTelemetry** - Observability and tracing
- **Streamlit** - UI demos
