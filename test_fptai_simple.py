#!/usr/bin/env python3
"""
Simple reproduction script for FPT.AI TTS API issue
"""

import requests
import json
import pprint

# API configuration
API_KEY = "sk-aRY-7_UWlaFfMLM6bdXd2w"
API_URL = "https://mkp-api.fptcloud.com/v1/audio/speech"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# First, list available models
print("="*50)
print("STEP 1: List available models")
print("="*50)
models_response = requests.get("https://mkp-api.fptcloud.com/v1/models", headers={"Authorization": f"Bearer {API_KEY}"})
print(f"GET /v1/models - Status: {models_response.status_code}")
if models_response.status_code == 200:
    models = models_response.json()
    print("Available models:")
    pprint.pprint(models)
    if models.get('data'):
        model_id = models['data'][0]['id']
        print(f"\nFirst model ID: {model_id}")
print()

print("="*50)
print("STEP 2: Try TTS with the model from Step 1")
print("="*50)

data = {
    "model": "FPT.AI-VITs",
    "input": "xin chào, chúng tôi là FPT",
    "voice": "std_kimngan"
}

print("Request URL:", API_URL)
print("\nRequest Headers:")
pprint.pprint(headers)
print("\nRequest Body:")
pprint.pprint(data)
print()

response = requests.post(API_URL, headers=headers, json=data)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Success! Audio size: {len(response.content)} bytes")
else:
    print(f"Error: {response.text}")

# Issue: Returns "Invalid model name passed in model=FPT.AI-TTS" 
# even though /v1/models lists FPT.AI-TTS as available