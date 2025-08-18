#!/usr/bin/env python3
"""
Standalone script to test FPT.AI's new TTS API endpoint.
This script demonstrates issues with the new API authentication/model access.
"""

import requests
import json
import sys

def test_fptai_api():
    """Test the new FPT.AI TTS API endpoint"""
    
    # API configuration
    API_KEY = "sk-xyNBKkYUjL9-1GqNGX2a6w"
    API_URL = "https://mkp-api.fptcloud.com/v1/audio/speech"
    
    print("=" * 60)
    print("FPT.AI TTS API Test Script")
    print("=" * 60)
    print()
    
    # First, check available models
    print("1. Checking available models...")
    models_url = "https://mkp-api.fptcloud.com/v1/models"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        response = requests.get(models_url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"   Available models: {json.dumps(models, indent=2)}")
            if models.get('data'):
                available_model = models['data'][0]['id']
                print(f"   First available model: {available_model}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print()
    print("2. Testing TTS API with different configurations...")
    print()
    
    # Test configurations
    test_cases = [
        {
            "name": "Test 1: With model from /v1/models response",
            "data": {
                "model": "FPT.AI-TTS",
                "input": "xin chào, chúng tôi là FPT",
                "voice": "std_kimngan"
            }
        },
        {
            "name": "Test 2: With speed parameter",
            "data": {
                "model": "FPT.AI-TTS",
                "input": "xin chào, chúng tôi là FPT",
                "voice": "std_kimngan",
                "speed": 1.0
            }
        },
        {
            "name": "Test 3: Without std_ prefix",
            "data": {
                "model": "FPT.AI-TTS",
                "input": "xin chào, chúng tôi là FPT",
                "voice": "kimngan"
            }
        },
        {
            "name": "Test 4: With voice name instead of ID",
            "data": {
                "model": "FPT.AI-TTS",
                "input": "xin chào, chúng tôi là FPT",
                "voice": "Kim Ngan"
            }
        },
        {
            "name": "Test 5: Without model parameter",
            "data": {
                "input": "xin chào, chúng tôi là FPT",
                "voice": "std_kimngan"
            }
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{test_case['name']}")
        print(f"   Request: {json.dumps(test_case['data'], ensure_ascii=False)}")
        
        try:
            response = requests.post(API_URL, headers=headers, json=test_case['data'], timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Success - audio data returned
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                print(f"   Success! Content-Type: {content_type}, Size: {content_length} bytes")
            else:
                # Error - print response
                try:
                    error_json = response.json()
                    print(f"   Error: {json.dumps(error_json, indent=6)}")
                except:
                    print(f"   Error: {response.text[:500]}")
        except requests.exceptions.Timeout:
            print(f"   Error: Request timed out")
        except Exception as e:
            print(f"   Exception: {e}")
        
        print()
    
    print("=" * 60)
    print("Additional Information:")
    print(f"- API Key: {API_KEY}")
    print(f"- API Endpoint: {API_URL}")
    print("- Expected behavior: The API should return audio data (WAV format)")
    print("- Issue: Model 'FPT.AI-TTS' is listed as available but returns")
    print("  'Invalid model name' error when used")
    print("=" * 60)

if __name__ == "__main__":
    test_fptai_api()