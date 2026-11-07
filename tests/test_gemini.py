import os
import sys
import io
import base64
import wave
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import magic
import pydub
import cloudlanguagetools.gemini
import cloudlanguagetools.configuration
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.errors
import cloudlanguagetools.options


def build_wav_bytes(duration_seconds=0.2, sample_rate=24000):
    """Build a short silent 16-bit mono WAV."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b'\x00\x00' * int(duration_seconds * sample_rate))
    return buffer.getvalue()


def build_generate_content_response(audio_bytes, mime_type='audio/wav'):
    return {
        'candidates': [{
            'content': {
                'role': 'model',
                'parts': [{
                    'inlineData': {
                        'mimeType': mime_type,
                        'data': base64.b64encode(audio_bytes).decode('ascii'),
                    }
                }]
            },
            'finishReason': 'STOP',
        }]
    }


def fake_http_response(status_code, json_data=None, text=''):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    if json_data is None:
        response.json.side_effect = ValueError('no json')
    else:
        response.json.return_value = json_data
    return response


@patch('cloudlanguagetools.gemini.requests.post')
class TestGeminiGenerateContent(unittest.TestCase):
    """All Gemini models go through the Gemini API generateContent REST endpoint, with an API key."""

    VOICE_KEY = {'name': 'Kore'}

    def setUp(self):
        self.service = cloudlanguagetools.gemini.GeminiService()
        self.service.configure(cloudlanguagetools.configuration.GeminiConfig(api_key='gemini-key'))
        self.wav_bytes = build_wav_bytes()

    def get_request(self, mock_post):
        self.assertEqual(mock_post.call_count, 1)
        args, kwargs = mock_post.call_args
        return args[0], kwargs

    def test_default_model_is_3_8_flash(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        self.service.get_tts_audio('hello', self.VOICE_KEY, {})

        url, kwargs = self.get_request(mock_post)
        self.assertEqual(url, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent')
        # the key goes in a header, never in the URL
        self.assertEqual(kwargs['headers'], {'x-goog-api-key': 'gemini-key'})
        self.assertEqual(kwargs['timeout'], cloudlanguagetools.constants.RequestTimeoutLong)

    def test_request_body_minimal(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        self.service.get_tts_audio('hello', self.VOICE_KEY, {'model': 'gemini-3.8-flash-lite-tts'})

        url, kwargs = self.get_request(mock_post)
        self.assertIn('gemini-3.8-flash-lite-tts:generateContent', url)
        self.assertEqual(kwargs['json'], {
            'contents': [{'role': 'user', 'parts': [{'text': 'hello'}]}],
            'generationConfig': {
                'responseModalities': ['AUDIO'],
                'speechConfig': {'voiceConfig': {'voice': 'Kore'}},
            }
        })

    def test_request_body_prompt_and_language_code(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        self.service.get_tts_audio('bonjour', self.VOICE_KEY,
            {'model': 'gemini-3.8-flash-tts', 'prompt': 'calm and warm', 'language_code': 'fr-FR'})

        url, kwargs = self.get_request(mock_post)
        body = kwargs['json']
        self.assertEqual(body['contents'][0]['parts'][0], {'text': 'bonjour', 'speechMetadata': {'style': 'calm and warm'}})
        self.assertEqual(body['generationConfig']['speechConfig'], {'voiceConfig': {'voice': 'Kore'}, 'languageCode': 'fr-FR'})

    def test_wav_response_is_encoded_to_mp3_by_default(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        audio_temp_file = self.service.get_tts_audio('hello', self.VOICE_KEY, {})

        self.assertEqual(magic.from_file(audio_temp_file.name, mime=True), 'audio/mpeg')
        audio_segment = pydub.AudioSegment.from_file(audio_temp_file.name, format='mp3')
        self.assertAlmostEqual(len(audio_segment) / 1000, 0.2, delta=0.1)

    def test_mp3_hq_response(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        audio_temp_file = self.service.get_tts_audio('hello', self.VOICE_KEY, {'format': 'mp3_hq'})

        self.assertEqual(magic.from_file(audio_temp_file.name, mime=True), 'audio/mpeg')

    def test_wav_response_passthrough(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        audio_temp_file = self.service.get_tts_audio('hello', self.VOICE_KEY, {'format': 'wav'})

        with open(audio_temp_file.name, 'rb') as f:
            self.assertEqual(f.read(), self.wav_bytes)

    def test_ogg_opus_response(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        audio_temp_file = self.service.get_tts_audio('hello', self.VOICE_KEY, {'format': 'ogg_opus'})

        self.assertIn('ogg', magic.from_file(audio_temp_file.name, mime=True))

    def test_headerless_pcm_response_is_wrapped(self, mock_post):
        # 0.2s of 16-bit mono silence at 16 kHz, without a RIFF header
        pcm_bytes = b'\x00\x00' * int(0.2 * 16000)
        mock_post.return_value = fake_http_response(200,
            build_generate_content_response(pcm_bytes, mime_type='audio/L16;codec=pcm;rate=16000'))

        audio_temp_file = self.service.get_tts_audio('hello', self.VOICE_KEY, {'format': 'wav'})

        with wave.open(audio_temp_file.name, 'rb') as wav:
            self.assertEqual(wav.getframerate(), 16000)
            self.assertEqual(wav.getnchannels(), 1)
            self.assertEqual(wav.getsampwidth(), 2)
            self.assertEqual(wav.getnframes(), int(0.2 * 16000))

    def test_older_model_request(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))

        self.service.get_tts_audio('hello', self.VOICE_KEY,
            {'model': 'gemini-2.5-flash-tts', 'prompt': 'Say cheerfully', 'language_code': 'en-US'})

        url, kwargs = self.get_request(mock_post)
        # library model name mapped to the Gemini API name
        self.assertEqual(url, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent')
        body = kwargs['json']
        # older models reject speechMetadata, the style prompt is a text prefix
        self.assertEqual(body['contents'][0]['parts'][0], {'text': 'Say cheerfully: hello'})
        self.assertEqual(body['generationConfig']['speechConfig'],
            {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': 'Kore'}}, 'languageCode': 'en-US'})

    def test_model_names(self, mock_post):
        mock_post.return_value = fake_http_response(200, build_generate_content_response(self.wav_bytes))
        expected = {
            'gemini-3.8-flash-tts': 'gemini-3.8-flash-tts',
            'gemini-3.8-flash-lite-tts': 'gemini-3.8-flash-lite-tts',
            'gemini-3.1-flash-tts-preview': 'gemini-3.1-flash-tts-preview',
            'gemini-2.5-flash-tts': 'gemini-2.5-flash-preview-tts',
            'gemini-2.5-pro-tts': 'gemini-2.5-pro-preview-tts',
        }
        for model, api_model in expected.items():
            self.service.get_tts_audio('hello', self.VOICE_KEY, {'model': model})
            self.assertTrue(mock_post.call_args.args[0].endswith(f'/models/{api_model}:generateContent'), model)

    def test_unsupported_model_raises_input_error(self, mock_post):
        # gemini-2.5-flash-lite-preview-tts was only served by Cloud Text-to-Speech
        for model in ['gemini-2.5-flash-lite-preview-tts', 'no-such-model']:
            with self.assertRaises(cloudlanguagetools.errors.InputError):
                self.service.get_tts_audio('hello', self.VOICE_KEY, {'model': model})
        mock_post.assert_not_called()

    def test_unconfigured_raises_authentication_error(self, mock_post):
        with self.assertRaises(cloudlanguagetools.errors.AuthenticationError):
            cloudlanguagetools.gemini.GeminiService().get_tts_audio('hello', self.VOICE_KEY, {})
        mock_post.assert_not_called()

    def test_rate_limit_with_retry_info(self, mock_post):
        mock_post.return_value = fake_http_response(429, {'error': {
            'code': 429,
            'message': 'Resource exhausted',
            'status': 'RESOURCE_EXHAUSTED',
            'details': [{'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '20s'}],
        }}, text='rate limited')

        with self.assertRaises(cloudlanguagetools.errors.RateLimitRetryAfterError) as context:
            self.service.get_tts_audio('hello', self.VOICE_KEY, {})
        self.assertEqual(context.exception.retry_after, 20)

    def test_rate_limit_without_retry_info(self, mock_post):
        mock_post.return_value = fake_http_response(429, {'error': {'code': 429, 'message': 'Resource exhausted'}})

        with self.assertRaises(cloudlanguagetools.errors.RateLimitRetryAfterError) as context:
            self.service.get_tts_audio('hello', self.VOICE_KEY, {})
        self.assertEqual(context.exception.retry_after, cloudlanguagetools.gemini.DEFAULT_RATE_LIMIT_RETRY_AFTER)

    def test_bad_request_raises_input_error(self, mock_post):
        mock_post.return_value = fake_http_response(400, {'error': {'code': 400, 'message': 'Voice not found'}})

        with self.assertRaises(cloudlanguagetools.errors.InputError):
            self.service.get_tts_audio('hello', {'name': 'non existent'}, {})

    def test_forbidden_raises_authentication_error(self, mock_post):
        mock_post.return_value = fake_http_response(403, {'error': {'code': 403, 'message': 'API key not valid'}})

        with self.assertRaisesRegex(cloudlanguagetools.errors.AuthenticationError, 'Gemini API key'):
            self.service.get_tts_audio('hello', self.VOICE_KEY, {})

    def test_server_error_raises_request_error(self, mock_post):
        mock_post.return_value = fake_http_response(503, None, text='Service Unavailable')

        with self.assertRaises(cloudlanguagetools.errors.RequestError):
            self.service.get_tts_audio('hello', self.VOICE_KEY, {})

    def test_read_timeout_raises_timeout_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ReadTimeout('timed out')

        with self.assertRaises(cloudlanguagetools.errors.TimeoutError):
            self.service.get_tts_audio('hello', self.VOICE_KEY, {})

    def test_no_candidates_raises_request_error(self, mock_post):
        mock_post.return_value = fake_http_response(200, {'candidates': [], 'promptFeedback': {'blockReason': 'SAFETY'}})

        with self.assertRaises(cloudlanguagetools.errors.RequestError) as context:
            self.service.get_tts_audio('hello', self.VOICE_KEY, {})
        self.assertIn('SAFETY', str(context.exception))

    def test_no_audio_part_raises_request_error(self, mock_post):
        mock_post.return_value = fake_http_response(200, {'candidates': [{'content': {'parts': []}, 'finishReason': 'SAFETY'}]})

        with self.assertRaises(cloudlanguagetools.errors.RequestError) as context:
            self.service.get_tts_audio('hello', self.VOICE_KEY, {})
        self.assertIn('SAFETY', str(context.exception))


class TestGeminiVoiceList(unittest.TestCase):

    def test_voice_list_options(self):
        voices = cloudlanguagetools.gemini.GeminiService().get_tts_voice_list_v3()
        self.assertEqual(len(voices), 30)
        for voice in voices:
            model_option = voice.options['model']
            self.assertEqual(model_option['default'], 'gemini-3.8-flash-tts')
            self.assertEqual(model_option['values'][:2], ['gemini-3.8-flash-tts', 'gemini-3.8-flash-lite-tts'])
            self.assertNotIn('gemini-2.5-flash-lite-preview-tts', model_option['values'])
            self.assertIn(cloudlanguagetools.languages.AudioLanguage.ig_NG, voice.audio_languages)
            self.assertIn(cloudlanguagetools.languages.AudioLanguage.en_US, voice.audio_languages)


if __name__ == '__main__':
    unittest.main()
