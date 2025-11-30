"""
Tool for generating photorealistic human avatars using Amazon Titan Image Generator.

This tool creates professional headshot images based on career profiles,
with appropriate attire and background settings.
"""

import json
import base64
import boto3
from typing import Any
from io import BytesIO
from PIL import Image
from strands import tool
from .analyze_pet import retry_with_exponential_backoff


@tool
def generate_avatar_image(career_profile: dict, personality_profile: dict, job_id: str = None) -> dict:
    """
    Generates a photorealistic human avatar image.
    
    Uses Amazon Titan Image Generator to create a professional headshot
    based on the career profile and personality traits.
    
    Args:
        career_profile: Output from map_personality_to_career containing:
            - job_title: Job title
            - seniority: Seniority level
            - attire_style: Clothing style
            - background_setting: Background type
        personality_profile: Output from analyze_pet_image for additional context
        job_id: Optional job ID for deterministic seed generation
        
    Returns:
        Dictionary containing:
        - image_base64: Base64 encoded PNG image (1024x1024)
        - prompt_used: The prompt sent to Titan
        - generation_params: Parameters used for generation
    """
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Build detailed prompt from career profile
    job_title = career_profile.get('job_title', 'Professional')
    seniority = career_profile.get('seniority', 'mid-level')
    attire = career_profile.get('attire_style', 'business_casual')
    background = career_profile.get('background_setting', 'linkedin_blue')
    
    # Map attire styles to descriptions
    attire_descriptions = {
        'suit': 'wearing a professional business suit',
        'business_casual': 'wearing business casual attire',
        'creative': 'wearing stylish creative professional clothing',
        'scrubs': 'wearing medical scrubs'
    }
    
    # Map background settings to descriptions
    background_descriptions = {
        'corner_office': 'in a corner office with windows and city view',
        'open_office': 'in a modern open office environment',
        'linkedin_blue': 'with a professional LinkedIn-style blue gradient background',
        'creative_space': 'in a creative workspace with modern design'
    }
    
    attire_desc = attire_descriptions.get(attire, 'wearing professional attire')
    background_desc = background_descriptions.get(background, 'with a professional background')
    
    # Construct the prompt
    prompt = (
        f"Professional headshot photograph of a {seniority} {job_title}, "
        f"{attire_desc}, {background_desc}, "
        f"photorealistic, high quality, professional photography, "
        f"well-lit, sharp focus, confident expression, "
        f"corporate portrait style, 8k resolution"
    )
    
    # Generate deterministic but unique seed from job_id if provided
    seed = hash(job_id) % (2**31) if job_id else 42
    
    generation_params = {
        "numberOfImages": 1,
        "quality": "premium",
        "cfgScale": 8.0,
        "height": 1024,
        "width": 1024,
        "seed": seed
    }
    
    def make_bedrock_call():
        response = bedrock.invoke_model(
            modelId='amazon.titan-image-generator-v1',
            body=json.dumps({
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt
                },
                "imageGenerationConfig": generation_params
            })
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract the base64 image from response
        image_base64 = response_body['images'][0]
        
        # Validate image format and dimensions
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))
        
        # Verify it's PNG and at least 1024x1024
        if image.format != 'PNG':
            raise ValueError(f"Expected PNG format, got {image.format}")
        
        width, height = image.size
        if width < 1024 or height < 1024:
            raise ValueError(f"Image dimensions {width}x{height} are below minimum 1024x1024")
        
        return {
            "image_base64": image_base64,
            "prompt_used": prompt,
            "generation_params": generation_params,
            "image_format": image.format,
            "image_dimensions": f"{width}x{height}"
        }
    
    # Call Bedrock with retry logic (up to 3 retries)
    result = retry_with_exponential_backoff(make_bedrock_call)
    
    return result
