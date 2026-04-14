import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.forvo
import cloudlanguagetools.errors


class TestForvoGetTtsAudio(unittest.TestCase):
    def setUp(self):
        self.service = cloudlanguagetools.forvo.ForvoService()
        self.service.key = 'fake_key'
        self.voice_key = {'language_code': 'en', 'country_code': 'ANY'}
        self.options = {}

    @patch('cloudlanguagetools.forvo.requests.get')
    def test_forvo_404_redirect_raises_not_found(self, mock_get):
        """When Forvo redirects the API request to its 404 page, raise NotFoundError."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.url = 'https://forvo.com/404'
        mock_response.content = b'Forbidden'
        mock_get.return_value = mock_response

        with self.assertRaises(cloudlanguagetools.errors.NotFoundError) as ctx:
            self.service.get_tts_audio('nonexistent', self.voice_key, self.options)

        self.assertIn('nonexistent', str(ctx.exception))

    @patch('cloudlanguagetools.forvo.requests.get')
    def test_forvo_empty_items_raises_not_found(self, mock_get):
        """When Forvo returns an empty items list, raise NotFoundError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = 'https://apicommercial.forvo.com/some-endpoint'
        mock_response.json.return_value = {'items': []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(cloudlanguagetools.errors.NotFoundError) as ctx:
            self.service.get_tts_audio('rareword', self.voice_key, self.options)

        self.assertIn('rareword', str(ctx.exception))
