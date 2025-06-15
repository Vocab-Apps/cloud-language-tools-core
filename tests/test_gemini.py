import unittest
import logging
import sys
import os

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

class TestGemini(unittest.TestCase):

    def setUp(self):
        self.manager = get_manager()
        self.gemini_service = self.manager.services[Service.Gemini]

    def test_get_tts_voice_list_v3(self):
        """Test TtsVoice_v3 voice list generation"""
        voice_list = self.gemini_service.get_tts_voice_list_v3()
        self.assertEqual(len(voice_list), 30)  # Should have 30 voices
        
        # Check that we have different voice names
        voice_names = set([voice.name for voice in voice_list])
        self.assertEqual(len(voice_names), 30)  # All voices should have unique names
        
        # Check that each voice has required attributes
        for voice in voice_list:
            self.assertIsNotNone(voice.name)
            self.assertIsNotNone(voice.service)
            self.assertEqual(voice.service, Service.Gemini)
            self.assertIsNotNone(voice.audio_languages)
            self.assertIsNotNone(voice.gender)
            self.assertIsNotNone(voice.voice_key)
            self.assertIn('name', voice.voice_key)
            
            # Check that voice supports multiple languages (multilingual)
            self.assertGreaterEqual(len(voice.audio_languages), 20)

    def test_service_manager_get_tts_voice_list_v3_gemini(self):
        """Test ServiceManager integration with TtsVoice_v3"""
        voice_list = self.manager.get_tts_voice_list_v3()
        gemini_voices = [voice for voice in voice_list if voice.service == Service.Gemini]
        self.assertEqual(len(gemini_voices), 30)
        
        # Verify all voices are from Gemini service
        for voice in gemini_voices:
            self.assertEqual(voice.service, Service.Gemini)

    def test_voice_characteristics(self):
        """Test that voice names include characteristics"""
        voice_list = self.gemini_service.get_tts_voice_list_v3()
        
        # Check that some well-known voices exist with characteristics
        voice_names = [voice.name for voice in voice_list]
        
        self.assertIn('Zephyr (Bright)', voice_names)
        self.assertIn('Puck (Upbeat)', voice_names)
        self.assertIn('Charon (Informative)', voice_names)
        self.assertIn('Kore (Firm)', voice_names)

    def test_voice_options(self):
        """Test voice options structure"""
        voice_list = self.gemini_service.get_tts_voice_list_v3()
        voice = voice_list[0]
        
        # Check that options include model selection
        self.assertIn('model', voice.options)
        self.assertIn('values', voice.options['model'])
        self.assertIn('gemini-2.5-flash-preview-tts', voice.options['model']['values'])
        self.assertIn('gemini-2.5-pro-preview-tts', voice.options['model']['values'])
        
        # Check audio format options
        self.assertIn(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, voice.options)

    def test_voice_key_format(self):
        """Test voice key format for TtsVoice_v3"""
        voice_list = self.gemini_service.get_tts_voice_list_v3()
        
        for voice in voice_list:
            self.assertIsInstance(voice.voice_key, dict)
            self.assertIn('name', voice.voice_key)
            self.assertIsInstance(voice.voice_key['name'], str)
            
            # Voice key name should not contain parentheses (that's in the display name)
            self.assertNotIn('(', voice.voice_key['name'])
            self.assertNotIn(')', voice.voice_key['name'])

    def test_multilingual_support(self):
        """Test that voices are multilingual like OpenAI"""
        voice_list = self.gemini_service.get_tts_voice_list_v3()
        voice = voice_list[0]
        
        # Check that the voice supports multiple languages
        supported_languages = voice.audio_languages
        self.assertGreaterEqual(len(supported_languages), 20)
        
        # Check for some key languages
        language_codes = [lang.name for lang in supported_languages]
        self.assertIn('en_US', language_codes)
        self.assertIn('fr_FR', language_codes)
        self.assertIn('es_ES', language_codes)
        self.assertIn('de_DE', language_codes)

    def test_service_fee(self):
        """Test that service fee is set correctly"""
        voice_list = self.gemini_service.get_tts_voice_list_v3()
        
        for voice in voice_list:
            self.assertEqual(voice.service_fee, cloudlanguagetools.constants.ServiceFee.paid)

    def test_legacy_voice_list_empty(self):
        """Test that legacy get_tts_voice_list returns empty list"""
        legacy_voices = self.gemini_service.get_tts_voice_list()
        self.assertEqual(len(legacy_voices), 0)

if __name__ == '__main__':
    unittest.main()