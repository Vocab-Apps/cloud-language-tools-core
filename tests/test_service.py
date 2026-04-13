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


def _make_mock_response(status_code, json_body=None, text_body=None):
    """Create a mock response. Provide json_body (dict/list/str) or text_body (str)."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    if json_body is not None:
        mock_response.json.return_value = json_body
        mock_response.text = json.dumps(json_body)
        mock_response.content = json.dumps(json_body).encode()
    else:
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = text_body or ''
        mock_response.content = (text_body or '').encode()
    return mock_response


class TestExtractErrorMessage(unittest.TestCase):
    """Tests for Service._extract_error_message."""

    def setUp(self):
        self.service = ConcreteService()

    def test_string_input(self):
        self.assertEqual(self.service._extract_error_message('some error'), 'some error')

    def test_dict_with_message_key(self):
        self.assertEqual(self.service._extract_error_message({'message': 'bad request'}), 'bad request')

    def test_dict_with_error_key(self):
        self.assertEqual(self.service._extract_error_message({'error': 'unauthorized'}), 'unauthorized')

    def test_dict_with_detail_key(self):
        self.assertEqual(self.service._extract_error_message({'detail': 'not found'}), 'not found')

    def test_dict_with_error_message_key(self):
        self.assertEqual(self.service._extract_error_message({'error_message': 'timeout'}), 'timeout')

    def test_nested_detail_message(self):
        """ElevenLabs-style: {"detail": {"message": "heavy traffic"}}"""
        data = {'detail': {'message': 'heavy traffic'}}
        self.assertEqual(self.service._extract_error_message(data), 'heavy traffic')

    def test_nested_error_dict(self):
        """{"error": {"message": "something went wrong"}}"""
        data = {'error': {'message': 'something went wrong'}}
        self.assertEqual(self.service._extract_error_message(data), 'something went wrong')

    def test_key_priority_message_first(self):
        """'message' is checked before 'error'."""
        data = {'message': 'from message', 'error': 'from error'}
        self.assertEqual(self.service._extract_error_message(data), 'from message')

    def test_dict_no_known_keys_falls_back_to_json_dump(self):
        data = {'code': 429, 'status': 'rate_limited'}
        self.assertEqual(self.service._extract_error_message(data), json.dumps(data))

    def test_list_input_falls_back_to_json_dump(self):
        data = ['error1', 'error2']
        self.assertEqual(self.service._extract_error_message(data), json.dumps(data))

    def test_integer_input_falls_back_to_json_dump(self):
        self.assertEqual(self.service._extract_error_message(42), '42')


class TestGetResponseErrorMessage(unittest.TestCase):
    """Tests for Service._get_response_error_message."""

    def setUp(self):
        self.service = ConcreteService()

    def test_json_response_with_message(self):
        response = _make_mock_response(400, json_body={'message': 'bad request'})
        self.assertEqual(self.service._get_response_error_message(response), 'bad request')

    def test_json_response_nested(self):
        response = _make_mock_response(429, json_body={'detail': {'message': 'heavy traffic'}})
        self.assertEqual(self.service._get_response_error_message(response), 'heavy traffic')

    def test_non_json_response_returns_text(self):
        response = _make_mock_response(500, text_body='Internal Server Error')
        self.assertEqual(self.service._get_response_error_message(response), 'Internal Server Error')

    def test_empty_non_json_response(self):
        response = _make_mock_response(502, text_body='')
        self.assertEqual(self.service._get_response_error_message(response), '')


class TestGetTtsAudioBasePostRequest(unittest.TestCase):

    @patch('requests.post')
    def test_429_with_json_detail_message(self, mock_post):
        """HTTP 429 with ElevenLabs-style JSON raises RateLimitError with parsed message."""
        mock_post.return_value = _make_mock_response(429, json_body={'detail': {'message': 'The system is experiencing heavy traffic'}})

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertIn('The system is experiencing heavy traffic', str(ctx.exception))
        self.assertIn('ElevenLabs', str(ctx.exception))

    @patch('requests.post')
    def test_429_with_plain_error_key(self, mock_post):
        """HTTP 429 with {"error": "msg"} raises RateLimitError with that message."""
        mock_post.return_value = _make_mock_response(429, json_body={'error': 'too many requests'})

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertIn('too many requests', str(ctx.exception))

    @patch('requests.post')
    def test_429_with_non_json_body(self, mock_post):
        """HTTP 429 with non-JSON body raises RateLimitError with text body."""
        mock_post.return_value = _make_mock_response(429, text_body='rate limited')

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertIn('rate limited', str(ctx.exception))

    @patch('requests.post')
    def test_400_with_json_message(self, mock_post):
        """HTTP 400 with JSON message raises RequestError."""
        mock_post.return_value = _make_mock_response(400, json_body={'message': 'invalid parameter'})

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RequestError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertNotIsInstance(ctx.exception, cloudlanguagetools.errors.RateLimitError)
        self.assertIn('invalid parameter', str(ctx.exception))

    @patch('requests.post')
    def test_400_with_non_json_body(self, mock_post):
        """HTTP 400 with non-JSON body raises RequestError with text."""
        mock_post.return_value = _make_mock_response(400, text_body='Bad Request')

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RequestError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertNotIsInstance(ctx.exception, cloudlanguagetools.errors.RateLimitError)
        self.assertIn('Bad Request', str(ctx.exception))

    @patch('requests.post')
    def test_500_raises_request_error(self, mock_post):
        """HTTP 500 raises RequestError."""
        mock_post.return_value = _make_mock_response(500, json_body={'error': 'internal server error'})

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RequestError) as ctx:
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})

        self.assertIn('internal server error', str(ctx.exception))

    @patch('requests.post')
    def test_429_is_not_caught_by_request_error_handler(self, mock_post):
        """RateLimitError from 429 must not be swallowed by the generic exception handler."""
        mock_post.return_value = _make_mock_response(429, json_body={'message': 'slow down'})

        service = ConcreteService()
        with self.assertRaises(cloudlanguagetools.errors.RateLimitError):
            service.get_tts_audio_base_post_request('https://example.com/tts', json={})
