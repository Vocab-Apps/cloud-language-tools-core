import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import azure.cognitiveservices.speech

import cloudlanguagetools.azure
import cloudlanguagetools.errors
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


def _build_failed_synth_result(error_details):
    result = MagicMock()
    result.reason = azure.cognitiveservices.speech.ResultReason.Canceled
    result.cancellation_details.reason = azure.cognitiveservices.speech.CancellationReason.Error
    result.cancellation_details.error_details = error_details
    return result


class TestAzureGetTtsAudioErrors:
    def _make_service(self):
        service = cloudlanguagetools.azure.AzureService()
        service.configure({'key': 'fake-key', 'region': 'eastus'})
        return service

    @patch('cloudlanguagetools.azure.azure.cognitiveservices.speech.SpeechSynthesizer')
    @patch('cloudlanguagetools.azure.azure.cognitiveservices.speech.SpeechConfig')
    def test_first_chunk_timeout_raises_timeout_error(self, mock_speech_config, mock_synthesizer_cls):
        synthesizer = mock_synthesizer_cls.return_value
        synthesizer.speak_ssml.return_value = _build_failed_synth_result(
            'USP error: timeout waiting for the first audio chunk'
        )

        service = self._make_service()
        with pytest.raises(cloudlanguagetools.errors.TimeoutError) as exc_info:
            service.get_tts_audio('hello', {'name': 'ja-JP-Nanami:DragonHDLatestNeural'}, {})

        assert 'timeout waiting for the first audio chunk' in str(exc_info.value)

    @patch('cloudlanguagetools.azure.azure.cognitiveservices.speech.SpeechSynthesizer')
    @patch('cloudlanguagetools.azure.azure.cognitiveservices.speech.SpeechConfig')
    def test_other_error_raises_request_error(self, mock_speech_config, mock_synthesizer_cls):
        synthesizer = mock_synthesizer_cls.return_value
        synthesizer.speak_ssml.return_value = _build_failed_synth_result(
            'WebSocket connection closed unexpectedly'
        )

        service = self._make_service()
        with pytest.raises(cloudlanguagetools.errors.RequestError) as exc_info:
            service.get_tts_audio('hello', {'name': 'ja-JP-Nanami:DragonHDLatestNeural'}, {})

        assert 'WebSocket connection closed unexpectedly' in str(exc_info.value)
        assert not isinstance(exc_info.value, cloudlanguagetools.errors.TimeoutError)
