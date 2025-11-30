"""
Tool for analyzing pet images using Claude Vision.

This tool uses Amazon Bedrock's Claude 3.5 Sonnet model to analyze pet photos
and extract personality traits, species, breed, and other characteristics.
"""

import json
import time
import boto3
from typing import Any
from strands import tool


def retry_with_exponential_backoff(func, max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: If all retries are exhausted
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay: {str(e)}")
            time.sleep(delay)


@tool
def analyze_pet_image(image_base64: str) -> dict:
    """
    Analyzes a pet image to extract personality traits and characteristics.
    
    Uses Claude 3.5 Sonnet vision capabilities to analyze the pet's appearance,
    expression, posture, and infer personality dimensions.
    
    Args:
        image_base64: Base64 encoded pet image (JPEG, PNG, or HEIC)
        
    Returns:
        Dictionary containing:
        - species: Animal species (dog, cat, hamster, fish, reptile, other)
        - breed: Breed characteristics when applicable
        - expression: Facial expression description
        - posture: Body posture description
        - personality_dimensions: Dict of 47 personality traits (0-100 scores)
        - dominant_traits: List of top 3-5 dominant personality traits
        - vibe: Overall personality vibe (e.g., "CFO energy", "friendly helper")
    """
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Comprehensive prompt for personality analysis
    analysis_prompt = """Analyze this pet image in detail and provide a comprehensive personality assessment.

Please provide your analysis in the following JSON format:

{
    "species": "<dog|cat|hamster|fish|reptile|other>",
    "breed": "<breed name or 'mixed' or 'unknown'>",
    "expression": "<description of facial expression>",
    "posture": "<description of body posture and positioning>",
    "personality_dimensions": {
        "confidence": <0-100>,
        "energy_level": <0-100>,
        "sociability": <0-100>,
        "assertiveness": <0-100>,
        "playfulness": <0-100>,
        "independence": <0-100>,
        "curiosity": <0-100>,
        "affection": <0-100>,
        "patience": <0-100>,
        "adaptability": <0-100>,
        "intelligence": <0-100>,
        "loyalty": <0-100>,
        "protectiveness": <0-100>,
        "gentleness": <0-100>,
        "boldness": <0-100>,
        "calmness": <0-100>,
        "enthusiasm": <0-100>,
        "focus": <0-100>,
        "determination": <0-100>,
        "sensitivity": <0-100>,
        "humor": <0-100>,
        "dignity": <0-100>,
        "mischievousness": <0-100>,
        "responsibility": <0-100>,
        "leadership": <0-100>,
        "cooperation": <0-100>,
        "competitiveness": <0-100>,
        "creativity": <0-100>,
        "organization": <0-100>,
        "spontaneity": <0-100>,
        "caution": <0-100>,
        "optimism": <0-100>,
        "resilience": <0-100>,
        "empathy": <0-100>,
        "assertive_communication": <0-100>,
        "listening_skills": <0-100>,
        "problem_solving": <0-100>,
        "strategic_thinking": <0-100>,
        "attention_to_detail": <0-100>,
        "big_picture_thinking": <0-100>,
        "risk_taking": <0-100>,
        "stability_seeking": <0-100>,
        "innovation": <0-100>,
        "tradition": <0-100>,
        "ambition": <0-100>,
        "contentment": <0-100>,
        "would_steal_lunch": <0-100>,
        "sends_passive_aggressive_emails": <0-100>
    },
    "dominant_traits": ["<trait1>", "<trait2>", "<trait3>"],
    "vibe": "<overall personality description in 2-4 words>"
}

Be creative but realistic in your assessment. Consider the pet's expression, posture, grooming, and overall demeanor."""

    def make_bedrock_call():
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": analysis_prompt
                        }
                    ]
                }]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Extract JSON from response (Claude might wrap it in markdown)
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        return json.loads(content)
    
    # Call Bedrock with retry logic
    result = retry_with_exponential_backoff(make_bedrock_call)
    
    return result
