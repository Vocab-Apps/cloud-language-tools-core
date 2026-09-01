import os
import sys
from unittest.mock import patch, MagicMock

import pytest
import requests
from pydub import AudioSegment

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.azure
import cloudlanguagetools.errors
import cloudlanguagetools.options
from cloudlanguagetools.azure import build_dragonhd_voice_attrs, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_TOP_K, DEFAULT_CFG_SCALE


class TestBuildDragonhdVoiceAttrs:
    def test_non_dragonhd_voice(self):
        voice_key = {'name': 'Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)'}
        result = build_dragonhd_voice_attrs(voice_key, {})
        assert result == 'name="Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)"'

    def test_dragonhd_all_defaults(self):
        voice_key = {'name': 'DragonHD-en-US'}
        options = {
            'temperature': DEFAULT_TEMPERATURE,
            'top_p': DEFAULT_TOP_P,
            'top_k': DEFAULT_TOP_K,
            'cfg_scale': DEFAULT_CFG_SCALE,
        }
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US"'

    def test_dragonhd_no_options(self):
        voice_key = {'name': 'DragonHD-en-US'}
        result = build_dragonhd_voice_attrs(voice_key, {})
        assert result == 'name="DragonHD-en-US"'

    def test_dragonhd_one_param_changed(self):
        voice_key = {'name': 'DragonHD-en-US'}
        options = {'temperature': 0.9}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US" parameters="temperature=0.9"'

    def test_dragonhd_multiple_params_changed(self):
        voice_key = {'name': 'DragonHD-en-US'}
        options = {'temperature': 0.5, 'top_k': 30}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US" parameters="temperature=0.5;top_k=30"'

    def test_dragonhd_all_params_changed(self):
        voice_key = {'name': 'DragonHD-en-US'}
        options = {'temperature': 0.5, 'top_p': 0.9, 'top_k': 30, 'cfg_scale': 1.8}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US" parameters="temperature=0.5;top_p=0.9;top_k=30;cfg_scale=1.8"'

    def test_non_dragonhd_name_no_params(self):
        voice_key = {'name': 'SomeOtherHDVoice'}
        options = {'cfg_scale': 1.8}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="SomeOtherHDVoice"'


_MISSING = object()


def _build_response(status_code=200, content=b'', text='', json_data=_MISSING):
    response = MagicMock()
    response.status_code = status_code
    response.content = content
    response.text = text
    response.reason = 'Bad Request' if status_code >= 400 else 'OK'
    if json_data is _MISSING:
        response.json.side_effect = ValueError('not JSON')
    else:
        response.json.return_value = json_data
    return response


class TestAzureGetTtsAudioErrors:
    def _make_service(self):
        service = cloudlanguagetools.azure.AzureService()
        service.configure({'key': 'fake-key', 'region': 'eastus'})
        return service

    @patch('cloudlanguagetools.azure.requests.post')
    def test_first_chunk_timeout_response_raises_timeout_error(self, mock_post):
        mock_post.return_value = _build_response(
            status_code=400,
            text='USP error: timeout waiting for the first audio chunk',
        )

        service = self._make_service()
        with pytest.raises(cloudlanguagetools.errors.TimeoutError) as exc_info:
            service.get_tts_audio('hello', {'name': 'ja-JP-Nanami:DragonHDLatestNeural'}, {})

        assert 'timeout waiting for the first audio chunk' in str(exc_info.value)

    @patch('cloudlanguagetools.azure.requests.post')
    def test_plain_text_error_body_is_in_request_error(self, mock_post):
        mock_post.return_value = _build_response(
            status_code=400,
            text='Invalid SSML: voice name is not valid',
        )

        service = self._make_service()
        with pytest.raises(cloudlanguagetools.errors.RequestError) as exc_info:
            service.get_tts_audio('hello', {'name': 'ja-JP-Nanami:DragonHDLatestNeural'}, {})

        assert 'Invalid SSML: voice name is not valid' in str(exc_info.value)
        assert not isinstance(exc_info.value, cloudlanguagetools.errors.TimeoutError)

    @patch('cloudlanguagetools.azure.requests.post')
    def test_nested_json_error_message_is_in_request_error(self, mock_post):
        mock_post.return_value = _build_response(
            status_code=401,
            text='full response body',
            json_data={
                'error': {
                    'code': 'Unauthorized',
                    'message': 'The subscription key is invalid.',
                }
            },
        )

        service = self._make_service()
        with pytest.raises(cloudlanguagetools.errors.RequestError) as exc_info:
            service.get_tts_audio('hello', {'name': 'en-US-JennyNeural'}, {})

        assert 'The subscription key is invalid.' in str(exc_info.value)

    @patch('cloudlanguagetools.azure.requests.post')
    def test_network_timeout_raises_timeout_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ReadTimeout('read timed out')

        service = self._make_service()
        with pytest.raises(cloudlanguagetools.errors.TimeoutError) as exc_info:
            service.get_tts_audio('hello', {'name': 'en-US-JennyNeural'}, {})

        assert 'timed out' in str(exc_info.value)

    @patch('cloudlanguagetools.azure.requests.post')
    def test_deprecated_standard_voice_is_rejected_without_request(self, mock_post):
        service = self._make_service()

        with pytest.raises(cloudlanguagetools.errors.RequestError) as exc_info:
            service.get_tts_audio(
                'hello',
                {
                    'name': (
                        'Microsoft Server Speech Text to Speech Voice '
                        '(ja-JP, HarukaRUS)'
                    )
                },
                {},
            )

        assert 'Unsupported Azure Standard voice' in str(exc_info.value)
        mock_post.assert_not_called()


