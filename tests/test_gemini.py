import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import google.api_core.exceptions
import cloudlanguagetools.gemini
import cloudlanguagetools.errors


class TestGeminiTtsInvalidArgument(unittest.TestCase):

    VOICE_KEY = {'name': 'non existent'}
    OPTIONS = {}

    @patch.object(cloudlanguagetools.gemini.GeminiService, 'get_client')
    def test_invalid_argument_raises_input_error(self, mock_get_client):
        """InvalidArgument from Gemini (e.g. nonexistent voice) must raise InputError to prevent client retries."""
        exc = google.api_core.exceptions.InvalidArgument(
            "Voice 'non existent' does not exist. Is it misspelled?"
        )

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = exc
        mock_get_client.return_value = mock_client

        service = cloudlanguagetools.gemini.GeminiService()
        with self.assertRaises(cloudlanguagetools.errors.InputError):
            service.get_tts_audio('hello', self.VOICE_KEY, self.OPTIONS)


if __name__ == '__main__':
    unittest.main()
