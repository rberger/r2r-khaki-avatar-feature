"""
Tool for mapping pet personality traits to human career profiles.

This tool uses Claude to analyze personality dimensions and select appropriate
human professions, seniority levels, and work styles.
"""

import json
import boto3
from typing import Any
from strands import tool
from .analyze_pet import retry_with_exponential_backoff


@tool
def map_personality_to_career(personality_profile: dict) -> dict:
    """
    Maps pet personality traits to human career profile.
    
    Analyzes the 47 personality dimensions to determine the most appropriate
    human profession, seniority level, work style, and professional presentation.
    
    Args:
        personality_profile: Output from analyze_pet_image containing:
            - species: Animal species
            - personality_dimensions: Dict of 47 traits (0-100 scores)
            - dominant_traits: List of top traits
            - vibe: Overall personality description
        
    Returns:
        Dictionary containing:
        - job_title: Specific job title (e.g., "Senior Product Manager")
        - seniority: One of "entry-level", "mid-level", "senior", "executive"
        - industry: Industry sector (e.g., "Technology", "Finance")
        - work_style: Description of work approach
        - attire_style: One of "suit", "business_casual", "creative", "scrubs"
        - background_setting: One of "corner_office", "open_office", "linkedin_blue", "creative_space"
        - confidence_score: 0-100 indicating match quality
    """
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Extract key information from personality profile
    personality_dims = personality_profile.get('personality_dimensions', {})
    dominant_traits = personality_profile.get('dominant_traits', [])
    vibe = personality_profile.get('vibe', '')
    species = personality_profile.get('species', 'unknown')
    
    career_mapping_prompt = f"""Based on this personality profile, determine the most appropriate human career and professional presentation.

Personality Profile:
- Species: {species}
- Overall Vibe: {vibe}
- Dominant Traits: {', '.join(dominant_traits)}
- Key Dimensions:
  - Confidence: {personality_dims.get('confidence', 50)}
  - Leadership: {personality_dims.get('leadership', 50)}
  - Assertiveness: {personality_dims.get('assertiveness', 50)}
  - Strategic Thinking: {personality_dims.get('strategic_thinking', 50)}
  - Creativity: {personality_dims.get('creativity', 50)}
  - Organization: {personality_dims.get('organization', 50)}
  - Sociability: {personality_dims.get('sociability', 50)}
  - Empathy: {personality_dims.get('empathy', 50)}
  - Ambition: {personality_dims.get('ambition', 50)}
  - Would Steal Lunch: {personality_dims.get('would_steal_lunch', 0)}
  - Sends Passive-Aggressive Emails: {personality_dims.get('sends_passive_aggressive_emails', 0)}

Provide your career mapping in the following JSON format:

{{
    "job_title": "<specific job title>",
    "seniority": "<entry-level|mid-level|senior|executive>",
    "industry": "<industry sector>",
    "work_style": "<brief description of work approach>",
    "attire_style": "<suit|business_casual|creative|scrubs>",
    "background_setting": "<corner_office|open_office|linkedin_blue|creative_space>",
    "confidence_score": <0-100>
}}

Guidelines:
- Match job title to dominant personality traits
- High confidence/leadership/ambition → senior or executive roles
- High creativity/spontaneity → creative industries
- High organization/detail → analytical/administrative roles
- High empathy/sociability → people-facing roles
- Consider the "would steal lunch" and "passive-aggressive emails" scores for realism
- Attire should match industry and seniority
- Background should match seniority (executives get corner offices)
- Confidence score reflects how well the personality fits the role"""

    def make_bedrock_call():
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": career_mapping_prompt
                }]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Extract JSON from response
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        return json.loads(content)
    
    # Call Bedrock with retry logic
    result = retry_with_exponential_backoff(make_bedrock_call)
    
    return result