class TestAzureGetTtsAudioRestRequest:
    def _make_service(self):
        service = cloudlanguagetools.azure.AzureService()
        service.configure({'key': 'fake-key', 'region': 'eastus'})
        return service

    @pytest.mark.parametrize(
        ('audio_format', 'expected_output_format'),
        [
            ('mp3', 'audio-24khz-96kbitrate-mono-mp3'),
            ('ogg_opus', 'ogg-48khz-16bit-mono-opus'),
            ('wav', 'riff-48khz-16bit-mono-pcm'),
        ],
    )
    @patch('cloudlanguagetools.azure.requests.post')
    def test_posts_ssml_and_returns_response_audio(
            self, mock_post, audio_format, expected_output_format):
        mock_post.return_value = _build_response(content=b'azure-audio')
        service = self._make_service()

        audio_file = service.get_tts_audio(
            'country & western',
            {'name': 'en-US-JennyNeural'},
            {'format': audio_format},
        )
        try:
            assert audio_file.read() == b'azure-audio'
            assert audio_file.name.endswith(f'.{audio_format}')
        finally:
            audio_file.close()

        args, kwargs = mock_post.call_args
        assert args == ('https://eastus.tts.speech.microsoft.com/cognitiveservices/v1',)
        assert kwargs['headers'] == {
            'Ocp-Apim-Subscription-Key': 'fake-key',
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': expected_output_format,
            'User-Agent': 'cloud-language-tools',
        }
        assert b'<voice name="en-US-JennyNeural">' in kwargs['data']
        assert b'country &amp; western' in kwargs['data']
        assert kwargs['timeout'] == cloudlanguagetools.constants.RequestTimeout


class TestAzureSpeechToTextRestRequest:
    def _make_service(self):
        service = cloudlanguagetools.azure.AzureService()
        service.configure({'key': 'fake-key', 'region': 'eastus'})
        return service

    @patch('cloudlanguagetools.azure.pydub.AudioSegment.from_wav')
    @patch('cloudlanguagetools.azure.requests.post')
    def test_posts_pcm_wav_and_returns_display_text(self, mock_post, mock_from_wav):
        mock_from_wav.return_value = AudioSegment.silent(duration=100)
        mock_post.return_value = _build_response(
            text='success response',
            json_data={
                'RecognitionStatus': 'Success',
                'DisplayText': 'Hello world.',
            },
        )
        service = self._make_service()

        result = service.speech_to_text(
            'audio.wav',
            cloudlanguagetools.options.AudioFormat.wav,
            language='en-GB',
        )

        assert result == 'Hello world.'
        args, kwargs = mock_post.call_args
        assert args == (
            'https://eastus.stt.speech.microsoft.com/'
            'speech/recognition/conversation/cognitiveservices/v1',
        )
        assert kwargs['headers'] == {
            'Ocp-Apim-Subscription-Key': 'fake-key',
            'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000',
            'Accept': 'application/json',
        }
        assert kwargs['params'] == {'language': 'en-GB', 'format': 'simple'}
        assert kwargs['data'].startswith(b'RIFF')
        assert kwargs['timeout'] == cloudlanguagetools.constants.RequestTimeout

    @patch('cloudlanguagetools.azure.pydub.AudioSegment.from_wav')
    @patch('cloudlanguagetools.azure.requests.post')
    def test_http_error_includes_azure_json_message(self, mock_post, mock_from_wav):
        mock_from_wav.return_value = AudioSegment.silent(duration=100)
        mock_post.return_value = _build_response(
            status_code=400,
            text='full response body',
            json_data={
                'error': {
                    'code': 'InvalidRequest',
                    'message': 'The audio file is invalid.',
                }
            },
        )
        service = self._make_service()

        with pytest.raises(cloudlanguagetools.errors.RequestError) as exc_info:
            service.speech_to_text(
                'audio.wav',
                cloudlanguagetools.options.AudioFormat.wav,
                language='en-US',
            )

        assert 'The audio file is invalid.' in str(exc_info.value)

    @patch('cloudlanguagetools.azure.pydub.AudioSegment.from_wav')
    @patch('cloudlanguagetools.azure.requests.post')
    def test_no_match_raises_request_error(self, mock_post, mock_from_wav):
        mock_from_wav.return_value = AudioSegment.silent(duration=100)
        mock_post.return_value = _build_response(
            text='no match response',
            json_data={'RecognitionStatus': 'NoMatch'},
        )
        service = self._make_service()

        with pytest.raises(cloudlanguagetools.errors.RequestError) as exc_info:
            service.speech_to_text(
                'audio.wav',
                cloudlanguagetools.options.AudioFormat.wav,
                language='en-US',
            )

        assert 'NoMatch' in str(exc_info.value)


class TestAzureTransliterationRequest:
    def test_chinese_language_id_follows_source_script(self):
        service = cloudlanguagetools.azure.AzureService()
        service.transliteration = MagicMock(return_value='講話')

        result = service.get_transliteration(
            '讲话',
            {
                'language_id': 'zh-Hant',
                'from_script': 'Hans',
                'to_script': 'Hant',
            },
        )

        assert result == '講話'
        service.transliteration.assert_called_once_with(
            '讲话', 'zh-Hans', 'Hans', 'Hant')
