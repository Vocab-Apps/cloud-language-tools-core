#!/usr/bin/env python3
"""
Demo script to show how rate limit handling works for Gemini service.
This script can be used to test rate limit scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import cloudlanguagetools.servicemanager
import cloudlanguagetools.errors
from cloudlanguagetools.constants import Service
from cloudlanguagetools.languages import AudioLanguage
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rate_limit_handling():
    """Test rate limit handling by making rapid requests"""
    
    # Initialize service manager
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    
    # Get a Gemini voice
    voice_list = manager.get_tts_voice_list_v3()
    gemini_voices = [v for v in voice_list if v.service == Service.Gemini]
    
    if not gemini_voices:
        logger.error("No Gemini voices found")
        return
    
    voice = gemini_voices[0]
    logger.info(f"Using voice: {voice.name}")
    
    # Make multiple rapid requests to potentially trigger rate limit
    text = "Testing rate limit handling"
    
    total_requests = 20
    for i in range(total_requests):
        try:
            logger.info(f"Request {i+1}/{total_requests}")
            start_time = time.time()
            
            audio_file = manager.get_tts_audio(
                text, 
                voice.service.name, 
                voice.voice_key,
                {}
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Success! Got audio file in {elapsed:.2f} seconds")
            
            # Small delay between requests
            # time.sleep(0.5)
            
        except cloudlanguagetools.errors.RateLimitError as e:
            logger.warning(f"Rate limited! Error: {e}")
            if hasattr(e, 'retry_after') and e.retry_after:
                logger.info(f"Server requested retry after {e.retry_after} seconds")
            else:
                logger.info("No retry_after time provided, using exponential backoff")
                
        except Exception as e:
            logger.error(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_rate_limit_handling()