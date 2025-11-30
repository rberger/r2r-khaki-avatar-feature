"""
PetAvatar Agent - Main orchestration for pet-to-human avatar transformation.

This agent coordinates the multi-step workflow of analyzing pet images,
mapping personality to careers, generating avatars, and creating complete
professional identity packages.
"""

from strands import Agent
from strands.models.bedrock import BedrockModel
from tools import (
    analyze_pet_image,
    map_personality_to_career,
    generate_avatar_image,
    generate_identity_package,
)


# System prompt for the agent
SYSTEM_PROMPT = """You are an AI assistant that transforms pet photos into professional human avatars with complete career identities.

Your workflow is:
1. Analyze the pet image to extract personality traits, species, breed, and characteristics
2. Map those personality traits to an appropriate human profession and career profile
3. Generate a photorealistic human avatar that matches the career profile
4. Create a complete professional identity package including name, bio, skills, and career trajectory

Be creative but believable. The goal is to capture the pet's essence in human form while creating a coherent professional identity.

Important guidelines:
- Always follow the workflow in order
- Use the personality analysis to inform career selection
- Ensure the avatar matches the career profile (attire, setting, etc.)
- Make the identity package feel authentic and professional
- The similarity score should reflect how well the pet's personality translates to the human identity

When you receive an image and job_id, execute all four steps and return the complete results."""


# Create the agent with Bedrock Claude model
agent = Agent(
    model=BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0", region_name="us-east-1"
    ),
    tools=[
        analyze_pet_image,
        map_personality_to_career,
        generate_avatar_image,
        generate_identity_package,
    ],
    system_prompt=SYSTEM_PROMPT,
)


def process_pet_avatar(image_base64: str, job_id: str) -> dict:
    """
    Process a pet image through the complete avatar generation workflow.

    This is the main entry point for the agent. It orchestrates the entire
    workflow from pet analysis to final identity package generation.

    Args:
        image_base64: Base64 encoded pet image
        job_id: Unique job identifier for tracking

    Returns:
        Dictionary containing:
        - pet_analysis: Complete personality analysis
        - career_profile: Mapped career information
        - avatar_image_base64: Generated avatar image
        - identity_package: Complete professional identity
        - job_id: The job identifier
    """
    # Invoke the agent with the image and job context
    user_message = f"""Please process this pet image (job_id: {job_id}) through the complete avatar generation workflow:

1. First, analyze the pet image to extract personality traits
2. Then, map the personality to an appropriate career
3. Next, generate a professional avatar image
4. Finally, create the complete identity package

The image data is: {image_base64[:100]}... (truncated for display)

Please execute all steps and provide the complete results."""

    # Run the agent
    result = agent(user_message)

    # The agent will have used the tools and stored results in its context
    # Extract the results from the agent's execution
    # Note: This is a simplified version - actual implementation may need
    # to parse the agent's response or access tool results differently

    return {"job_id": job_id, "status": "completed", "response": str(result)}


# For AgentCore deployment, we need an entrypoint
# This will be configured when deploying with bedrock-agentcore-starter-toolkit
if __name__ == "__main__":
    # Example usage for local testing
    import sys
    import base64

    if len(sys.argv) > 1:
        # Load image from file
        with open(sys.argv[1], "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        result = process_pet_avatar(image_data, "test-job-123")
        print(result)
    else:
        print("Usage: python agent.py <image_file>")
        print("Example: python agent.py test_pet.jpg")
