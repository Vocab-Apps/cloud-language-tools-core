import json
import unittest
from unittest.mock import patch, MagicMock

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.errors


class ConcreteService(cloudlanguagetools.service.Service):
    """Minimal concrete subclass for testing the base Service methods."""
    def __init__(self):
        self.service = cloudlanguagetools.constants.Service.ElevenLabs


class TestGetTtsAudioBasePostRequest429(unittest.TestCase):

    def _make_mock_response(self, status_code, content_bytes):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.content = content_bytes
        return mock_response

    @patch('requests.post')
    def test_429_with_json_error_body(self, mock_post):
        """HTTP 429 with a JSON detail message raises RateLimitError with parsed message."""
        body = json.dumps({'detail': {'message': 'The system is experiencing heavy traffic'}}).encode()
        mock_post.return_value = self._make_mock_response(429, body)

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertIn('The system is experiencing heavy traffic', str(ctx.exception))

    @patch('requests.post')
    def test_429_with_non_json_body(self, mock_post):
        """HTTP 429 with a non-JSON body raises RateLimitError with default message."""
        mock_post.return_value = self._make_mock_response(429, b'rate limited')

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertIn('rate limited (429)', str(ctx.exception))

    @patch('requests.post')
    def test_other_4xx_raises_request_error(self, mock_post):
        """Non-429 4xx errors still raise RequestError (existing behavior)."""
        body = json.dumps({'detail': {'message': 'Bad request'}}).encode()
        mock_post.return_value = self._make_mock_response(400, body)

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RequestError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        # Should be RequestError, not RateLimitError
        self.assertNotIsInstance(ctx.exception, cloudlanguagetools.errors.RateLimitError)
