# PetAvatar Agent

AI agent for transforming pet photos into professional human avatars with complete career identities.

## Overview

This agent uses Amazon Bedrock's Claude 3.5 Sonnet and Titan Image Generator to:
1. Analyze pet personality traits from photos
2. Map personality to appropriate human careers
3. Generate photorealistic professional avatars
4. Create complete identity packages (name, bio, skills, career trajectory)

## Project Structure

```
petavatar-agent/
├── agent.py              # Main agent orchestration with AgentCore entrypoint
├── tools/                # Agent tools
│   ├── __init__.py
│   ├── analyze_pet.py    # Pet personality analysis
│   ├── map_career.py     # Personality-to-career mapping
│   ├── generate_avatar.py # Avatar image generation
│   └── generate_identity.py # Identity package creation
├── scripts/
│   └── deploy-agentcore.sh # Deployment script for AgentCore
├── pyproject.toml        # Project dependencies (uv)
└── README.md            # This file
```

## Dependencies

- Python 3.13+
- strands-agents
- boto3 (AWS SDK)
- pillow (image processing)

## Installation

Using `uv` (recommended):

```bash
cd petavatar-agent
uv sync
```

## Usage

### Local Testing

```bash
python agent.py path/to/pet_image.jpg
```

### As a Module

```python
from agent import process_pet_avatar
import base64

# Load and encode image
with open('pet.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# Process the image
result = process_pet_avatar(image_base64, job_id="unique-job-id")
print(result)
```

### Deployment to AgentCore

This agent is designed to be deployed to AWS Bedrock AgentCore Runtime.

#### Prerequisites

- AWS CLI configured with appropriate credentials and permissions
- uv package manager installed
- bedrock-agentcore-starter-toolkit installed

```bash
pip install bedrock-agentcore-starter-toolkit
```

#### Using the Deployment Script (Recommended)

```bash
cd petavatar-agent

# Deploy to AWS AgentCore
./scripts/deploy-agentcore.sh

# Or test locally first (requires Docker/Finch/Podman)
./scripts/deploy-agentcore.sh --local
```

The script will:
1. Generate requirements.txt from pyproject.toml using uv
2. Configure the agent with agentcore
3. Deploy to AWS (or run locally with --local flag)
4. Display the Agent Runtime ARN
5. Clean up the generated requirements.txt

#### Manual Deployment

```bash
cd petavatar-agent

# Generate requirements.txt from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt

# Configure the agent
agentcore configure --entrypoint agent.py

# Optional: Test locally (requires container engine)
agentcore launch --local

# Deploy to AWS
agentcore launch

# Test the deployed agent
agentcore invoke '{"image_base64": "<base64_image>", "job_id": "test-123"}'

# Clean up
rm requirements.txt
```

#### Capturing the Agent ARN

After deployment, the Agent Runtime ARN will be displayed. Save this ARN - it's needed to configure the `AGENT_RUNTIME_ARN` environment variable for the process-worker Lambda function.

Example ARN format:
```
arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/petavatar-agent-xxxxx
```

## Tools

### analyze_pet_image

Analyzes pet photos using Claude Vision to extract:
- Species and breed
- Expression and posture
- 47 personality dimensions (0-100 scores)
- Dominant traits and overall vibe

### map_personality_to_career

Maps personality traits to human careers:
- Job title and seniority level
- Industry and work style
- Attire and background settings
- Confidence score for the match

### generate_avatar_image

Creates photorealistic avatars using Titan:
- Professional headshot style
- Appropriate attire for career
- Suitable background setting
- 1024x1024 PNG format

### generate_identity_package

Generates complete professional identity:
- Species-appropriate human name
- 3-paragraph LinkedIn-style bio
- 5-10 professional skills
- Career trajectory (past, present, future)
- Similarity score (0-100)

## AWS Permissions Required

The agent needs the following AWS permissions:
- `bedrock:InvokeModel` for Claude and Titan models
- CloudWatch Logs access for logging

## Error Handling

All Bedrock API calls include:
- Exponential backoff retry logic (3 attempts)
- Delays: 1s, 2s, 4s between retries
- Comprehensive error logging

## Testing

Run tests with pytest:

```bash
pytest tests/
```

Property-based tests use Hypothesis with 100 iterations per property.

## Environment Variables

- `AWS_REGION`: AWS region for Bedrock (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use (optional)

## License

Proprietary - Part of the PetAvatar system
