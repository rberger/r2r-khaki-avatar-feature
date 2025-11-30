"""
Tool for generating complete professional identity packages.

This tool creates human names, LinkedIn-style bios, professional skills,
career trajectories, and similarity scores based on pet personality and career profiles.
"""

import json
import boto3
from typing import Any
from strands import tool
from .analyze_pet import retry_with_exponential_backoff


# Species-appropriate name patterns
SPECIES_NAME_PATTERNS = {
    'dog': {
        'golden_retriever': ['Greg', 'Doug', 'Buddy', 'Max', 'Charlie', 'Cooper', 'Tucker'],
        'labrador': ['Jake', 'Sam', 'Bailey', 'Duke', 'Rocky', 'Bear'],
        'german_shepherd': ['Rex', 'Bruno', 'Zeus', 'Thor', 'Gunner', 'Axel'],
        'poodle': ['Pierre', 'Marcel', 'Francois', 'Henri', 'Claude'],
        'default': ['Max', 'Buddy', 'Charlie', 'Jack', 'Rocky', 'Duke', 'Bear', 'Tucker']
    },
    'cat': {
        'default': ['Margaret', 'Sebastian', 'Penelope', 'Theodore', 'Beatrice', 
                   'Winston', 'Vivienne', 'Reginald', 'Cordelia', 'Archibald']
    },
    'hamster': {
        'default': ['Chip', 'Nibbles', 'Squeaky', 'Peanut', 'Whiskers']
    },
    'fish': {
        'default': ['Finn', 'Coral', 'Marina', 'Neptune', 'Splash']
    },
    'reptile': {
        'default': ['Rex', 'Spike', 'Scales', 'Draco', 'Viper']
    },
    'other': {
        'default': ['Alex', 'Sam', 'Jordan', 'Casey', 'Riley']
    }
}


def generate_name_from_species(species: str, breed: str = None) -> str:
    """
    Generate an appropriate human name based on pet species and breed.
    
    Args:
        species: Pet species (dog, cat, etc.)
        breed: Optional breed information
        
    Returns:
        Human name string
    """
    import random
    
    species = species.lower() if species else 'other'
    breed_lower = breed.lower() if breed else 'default'
    
    # Get species-specific names
    species_names = SPECIES_NAME_PATTERNS.get(species, SPECIES_NAME_PATTERNS['other'])
    
    # Try to match breed-specific names first
    if breed_lower in species_names:
        names = species_names[breed_lower]
    else:
        names = species_names.get('default', SPECIES_NAME_PATTERNS['other']['default'])
    
    return random.choice(names)


def calculate_similarity_score(
    personality_profile: dict,
    career_profile: dict,
    name_appropriateness: float = 0.8
) -> float:
    """
    Calculate similarity score representing pet-to-human match quality.
    
    Weighted combination of:
    - Personality trait alignment (40%)
    - Career fit confidence (30%)
    - Name appropriateness (15%)
    - Overall coherence (15%)
    
    Args:
        personality_profile: Pet personality analysis
        career_profile: Career mapping results
        name_appropriateness: Score for name fit (0-1)
        
    Returns:
        Similarity score (0-100)
    """
    # Career fit confidence (30%)
    career_confidence = career_profile.get('confidence_score', 75) * 0.3
    
    # Personality trait alignment (40%) - based on dominant traits
    personality_dims = personality_profile.get('personality_dimensions', {})
    relevant_traits = ['confidence', 'leadership', 'assertiveness', 'sociability', 
                      'creativity', 'organization', 'empathy']
    trait_scores = [personality_dims.get(trait, 50) for trait in relevant_traits]
    avg_trait_score = sum(trait_scores) / len(trait_scores) if trait_scores else 50
    personality_alignment = avg_trait_score * 0.4
    
    # Name appropriateness (15%)
    name_score = name_appropriateness * 100 * 0.15
    
    # Overall coherence (15%) - assume high coherence if we got this far
    coherence_score = 85 * 0.15
    
    total_score = career_confidence + personality_alignment + name_score + coherence_score
    
    # Ensure score is between 0 and 100
    return min(100, max(0, total_score))


@tool
def generate_identity_package(
    personality_profile: dict,
    career_profile: dict,
    species: str
) -> dict:
    """
    Generates complete professional identity package.
    
    Creates a human name, LinkedIn-style bio, professional skills list,
    career trajectory, and similarity score.
    
    Args:
        personality_profile: Pet personality analysis from analyze_pet_image
        career_profile: Career mapping from map_personality_to_career
        species: Pet species for name generation
        
    Returns:
        Dictionary containing:
        - human_name: Generated human name
        - bio: Three-paragraph LinkedIn-style professional bio
        - skills: List of 5-10 professional skills
        - career_trajectory: Dict with past, present, future
        - similarity_score: 0-100 match percentage
    """
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Generate appropriate name
    breed = personality_profile.get('breed', '')
    human_name = generate_name_from_species(species, breed)
    
    # Extract key information
    job_title = career_profile.get('job_title', 'Professional')
    seniority = career_profile.get('seniority', 'mid-level')
    industry = career_profile.get('industry', 'Business')
    work_style = career_profile.get('work_style', 'collaborative')
    dominant_traits = personality_profile.get('dominant_traits', [])
    vibe = personality_profile.get('vibe', 'professional')
    
    identity_prompt = f"""Create a complete professional identity package for {human_name}, a {seniority} {job_title} in the {industry} industry.

Personality Context:
- Overall Vibe: {vibe}
- Dominant Traits: {', '.join(dominant_traits)}
- Work Style: {work_style}

Provide your response in the following JSON format:

{{
    "bio": "<three paragraphs in LinkedIn style>",
    "skills": ["<skill1>", "<skill2>", ..., "<skill5-10>"],
    "career_trajectory": {{
        "past": "<description of past roles and journey>",
        "present": "<description of current role and responsibilities>",
        "future": "<description of aspirations and goals>"
    }}
}}

Guidelines for the bio:
- Paragraph 1: Current role, key responsibilities, and impact
- Paragraph 2: Professional background, experience, and achievements
- Paragraph 3: Approach to work, values, and what drives them

Guidelines for skills:
- Generate 5-10 professional skills that align with the job title and personality
- Mix technical/domain skills with soft skills
- Make them believable and relevant to the role

Guidelines for career trajectory:
- Past: 2-3 sentences about how they got to where they are
- Present: 2-3 sentences about current focus and contributions
- Future: 2-3 sentences about career aspirations and goals

Make it professional, believable, and aligned with the personality traits."""

    def make_bedrock_call():
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{
                    "role": "user",
                    "content": identity_prompt
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
    
    # Add the generated name
    result['human_name'] = human_name
    
    # Calculate similarity score
    result['similarity_score'] = calculate_similarity_score(
        personality_profile,
        career_profile
    )
    
    return result
