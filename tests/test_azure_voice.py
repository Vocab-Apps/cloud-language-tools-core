import pytest

from cloudlanguagetools.azure import build_dragonhd_voice_attrs, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_TOP_K, DEFAULT_CFG_SCALE


class TestBuildDragonhdVoiceAttrs:
    def test_non_dragonhd_voice(self):
        voice_key = {'name': 'Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)', 'voice_type': 'Neural'}
        result = build_dragonhd_voice_attrs(voice_key, {})
        assert result == 'name="Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)"'

    def test_dragonhd_all_defaults(self):
        voice_key = {'name': 'DragonHD-en-US', 'voice_type': 'NeuralHD'}
        options = {
            'temperature': DEFAULT_TEMPERATURE,
            'top_p': DEFAULT_TOP_P,
            'top_k': DEFAULT_TOP_K,
            'cfg_scale': DEFAULT_CFG_SCALE,
        }
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US"'

    def test_dragonhd_no_options(self):
        voice_key = {'name': 'DragonHD-en-US', 'voice_type': 'NeuralHD'}
        result = build_dragonhd_voice_attrs(voice_key, {})
        assert result == 'name="DragonHD-en-US"'

    def test_dragonhd_one_param_changed(self):
        voice_key = {'name': 'DragonHD-en-US', 'voice_type': 'NeuralHD'}
        options = {'temperature': 0.9}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US" parameters="temperature=0.9"'

    def test_dragonhd_multiple_params_changed(self):
        voice_key = {'name': 'DragonHD-en-US', 'voice_type': 'NeuralHD'}
        options = {'temperature': 0.5, 'top_k': 30}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US" parameters="temperature=0.5;top_k=30"'

    def test_dragonhd_all_params_changed(self):
        voice_key = {'name': 'DragonHD-en-US', 'voice_type': 'NeuralHD'}
        options = {'temperature': 0.5, 'top_p': 0.9, 'top_k': 30, 'cfg_scale': 1.8}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-en-US" parameters="temperature=0.5;top_p=0.9;top_k=30;cfg_scale=1.8"'

    def test_neuralhd_voice_type_without_dragonhd_name(self):
        voice_key = {'name': 'SomeOtherHDVoice', 'voice_type': 'NeuralHD'}
        options = {'cfg_scale': 1.8}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="SomeOtherHDVoice" parameters="cfg_scale=1.8"'

    def test_dragonhd_in_name_without_neuralhd_type(self):
        voice_key = {'name': 'DragonHD-zh-CN', 'voice_type': 'SomeType'}
        options = {'top_p': 0.5}
        result = build_dragonhd_voice_attrs(voice_key, options)
        assert result == 'name="DragonHD-zh-CN" parameters="top_p=0.5"'
