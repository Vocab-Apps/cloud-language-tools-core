import unittest
import logging
import random
import requests
import re
import sys
import os
import time
import magic
import pytest
import json
import time
import pprint
import functools
import tempfile
import backoff

import audio_utils

CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE = os.environ.get('CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE', 'no') == 'yes'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.options
import cloudlanguagetools.errors
import cloudlanguagetools.gemini
from cloudlanguagetools.languages import Language
from cloudlanguagetools.languages import AudioLanguage
from cloudlanguagetools.constants import Service

logger = logging.getLogger(__name__)

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

BACKOFF_MAX_TIME=30

def skip_unreliable_clt_test():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE:
                pytest.skip(f'you must set CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes')
            return func(*args, **kwargs)
        return wrapper
    return decorator

class TestGemini(unittest.TestCase):

    def setUp(self):
        self.manager = get_manager()
        self.gemini_service = self.manager.services[Service.Gemini]

    def test_get_tts_voice_list(self):
        voice_list = cloudlanguagetools.gemini.get_tts_voice_list()
        self.assertTrue(len(voice_list) > 0)
        
        # Check that we have voices for different languages
        languages = set([voice.audio_language for voice in voice_list])
        self.assertTrue(len(languages) > 1)
        
        # Check that each voice has required attributes
        for voice in voice_list:
            self.assertIsNotNone(voice.name)
            self.assertIsNotNone(voice.service)
            self.assertEqual(voice.service, Service.Gemini)
            self.assertIsNotNone(voice.audio_language)
            self.assertIsNotNone(voice.gender)

    def test_service_manager_get_tts_voice_list_gemini(self):
        voice_list = self.manager.get_tts_voice_list()
        gemini_voices = [voice for voice in voice_list if voice.service == Service.Gemini]
        self.assertTrue(len(gemini_voices) > 0)
        
        # Verify all voices are from Gemini service
        for voice in gemini_voices:
            self.assertEqual(voice.service, Service.Gemini)

    @skip_unreliable_clt_test()
    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, 
                          cloudlanguagetools.errors.RequestError,
                          cloudlanguagetools.errors.TimeoutError),
                         max_time=BACKOFF_MAX_TIME)
    def test_get_tts_audio_simple(self):
        """Test basic TTS audio generation"""
        voice_list = [voice for voice in self.manager.get_tts_voice_list() if voice.service == Service.Gemini]
        voice = [x for x in voice_list if x.audio_language == AudioLanguage.en_US][0]
        
        output_temp_file = self.manager.get_tts_audio('hello world', 'Gemini', voice.get_voice_key(), {})
        
        # Verify file was created and has content
        self.assertIsNotNone(output_temp_file)
        file_size = os.path.getsize(output_temp_file.name)
        self.assertTrue(file_size > 1000)  # Should be at least 1KB
        
        # Verify it's an audio file
        file_type = magic.from_file(output_temp_file.name, mime=True)
        self.assertTrue('audio' in file_type)

    @skip_unreliable_clt_test()
    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, 
                          cloudlanguagetools.errors.RequestError,
                          cloudlanguagetools.errors.TimeoutError),
                         max_time=BACKOFF_MAX_TIME)
    def test_get_tts_audio_different_voices(self):
        """Test TTS with different voice options"""
        voice_list = [voice for voice in self.manager.get_tts_voice_list() if voice.service == Service.Gemini]
        
        # Test with Kore voice
        kore_voice = [x for x in voice_list if 'kore' in x.get_voice_key().lower() and x.audio_language == AudioLanguage.en_US][0]
        output_file_kore = self.manager.get_tts_audio('Hello, this is a test', 'Gemini', kore_voice.get_voice_key(), {})
        
        # Test with Zephyr voice
        zephyr_voice = [x for x in voice_list if 'zephyr' in x.get_voice_key().lower() and x.language == AudioLanguage.en_US][0]
        output_file_zephyr = self.manager.get_tts_audio('Hello, this is a test', 'Gemini', zephyr_voice.get_voice_key(), {})
        
        # Both should generate valid audio files
        self.assertTrue(os.path.getsize(output_file_kore.name) > 1000)
        self.assertTrue(os.path.getsize(output_file_zephyr.name) > 1000)
        
        # Files should be different (different voices should produce different audio)
        with open(output_file_kore.name, 'rb') as f1, open(output_file_zephyr.name, 'rb') as f2:
            content1 = f1.read()
            content2 = f2.read()
            self.assertNotEqual(content1, content2)

    @skip_unreliable_clt_test()
    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, 
                          cloudlanguagetools.errors.RequestError,
                          cloudlanguagetools.errors.TimeoutError),
                         max_time=BACKOFF_MAX_TIME)
    def test_get_tts_audio_different_languages(self):
        """Test TTS with different languages"""
        voice_list = [voice for voice in self.manager.get_tts_voice_list() if voice.service == Service.Gemini]
        
        # Test English
        en_voice = [x for x in voice_list if x.language == AudioLanguage.en_US][0]
        output_en = self.manager.get_tts_audio('Hello world', 'Gemini', en_voice.get_voice_key(), {})
        
        # Test French
        fr_voices = [x for x in voice_list if x.audio_language == AudioLanguage.fr_FR]
        if fr_voices:
            fr_voice = fr_voices[0]
            output_fr = self.manager.get_tts_audio('Bonjour le monde', 'Gemini', fr_voice.get_voice_key(), {})
            
            # Both should generate valid audio files
            self.assertTrue(os.path.getsize(output_en.name) > 1000)
            self.assertTrue(os.path.getsize(output_fr.name) > 1000)

    @skip_unreliable_clt_test()
    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, 
                          cloudlanguagetools.errors.RequestError,
                          cloudlanguagetools.errors.TimeoutError),
                         max_time=BACKOFF_MAX_TIME)
    def test_get_tts_audio_with_options(self):
        """Test TTS with different model options"""
        voice_list = [voice for voice in self.manager.get_tts_voice_list() if voice.service == Service.Gemini]
        voice = [x for x in voice_list if x.audio_language == AudioLanguage.en_US][0]
        
        # Test with flash model
        options_flash = {'model': 'gemini-2.5-flash-preview-tts'}
        output_flash = self.manager.get_tts_audio('Testing flash model', 'Gemini', voice.get_voice_key(), options_flash)
        
        # Test with pro model
        options_pro = {'model': 'gemini-2.5-pro-preview-tts'}
        output_pro = self.manager.get_tts_audio('Testing pro model', 'Gemini', voice.get_voice_key(), options_pro)
        
        # Both should generate valid audio files
        self.assertTrue(os.path.getsize(output_flash.name) > 1000)
        self.assertTrue(os.path.getsize(output_pro.name) > 1000)

    def test_get_tts_audio_invalid_voice_key(self):
        """Test error handling for invalid voice key"""
        with self.assertRaises(cloudlanguagetools.errors.RequestError):
            self.manager.get_tts_audio('test', 'Gemini', 'invalid_voice_key', {})

    @skip_unreliable_clt_test()
    def test_get_tts_audio_long_text(self):
        """Test TTS with longer text"""
        voice_list = [voice for voice in self.manager.get_tts_voice_list() if voice.service == Service.Gemini]
        voice = [x for x in voice_list if x.audio_language == AudioLanguage.en_US][0]
        
        long_text = ("This is a longer text to test the Gemini TTS service. "
                    "It should handle longer passages of text without issues. "
                    "The service should generate clear, natural-sounding speech "
                    "for this extended content.")
        
        output_file = self.manager.get_tts_audio(long_text, 'Gemini', voice.get_voice_key(), {})
        
        # Should generate a larger audio file for longer text
        file_size = os.path.getsize(output_file.name)
        self.assertTrue(file_size > 2000)  # Should be larger for longer text
        
        # Verify it's still valid audio
        file_type = magic.from_file(output_file.name, mime=True)
        self.assertTrue('audio' in file_type)

if __name__ == '__main__':
    unittest.main()