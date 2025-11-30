# PetAvatar: Anthropomorphic Identity Generation 

PetAvatar is an AI-powered service that transforms photos of your pet into disturbingly professional human-like avatars. Upload a photo of your golden retriever, receive back a middle-aged man in a business suit who somehow captures your dog's essence. Your cat becomes a disapproving HR manager. Your hamster? Entry-level accountant energy.

## Constraints

* Runs on AWS
  * Use Bedrock for all models
* Should use strands agents and agentcore
* No UI as part of this project, should have a REST interface
  * Rest interface should be implemented with API Gateway and tc-functors
* Use the latest python (3.13?) that will work with the AWS services
  * Should use uv / pyproject.toml for python and dependency management
* For initial MVP we con't need any sophisticated authentication/authorization. Just use an API key for the REST interface initially.

Use modern techniques. Its ok to be overly complex as long as it doesn't take too long to build/deploy/iteratte. 

## Features:

### Core Capabilities

#### Multi-Modal Pet Analysis

* Upload photos in any format (JPEG, PNG, HEIC, or blurry phone pics taken at 2am)
* AI analyzes breed, expression, posture, and "vibe"
* Detects subtle personality traits: "This cat has CFO energy"
* Works with dogs, cats, hamsters, fish, reptiles, and "whatever that thing is"

#### Personality-to-Profession Mapping

* Proprietary algorithm matches pet traits to human careers
* Considers 47 personality dimensions including:
  * "Would steal your lunch from the fridge" score
  * "Sends passive-aggressive emails" probability
  * "Actually reads the meeting agenda" likelihood
  * "Takes credit for group projects" index

#### 👔 Professional Avatar Generation

* Creates photorealistic human avatars using Amazon Titan Image Generator
* Automatically selects appropriate business attire:
  * Suit & tie for executive pets
  * Business casual for friendly breeds
  * Black turtleneck for "visionary" pets
  * Scrubs for pets with "helper" energy
* Background options can include (come up with more): 
  * Office
  * LinkedIn blue gradient
  * Corner office with city view

#### Bio & Identity Package

* Each avatar comes with:
  * Human Name: AI-generated name that "feels right" (Golden Retriever = "Greg," "Doug," or "Buddy")
  * Job Title: Matched to personality analysis
  * LinkedIn Summary: 3-paragraph professional bio written in corporate speak
  * Skills & Endorsements: Auto-generated from pet behaviors
  * Career Trajectory: Where they started, where they're going
* Similarity Scoring
  * Pet-to-Human match percentage
  * "Separated at Birth?" analysis
  * Side-by-side comparison highlighting uncanny parallels
  * Shareable report card
