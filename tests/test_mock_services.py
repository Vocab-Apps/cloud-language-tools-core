import os
import sys
import logging
import unittest
import json
import pytest
import pprint
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

LOAD_TEST_SERVICES_ONLY = os.environ.get('CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES', 'no') == 'yes'

import requests.exceptions
import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.languages import Language
from cloudlanguagetools.constants import Service
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestMockServices(unittest.TestCase):
    
    def test_language_data(self):
        if not LOAD_TEST_SERVICES_ONLY:
            pytest.skip('you must set CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes')

        manager = get_manager()
        language_data = manager.get_language_data_json_v2()
        self.assertTrue(len(language_data['premium']) > 0)
        self.assertTrue(len(language_data['free']) > 0)


    def test_translation(self):
        if not LOAD_TEST_SERVICES_ONLY:
            pytest.skip('you must set CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes')

        manager = get_manager()
        language_data = manager.get_language_data_json_v2()
        translation_options = language_data['free']['translation_options']
        # pprint.pprint(translation_options)
        translation_options_fr = [x for x in translation_options if x['language_code'] == 'fr']
        self.assertEqual(len(translation_options_fr), 1)

        translated_text_str = manager.get_translation('text_input', 'TestServiceA', 'fr', 'en')
        translated_text_obj = json.loads(translated_text_str)
        translated_text_expected = {
            'text': 'text_input',
            'from_language_key': 'fr',
            'to_language_key': 'en'
        }
        self.assertEqual(translated_text_obj, translated_text_expected)

        translated_text_str = manager.get_translation('text_input', 'TestServiceB', 'fr', 'en')
        translated_text_obj = json.loads(translated_text_str)
        self.assertEqual(translated_text_obj, translated_text_expected)

    def test_transliteration(self):
        if not LOAD_TEST_SERVICES_ONLY:
            pytest.skip('you must set CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes')

        manager = get_manager()
        language_data = manager.get_language_data_json_v2()
        translation_options = language_data['free']['transliteration_options']
        # pprint.pprint(translation_options)
        translation_options_zh = [x for x in translation_options if x['language_code'] == 'zh_cn']
        self.assertEqual(len(translation_options_zh), 1)

        transliterated_text_str = manager.get_transliteration('text_input', 'TestServiceA', translation_options_zh[0]['transliteration_key'])
        transliterated_text_obj = json.loads(transliterated_text_str)
        transliterated_text_expected = {
            'text': 'text_input',
            'transliteration_key': 'pinyin'
        }
        self.assertEqual(transliterated_text_obj, transliterated_text_expected)

    def test_dictionary_lookup(self):
        if not LOAD_TEST_SERVICES_ONLY:
            pytest.skip('you must set CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes')

        manager = get_manager()
        language_data = manager.get_language_data_json_v2()
        dict_lookup_options = language_data['free']['dictionary_lookup_options']
        # pprint.pprint(translation_options)
        dict_lookup_options_zh = [x for x in dict_lookup_options if x['language_code'] == 'zh_cn']
        self.assertEqual(len(dict_lookup_options_zh), 1)

        transliterated_text_str = manager.get_dictionary_lookup('text_input', 'TestServiceA', dict_lookup_options_zh[0]['lookup_key'])
        transliterated_text_obj = json.loads(transliterated_text_str)
        transliterated_text_expected = {
            'type': 'dictionary',
            'text': 'text_input',
            'lookup_key': 'zh'
        }
        self.assertEqual(transliterated_text_obj, transliterated_text_expected)

    def test_service_cost(self):
        if not LOAD_TEST_SERVICES_ONLY:
            pytest.skip('you must set CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes')

        manager = get_manager()
        # test services
        self.assertEqual(manager.service_cost('abcd', 'TestServiceA', cloudlanguagetools.constants.RequestType.transliteration), 0)
        self.assertEqual(manager.service_cost('abcd', 'TestServiceB', cloudlanguagetools.constants.RequestType.transliteration), 4)


@pytest.mark.skipif(
    os.environ.get('CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES', 'no') != 'yes',
    reason='you must set CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes'
)
class TestTtsAudioV5(unittest.TestCase):
    """Tests for get_tts_audio_v5 exception normalization."""

    def setUp(self):
        self.manager = cloudlanguagetools.servicemanager.ServiceManager()

    def test_success(self):
        """Successful call returns a temp file."""
        result = self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})
        self.assertIsNotNone(result)

    def test_transient_error_passes_through(self):
        """TransientError from the service is re-raised as-is."""
        with patch.object(self.manager.services[Service.TestServiceA], 'get_tts_audio',
                          side_effect=cloudlanguagetools.errors.RequestError('service unavailable')):
            with self.assertRaises(cloudlanguagetools.errors.RequestError):
                self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})

    def test_permanent_error_passes_through(self):
        """PermanentError from the service is re-raised as-is."""
        with patch.object(self.manager.services[Service.TestServiceA], 'get_tts_audio',
                          side_effect=cloudlanguagetools.errors.AuthenticationError('bad key')):
            with self.assertRaises(cloudlanguagetools.errors.AuthenticationError):
                self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})

    def test_timeout_error_passes_through(self):
        """errors.TimeoutError (already a TransientError) passes through."""
        with patch.object(self.manager.services[Service.TestServiceA], 'get_tts_audio',
                          side_effect=cloudlanguagetools.errors.TimeoutError('timed out')):
            with self.assertRaises(cloudlanguagetools.errors.TimeoutError):
                self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})

    def test_requests_timeout_becomes_timeout_error(self):
        """requests.exceptions.Timeout is caught and re-raised as errors.TimeoutError."""
        with patch.object(self.manager.services[Service.TestServiceA], 'get_tts_audio',
                          side_effect=requests.exceptions.ReadTimeout('read timed out')):
            with self.assertRaises(cloudlanguagetools.errors.TimeoutError):
                self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})

    def test_requests_connect_timeout_becomes_timeout_error(self):
        """requests.exceptions.ConnectTimeout is caught as Timeout subclass."""
        with patch.object(self.manager.services[Service.TestServiceA], 'get_tts_audio',
                          side_effect=requests.exceptions.ConnectTimeout('connect timed out')):
            with self.assertRaises(cloudlanguagetools.errors.TimeoutError):
                self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})


    def test_unexpected_exception_becomes_transient_error(self):
        """Any unexpected exception is wrapped as TransientError."""
        with patch.object(self.manager.services[Service.TestServiceA], 'get_tts_audio',
                          side_effect=RuntimeError('something broke')):
            with self.assertRaises(cloudlanguagetools.errors.TransientError) as ctx:
                self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})
            self.assertNotIsInstance(ctx.exception, cloudlanguagetools.errors.PermanentError)

    def test_unexpected_exception_preserves_cause(self):
        """Unexpected exceptions are chained with __cause__."""
        original = ValueError('bad value')
        with patch.object(self.manager.services[Service.TestServiceA], 'get_tts_audio',
                          side_effect=original):
            with self.assertRaises(cloudlanguagetools.errors.TransientError) as ctx:
                self.manager.get_tts_audio_v5('hello', 'TestServiceA', {'voice_id': 'paul'}, {})
            self.assertIs(ctx.exception.__cause__, original)
