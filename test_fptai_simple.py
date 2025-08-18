#!/usr/bin/env python3
"""
Simple reproduction script for FPT.AI TTS API issue
"""

import requests
import json
import pprint

# API configuration
API_KEY = "sk-xyNBKkYUjL9-1GqNGX2a6w"
API_URL = "https://mkp-api.fptcloud.com/v1/audio/speech"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "FPT.AI-TTS",
    "input": "xin chào, chúng tôi là FPT",
    "voice": "std_kimngan"
}

print("Request URL:", API_URL)
print("\nRequest Headers:")
pprint.pprint(headers)
print("\nRequest Body:")
pprint.pprint(data)
print("\n" + "="*50)

response = requests.post(API_URL, headers=headers, json=data)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Success! Audio size: {len(response.content)} bytes")
else:
    print(f"Error: {response.text}")

# Issue: Returns "Invalid model name passed in model=FPT.AI-TTS" 
# even though /v1/models lists FPT.AI-TTS as available