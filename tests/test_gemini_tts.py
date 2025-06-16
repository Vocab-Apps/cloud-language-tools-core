#!/usr/bin/env python3

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

import cloudlanguagetools.servicemanager
from cloudlanguagetools.constants import Service

# Set up logging to see the debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_tts():
    """Test Gemini TTS with corrected API format"""
    
    # Check if API key is available
    if 'GEMINI_API_KEY' not in os.environ:
        print("GEMINI_API_KEY environment variable not set. Skipping test.")
        return
    
    try:
        # Initialize service manager
        manager = cloudlanguagetools.servicemanager.ServiceManager()
        manager.configure_default()
        
        # Get Gemini service
        gemini_service = manager.services[Service.Gemini]
        
        # Get a voice
        voice_list = gemini_service.get_tts_voice_list_v3()
        if not voice_list:
            print("No Gemini voices available")
            return
            
        test_voice = voice_list[0]  # Use first voice (Zephyr)
        print(f"Testing with voice: {test_voice.name}")
        print(f"Voice key: {test_voice.voice_key}")
        
        # Test text
        test_text = "Hello, this is a test of Google Gemini text-to-speech."
        
        # Options
        options = {
            'model': 'gemini-2.5-flash-preview-tts',
            'audio_format': 'wav'
        }
        
        print("Making TTS request...")
        
        # Make TTS request
        audio_file = gemini_service.get_tts_audio(
            text=test_text,
            voice_key=test_voice.voice_key,
            options=options
        )
        
        print(f"Success! Audio file created: {audio_file.name}")
        print(f"File size: {os.path.getsize(audio_file.name)} bytes")
        
        # Cleanup
        audio_file.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_gemini_tts()