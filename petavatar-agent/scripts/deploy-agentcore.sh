#!/bin/bash
# Deploy PetAvatar Agent to AWS Bedrock AgentCore Runtime
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - uv package manager installed
#   - bedrock-agentcore-starter-toolkit installed (pip install bedrock-agentcore-starter-toolkit)
#
# Usage:
#   ./scripts/deploy-agentcore.sh [--local]
#
# Options:
#   --local    Test locally before deploying (requires Docker/Finch/Podman)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== PetAvatar Agent Deployment to AgentCore ==="
echo "Agent directory: $AGENT_DIR"

cd "$AGENT_DIR"

# Step 1: Generate requirements.txt from pyproject.toml using uv
echo ""
echo "Step 1: Generating requirements.txt from pyproject.toml..."
uv pip compile pyproject.toml -o requirements.txt --quiet
echo "Generated requirements.txt"

# Step 2: Configure the agent with agentcore
echo ""
echo "Step 2: Configuring agent with agentcore..."
agentcore configure --entrypoint agent.py

# Step 3: Deploy based on argument
if [[ "$1" == "--local" ]]; then
    echo ""
    echo "Step 3: Testing locally (requires container engine)..."
    agentcore launch --local
else
    echo ""
    echo "Step 3: Deploying to AWS AgentCore Runtime..."
    agentcore launch
    
    echo ""
    echo "Step 4: Capturing Agent ARN..."
    echo "The Agent Runtime ARN will be displayed above."
    echo "Save this ARN for configuring the process-worker Lambda."
    echo ""
    echo "To test the deployed agent:"
    echo "  agentcore invoke '{\"image_base64\": \"<base64_image>\", \"job_id\": \"test-123\"}'"
fi

# Step 5: Clean up generated requirements.txt
echo ""
echo "Step 5: Cleaning up generated requirements.txt..."
rm -f requirements.txt
echo "Cleanup complete"

echo ""
echo "=== Deployment Complete ==="
