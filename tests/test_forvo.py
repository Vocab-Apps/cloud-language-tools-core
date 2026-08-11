import os
import sys
import unittest
from unittest.mock import patch, MagicMock

import requests
import urllib3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.forvo
import cloudlanguagetools.errors
import cloudlanguagetools.languages
import cloudlanguagetools.constants

AudioLanguage = cloudlanguagetools.languages.AudioLanguage


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

    @patch('cloudlanguagetools.forvo.requests.get')
    def test_forvo_false_body_raises_not_found(self, mock_get):
        """When Forvo returns a bare `false` json body (HTTP 200) for a word
        with no pronunciations, raise NotFoundError rather than RequestError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = 'https://apicommercial.forvo.com/some-endpoint'
        mock_response.content = b'false'
        mock_response.json.return_value = False
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(cloudlanguagetools.errors.NotFoundError) as ctx:
            self.service.get_tts_audio('0', self.voice_key, self.options)

        self.assertIn('0', str(ctx.exception))

    @patch('cloudlanguagetools.forvo.requests.get')
    def test_forvo_word_mismatch_raises_not_found(self, mock_get):
        """When Forvo returns a pronunciation for a similar but different word
        (e.g. Thai คล่อง requested, คลอง returned -- differing by a tone mark),
        raise NotFoundError instead of serving the wrong word's audio. See issue #322."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = 'https://apicommercial.forvo.com/some-endpoint'
        mock_response.json.return_value = {
            'items': [{
                'word': 'คลอง',
                'original': 'คลอง',
                'pathmp3': 'https://apicommercial.forvo.com/audio/should_not_be_fetched',
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(cloudlanguagetools.errors.NotFoundError) as ctx:
            self.service.get_tts_audio('คล่อง', self.voice_key, self.options)

        self.assertIn('คล่อง', str(ctx.exception))
        # the mp3 download must not happen when the word mismatches
        self.assertEqual(mock_get.call_count, 1)

    @patch('cloudlanguagetools.forvo.requests.get')
    def test_forvo_read_timeout_raises_timeout(self, mock_get):
        """A read timeout from requests.exceptions.Timeout maps to TimeoutError."""
        mock_get.side_effect = requests.exceptions.ReadTimeout('Read timed out.')

        with self.assertRaises(cloudlanguagetools.errors.TimeoutError):
            self.service.get_tts_audio('word', self.voice_key, self.options)

    @patch('cloudlanguagetools.forvo.requests.get')
    def test_forvo_body_read_timeout_raises_timeout(self, mock_get):
        """When requests wraps urllib3 ReadTimeoutError in ConnectionError
        (timeout during response body read), it must still map to TimeoutError."""
        wrapped = urllib3.exceptions.ReadTimeoutError(
            None, None, "Read timed out."
        )
        mock_get.side_effect = requests.exceptions.ConnectionError(wrapped)

        with self.assertRaises(cloudlanguagetools.errors.TimeoutError):
            self.service.get_tts_audio('word', self.voice_key, self.options)


class TestForvoChineseDialects(unittest.TestCase):
    """Forvo's language-list lumps every chinese variety into the `zh` bucket, but
    word-pronunciations accepts far more codes. These tests pin the per-audio_language
    overrides that carry the dialect through to the API request."""

    def setUp(self):
        self.service = cloudlanguagetools.forvo.ForvoService()
        self.service.key = 'fake_key'

    def test_swahili_dialects_use_their_country_codes(self):
        voices = self.service.get_voices_for_language_entry({'code': 'sw'})
        country_codes = {
            voice.audio_language: voice.country_code
            for voice in voices
        }

        self.assertEqual(country_codes[AudioLanguage.sw_KE], 'KEN')
        self.assertEqual(country_codes[AudioLanguage.sw_TZ], 'TZA')

    def get_language_code_map(self, forvo_language_code):
        """audio_language -> voice_key['language_code'] for one language-list entry.
        Only needs the `code` field, and touches no network."""
        voices = self.service.get_voices_for_language_entry({'code': forvo_language_code})
        return {voice.audio_language: voice.get_voice_key()['language_code'] for voice in voices}

    def test_mandarin_bucket_dialects_get_distinct_forvo_codes(self):
        """Each chinese variety must request its own forvo language code, not `zh`."""
        language_code_map = self.get_language_code_map('zh')

        expected = {
            AudioLanguage.zh_CN: 'zh',
            AudioLanguage.nan_CN: 'nan',
            AudioLanguage.wuu_CN: 'wuu',
            AudioLanguage.zh_CN_liaoning: 'jliu',
            AudioLanguage.zh_CN_shandong: 'jlua',
            AudioLanguage.zh_CN_anhui: 'juai',
            AudioLanguage.zh_CN_sichuan: 'xghu',
            AudioLanguage.zh_CN_hunan: 'hsn',
            AudioLanguage.hak_CN: 'hak',
            AudioLanguage.gan_CN: 'gan',
            AudioLanguage.cjy_CN: 'cjy',
            AudioLanguage.cdo_CN: 'cdo',
            AudioLanguage.cdo_CN_fuzhou: 'fzho',
            AudioLanguage.wuu_CN_shanghai: 'jusi',
            AudioLanguage.wuu_CN_changzhou: 'plig',
            AudioLanguage.ltc_CN: 'ltc',
        }
        for audio_language, forvo_language_code in expected.items():
            self.assertEqual(language_code_map.get(audio_language), forvo_language_code,
                             f'{audio_language.name} should request language/{forvo_language_code}')

    def test_cantonese_bucket_dialects_get_distinct_forvo_codes(self):
        language_code_map = self.get_language_code_map('yue')

        self.assertEqual(language_code_map.get(AudioLanguage.yue_CN), 'yue')
        self.assertEqual(language_code_map.get(AudioLanguage.zh_HK), 'yue')
        self.assertEqual(language_code_map.get(AudioLanguage.yue_CN_toisan), 'tisa')

    def test_untargetable_audio_languages_produce_no_voice(self):
        """Forvo has no code for zhongyuan/lanyin mandarin, and zh_CN_guangxi would
        collide with zh_CN_sichuan on `xghu`. Don't advertise voices that can only
        serve standard mandarin under a dialect label."""
        language_code_map = self.get_language_code_map('zh')

        for audio_language in [AudioLanguage.zh_CN_henan, AudioLanguage.zh_CN_shaanxi,
                               AudioLanguage.zh_CN_gansu, AudioLanguage.zh_CN_guangxi]:
            self.assertNotIn(audio_language, language_code_map,
                             f'{audio_language.name} cannot be targeted on the forvo api')

    def test_voice_keys_are_unique(self):
        """The original bug: every chinese voice shared one voice_key, so every dialect
        selection issued the identical request."""
        for forvo_language_code in ['zh', 'yue']:
            voices = self.service.get_voices_for_language_entry({'code': forvo_language_code})
            voice_keys = [tuple(sorted(voice.get_voice_key().items())) for voice in voices]
            self.assertEqual(len(voice_keys), len(set(voice_keys)),
                             f'duplicate voice keys in the forvo {forvo_language_code} bucket')

    @patch('cloudlanguagetools.forvo.requests.get')
    def test_dialect_voices_request_distinct_urls(self, mock_get):
        """End to end: two chinese audio languages must produce different forvo urls."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = 'https://apicommercial.forvo.com/some-endpoint'
        mock_response.json.return_value = {'items': []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        voices = self.service.get_voices_for_language_entry({'code': 'zh'})
        voice_by_audio_language = {voice.audio_language: voice for voice in voices
                                   if voice.gender == cloudlanguagetools.constants.Gender.Male}

        requested_urls = {}
        for audio_language in [AudioLanguage.zh_CN, AudioLanguage.nan_CN]:
            voice_key = voice_by_audio_language[audio_language].get_voice_key()
            with self.assertRaises(cloudlanguagetools.errors.NotFoundError):
                self.service.get_tts_audio('你好', voice_key, {})
            requested_urls[audio_language] = mock_get.call_args[0][0]

        self.assertIn('/language/zh/', requested_urls[AudioLanguage.zh_CN])
        self.assertIn('/language/nan/', requested_urls[AudioLanguage.nan_CN])
        self.assertNotEqual(requested_urls[AudioLanguage.zh_CN], requested_urls[AudioLanguage.nan_CN])
