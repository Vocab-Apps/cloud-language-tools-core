import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import google.cloud.texttospeech
import google.api_core.exceptions
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.google
import cloudlanguagetools.errors


class MockVoiceData:
    def __init__(self, name, language_code='en-US', ssml_gender=google.cloud.texttospeech.SsmlVoiceGender.FEMALE):
        self.name = name
        self.language_codes = [language_code]
        self.ssml_gender = ssml_gender


class TestGoogleVoicePitchSupport(unittest.TestCase):

    def test_neural2_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Neural2-A'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_news_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-News-K'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_wavenet_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Wavenet-A'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_standard_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Standard-A'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_chirp_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Chirp3-HD-Leda'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())

    def test_chirp_variant_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('ar-XA-Chirp3-HD-Leda'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())

    def test_studio_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Studio-O'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())

    def test_journey_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Journey-F'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())


class TestGoogleVoiceSupportsSsml(unittest.TestCase):

    def test_chirp3_hd_supports_ssml(self):
        self.assertTrue(cloudlanguagetools.google.voice_supports_ssml('en-US-Chirp3-HD-Charon'))

    def test_chirp3_hd_arabic_supports_ssml(self):
        self.assertTrue(cloudlanguagetools.google.voice_supports_ssml('ar-XA-Chirp3-HD-Leda'))

    def test_chirp_hd_no_ssml(self):
        self.assertFalse(cloudlanguagetools.google.voice_supports_ssml('en-US-Chirp-HD-O'))

    def test_journey_no_ssml(self):
        self.assertFalse(cloudlanguagetools.google.voice_supports_ssml('en-US-Journey-F'))

    def test_neural2_supports_ssml(self):
        self.assertTrue(cloudlanguagetools.google.voice_supports_ssml('en-US-Neural2-A'))

    def test_wavenet_supports_ssml(self):
        self.assertTrue(cloudlanguagetools.google.voice_supports_ssml('en-US-Wavenet-A'))

    def test_standard_supports_ssml(self):
        self.assertTrue(cloudlanguagetools.google.voice_supports_ssml('en-US-Standard-A'))

    def test_studio_supports_ssml(self):
        self.assertTrue(cloudlanguagetools.google.voice_supports_ssml('en-US-Studio-O'))


class TestGoogleTtsInvalidArgument(unittest.TestCase):

    VOICE_KEY = {
        'name': 'en-US-Standard-A',
        'language_code': 'en-US',
        'ssml_gender': 'FEMALE',
    }
    OPTIONS = {}

    @patch.object(cloudlanguagetools.google.GoogleService, 'get_client')
    def test_invalid_argument_raises_input_error(self, mock_get_client):
        """InvalidArgument from Google (e.g. sentence too long) must raise InputError to prevent client retries."""
        exc = google.api_core.exceptions.InvalidArgument(
            'This request contains sentences that are too long. '
            'Consider splitting up long sentences with sentence ending punctuation e.g. periods. '
            'Sentence starting with: "\U0001d410\U0001d410 Eg" is too long.'
        )

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = exc
        mock_get_client.return_value = mock_client

        service = cloudlanguagetools.google.GoogleService()
        with self.assertRaises(cloudlanguagetools.errors.InputError):
            service.get_tts_audio('hello', self.VOICE_KEY, self.OPTIONS)


class TestGoogleTtsDeadlineExceeded(unittest.TestCase):

    VOICE_KEY = {
        'name': 'en-US-Standard-A',
        'language_code': 'en-US',
        'ssml_gender': 'FEMALE',
    }
    OPTIONS = {}

    @patch.object(cloudlanguagetools.google.GoogleService, 'get_client')
    def test_deadline_exceeded_raises_timeout_error(self, mock_get_client):
        """DeadlineExceeded from Google must raise TimeoutError so callers can retry."""
        exc = google.api_core.exceptions.DeadlineExceeded('Deadline Exceeded')

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = exc
        mock_get_client.return_value = mock_client

        service = cloudlanguagetools.google.GoogleService()
        with self.assertRaises(cloudlanguagetools.errors.TimeoutError):
            service.get_tts_audio('hello', self.VOICE_KEY, self.OPTIONS)


class TestGoogleTtsRateLimit(unittest.TestCase):

    VOICE_KEY = {
        'name': 'en-US-Standard-A',
        'language_code': 'en-US',
        'ssml_gender': 'FEMALE',
    }
    OPTIONS = {}

    def _make_resource_exhausted(self, details):
        exc = google.api_core.exceptions.ResourceExhausted('Resource has been exhausted')
        exc._details = details
        return exc

    @patch.object(cloudlanguagetools.google.GoogleService, 'get_client')
    def test_rate_limit_with_retry_delay(self, mock_get_client):
        """When Google provides a retry_delay, use that value."""
        retry_detail = MagicMock()
        retry_detail.retry_delay.seconds = 30
        exc = self._make_resource_exhausted([retry_detail])

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = exc
        mock_get_client.return_value = mock_client

        service = cloudlanguagetools.google.GoogleService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitRetryAfterError) as ctx:
            service.get_tts_audio('hello', self.VOICE_KEY, self.OPTIONS)
        self.assertEqual(ctx.exception.retry_after, 30)

    @patch.object(cloudlanguagetools.google.GoogleService, 'get_client')
    def test_rate_limit_without_retry_delay_defaults_to_60(self, mock_get_client):
        """When Google does not provide a retry_delay, default to 60 seconds."""
        detail_without_retry = MagicMock(spec=[])  # no retry_delay attribute
        exc = self._make_resource_exhausted([detail_without_retry])

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = exc
        mock_get_client.return_value = mock_client

        service = cloudlanguagetools.google.GoogleService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitRetryAfterError) as ctx:
            service.get_tts_audio('hello', self.VOICE_KEY, self.OPTIONS)
        self.assertEqual(ctx.exception.retry_after, 60)

    @patch.object(cloudlanguagetools.google.GoogleService, 'get_client')
    def test_rate_limit_empty_details_defaults_to_60(self, mock_get_client):
        """When Google provides no details at all, default to 60 seconds."""
        exc = self._make_resource_exhausted([])

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = exc
        mock_get_client.return_value = mock_client

        service = cloudlanguagetools.google.GoogleService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitRetryAfterError) as ctx:
            service.get_tts_audio('hello', self.VOICE_KEY, self.OPTIONS)
        self.assertEqual(ctx.exception.retry_after, 60)


if __name__ == '__main__':
    unittest.main()
