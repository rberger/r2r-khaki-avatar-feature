#!/usr/bin/env python3
"""
End-to-end API test script for PetAvatar.

Tests the complete flow:
1. Get presigned URL
2. Upload a test image
3. Start processing
4. Poll status
5. Get results
"""
import boto3
import json
import requests
import time
import sys
import os
from pathlib import Path

# Configuration
BASE_URL = "https://42kw05zl4d.execute-api.us-west-2.amazonaws.com"
API_KEY = "nX92rzyA9PVj3lniXfHb6H1Uzk3fC8oOgTNRnUjHMSw"

HEADERS = {
    "x-api-key": API_KEY
}


def create_test_image(path: str) -> None:
    """Create a simple test JPEG image using PIL or raw bytes."""
    try:
        from PIL import Image
        # Create a simple 100x100 colored image
        img = Image.new('RGB', (100, 100), color=(73, 109, 137))
        img.save(path, 'JPEG')
        print(f"✓ Created test image with PIL: {path}")
    except ImportError:
        # Create minimal valid JPEG without PIL
        # This is a 1x1 red pixel JPEG
        jpeg_bytes = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xF1, 0x7E, 0xCD,
            0xBF, 0xFF, 0xD9
        ])
        with open(path, 'wb') as f:
            f.write(jpeg_bytes)
        print(f"✓ Created minimal test JPEG: {path}")


def step1_get_presigned_url() -> dict:
    """Step 1: Get presigned URL for upload."""
    print("\n" + "=" * 60)
    print("STEP 1: Get Presigned URL")
    print("=" * 60)
    
    url = f"{BASE_URL}/presigned-url"
    print(f"GET {url}")
    
    response = requests.get(url, headers=HEADERS)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        sys.exit(1)
    
    data = response.json()
    print(f"✓ Job ID: {data.get('job_id')}")
    print(f"✓ Upload URL: {data.get('upload_url', 'N/A')[:80]}...")
    print(f"✓ Expires in: {data.get('expires_in')} seconds")
    
    return data


def step2_upload_image(presigned_data: dict, image_path: str) -> None:
    """Step 2: Upload image using presigned URL."""
    print("\n" + "=" * 60)
    print("STEP 2: Upload Image to S3")
    print("=" * 60)
    
    upload_url = presigned_data.get('upload_url')
    upload_fields = presigned_data.get('upload_fields', {})
    
    if not upload_url:
        print("⚠ No upload_url in response, skipping direct upload")
        return
    
    print(f"POST {upload_url}")
    
    # Prepare form data
    files = {
        'file': ('test_pet.jpg', open(image_path, 'rb'), 'image/jpeg')
    }
    
    response = requests.post(upload_url, data=upload_fields, files=files)
    print(f"Status: {response.status_code}")
    
    if response.status_code in [200, 201, 204]:
        print("✓ Image uploaded successfully")
    else:
        print(f"Upload response: {response.text[:200]}")


def step3_start_processing(job_id: str, s3_key: str) -> dict:
    """Step 3: Start processing the uploaded image."""
    print("\n" + "=" * 60)
    print("STEP 3: Start Processing")
    print("=" * 60)
    
    url = f"{BASE_URL}/process"
    s3_uri = f"s3://petavatar-uploads-456773209430/{s3_key}"
    
    print(f"POST {url}")
    print(f"S3 URI: {s3_uri}")
    
    payload = {"s3_uri": s3_uri}
    response = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)
    print(f"Status: {response.status_code}")
    
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    return data


def step4_poll_status(job_id: str, max_attempts: int = 30, interval: int = 10) -> dict:
    """Step 4: Poll status until complete or failed."""
    print("\n" + "=" * 60)
    print("STEP 4: Poll Job Status")
    print("=" * 60)
    
    url = f"{BASE_URL}/status/{job_id}"
    print(f"GET {url}")
    
    for attempt in range(max_attempts):
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        status = data.get('status', 'unknown')
        progress = data.get('progress', 0)
        
        print(f"  [{attempt + 1}/{max_attempts}] Status: {status}, Progress: {progress}%")
        
        if status == 'completed':
            print("✓ Processing completed!")
            return data
        elif status == 'failed':
            print(f"✗ Processing failed: {data.get('error', 'Unknown error')}")
            return data
        
        time.sleep(interval)
    
    print("⚠ Max polling attempts reached")
    return data


def step5_get_results(job_id: str) -> dict:
    """Step 5: Get the results."""
    print("\n" + "=" * 60)
    print("STEP 5: Get Results")
    print("=" * 60)
    
    url = f"{BASE_URL}/results/{job_id}"
    print(f"GET {url}")
    
    response = requests.get(url, headers=HEADERS)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✓ Results retrieved successfully!")
        print(f"\nAvatar URL: {data.get('avatar_url', 'N/A')[:80]}...")
        
        identity = data.get('identity', {})
        print(f"\nIdentity Package:")
        print(f"  Name: {identity.get('human_name', 'N/A')}")
        print(f"  Job Title: {identity.get('job_title', 'N/A')}")
        print(f"  Seniority: {identity.get('seniority', 'N/A')}")
        print(f"  Similarity Score: {identity.get('similarity_score', 'N/A')}%")
        
        pet = data.get('pet_analysis', {})
        print(f"\nPet Analysis:")
        print(f"  Species: {pet.get('species', 'N/A')}")
        print(f"  Breed: {pet.get('breed', 'N/A')}")
        
        return data
    else:
        print(f"Error: {response.text}")
        return response.json()


def main():
    """Run the complete API test flow."""
    print("=" * 60)
    print("PetAvatar API End-to-End Test")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    
    # Create test image
    test_image_path = "/tmp/test_pet.jpg"
    create_test_image(test_image_path)
    
    # Step 1: Get presigned URL
    presigned_data = step1_get_presigned_url()
    job_id = presigned_data.get('job_id')
    
    if not job_id:
        print("✗ No job_id returned")
        sys.exit(1)
    
    # Step 2: Upload image
    step2_upload_image(presigned_data, test_image_path)
    
    # Get the S3 key from presigned data
    s3_key = presigned_data.get('upload_fields', {}).get('key', f"uploads/{job_id}/image")
    
    # Step 3: Start processing
    process_result = step3_start_processing(job_id, s3_key)
    
    # Step 4: Poll status
    status_result = step4_poll_status(job_id)
    
    # Step 5: Get results (only if completed)
    if status_result.get('status') == 'completed':
        results = step5_get_results(job_id)
    else:
        print("\n⚠ Skipping results retrieval - job not completed")
    
    # Cleanup
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
