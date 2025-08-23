import unittest
import logging
import random
import requests
import re
import sys
import os
import time
import magic
import pytest
import json
import time
import pprint
import functools
import tempfile
import backoff

import audio_utils

CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE = os.environ.get('CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE', 'no') == 'yes'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.options
import cloudlanguagetools.errors
from cloudlanguagetools.languages import Language
from cloudlanguagetools.languages import AudioLanguage
from cloudlanguagetools.constants import Service

logger = logging.getLogger(__name__)

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()

    return manager

BACKOFF_MAX_TIME=90

def skip_unreliable_clt_test():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE:
                pytest.skip(f'you must set CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes')
            return func(*args, **kwargs)
        return wrapper
    return decorator




@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_time=BACKOFF_MAX_TIME)
def get_tts_voice_list_json_with_retry(manager):
    return manager.get_tts_voice_list_json()

@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException, 
                      max_time=BACKOFF_MAX_TIME)
def get_tts_voice_list_v3_with_retry(manager):
    return manager.get_tts_voice_list_v3()

class TestAudio(unittest.TestCase):

    ENGLISH_INPUT_TEXT = 'This is the best restaurant in town.'
    FRENCH_INPUT_TEXT = 'Bonjour'
    SPANISH_INPUT_TEXT = 'Hola'
    JAPANESE_INPUT_TEXT = 'すみません'
    CHINESE_INPUT_TEXT = '你好'
    CHINESE_INPUT_TEXT_2 = '信用卡'
    KOREAN_INPUT_TEXT = '안녕하세요'

    @classmethod
    def setUpClass(cls):
        cls.manager = get_manager()
        cls.language_list = cls.manager.get_language_list()
        cls.voice_list = get_tts_voice_list_json_with_retry(cls.manager)
        cls.voice_list_v3 = get_tts_voice_list_v3_with_retry(cls.manager)
        
        import http.client as http_client                            
        http_client.HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True



    def get_voice_list_for_language(self, language):
        subset = [x for x in self.voice_list if x['language_code'] == language.name]
        return subset

    def get_voice_list_service_audio_language(self, service, audio_language):
        subset = [x for x in self.voice_list if x['audio_language_code'] == audio_language.name and x['service'] == service.name]
        return subset        

    def get_voice_list_service_audio_language_v3(self, service, audio_language):
        subset = [x for x in self.voice_list_v3 if audio_language in x.audio_languages and x.service == service]
        return subset                

    def get_voice_by_service_and_name(self, service: Service, voice_name) -> cloudlanguagetools.ttsvoice.TtsVoice_v3:
        subset = [x for x in self.voice_list_v3 if voice_name in x.name and x.service == service]
        num_voices = len(subset)
        self.assertEqual(num_voices, 1, msg=f'found {num_voices} voices for {service} and {voice_name}, expected 1')
        return subset[0]

    def get_voice_by_lambda(self, service: Service, filter_func, assert_unique=True):
        service_voices = [x for x in self.voice_list_v3 if x.service == service]
        subset = [x for x in service_voices if filter_func(x)]
        if assert_unique:
            self.assertEqual(len(subset), 1, pprint.pformat(subset))
        return subset[0]

    def verify_voice(self, voice, text, recognition_language):
        return self.verify_voice_internal(voice['voice_key'], voice['service'], text, recognition_language)

    def verify_voice_v3(self, voice, text, recognition_language):
        voice_key = voice.voice_key
        voice_service = voice.service.name
        return self.verify_voice_internal(voice_key, voice_service, text, recognition_language)

    @backoff.on_exception(backoff.expo,
                        cloudlanguagetools.errors.TransientError,
                        max_time=BACKOFF_MAX_TIME)
    def get_tts_audio_with_retry(self, text, voice_service, voice_key, options=None):
        if options is None:
            options = {}
        try:
            audio_temp_file = self.manager.get_tts_audio(text, voice_service, voice_key, options)
            return audio_temp_file
        except cloudlanguagetools.errors.RateLimitError as e:
            # Handle rate limit with custom wait time if available
            if e.retry_after:
                logger.info(f"Rate limited. Waiting {e.retry_after} seconds as requested by server")
                time.sleep(e.retry_after)
                # Retry once after waiting
                return self.manager.get_tts_audio(text, voice_service, voice_key, options)
            else:
                # Re-raise to let backoff handle it
                raise

    def verify_voice_internal(self, voice_key, voice_service, text, recognition_language):

        audio_temp_file = self.get_tts_audio_with_retry(text, voice_service, voice_key)

        # check file format
        is_mp3 = audio_utils.is_mp3_format(audio_temp_file.name)
        if not is_mp3:
            mime_type = magic.from_file(audio_temp_file.name)
            logger.error(f'found mime type: {mime_type}')
            # dump file to console
            f = open(audio_temp_file.name, "r")
            print(f.read())

        self.assertTrue(is_mp3)

        audio_format = cloudlanguagetools.options.AudioFormat.mp3

        self.recognize_and_verify_text(audio_temp_file, text, recognition_language, audio_format)


    def recognize_and_verify_text(self, 
                audio_temp_file: tempfile.NamedTemporaryFile, 
                expected_text: str,
                recognition_language: str,
                audio_format: cloudlanguagetools.options.AudioFormat):
        # recognize text
        # ==============
        sanitized_expected_text = audio_utils.sanitize_recognized_text(expected_text)
        # first, try openwhisper
        logger.info(f'attempting to recognize text using OpenAI. expected text: {sanitized_expected_text}')
        audio_text_openai = audio_utils.speech_to_text_openai(self.manager, audio_temp_file, audio_format)
        sanitized_openai_text = audio_utils.sanitize_recognized_text(audio_text_openai)
        if sanitized_expected_text == sanitized_openai_text:
            # openai text matches
            logger.info(f'found a match on OpenAI with {sanitized_openai_text}=={sanitized_expected_text}')
            return
        else:
            logger.warning(f'failed to recognize text using OpenAI. expected text: {sanitized_expected_text} got: {sanitized_openai_text}')

        # second, try azure
        logger.info(f'attempting to recognize text using Azure. expected text: {sanitized_expected_text}')
        audio_text = audio_utils.speech_to_text_azure_wav(self.manager, audio_temp_file, recognition_language, audio_format)
        sanitized_azure_text = audio_utils.sanitize_recognized_text(audio_text)
        self.assertEqual(sanitized_expected_text, sanitized_azure_text)

    def verify_service_audio_language(self, text, service, audio_language, recognition_language):
        """Legacy version using voice_list"""
        # logging.info(f'verify_service_audio: service: {service} audio_language: {audio_language}')
        voices = self.get_voice_list_service_audio_language(service, audio_language)
        self.assertGreaterEqual(len(voices), 1, f'at least one voice for service {service}, language {audio_language}')

        if service == Service.Google:
            # exclude Journey voices, they don't use the standard interface
            voices = [x for x in voices if 'Journey' not in x['voice_name']]

        # pick 3 random voices
        max_voices = 3
        if len(voices) > max_voices:
            voices = random.sample(voices, max_voices)
        for voice in voices:
            self.verify_voice(voice, text, recognition_language)

    def verify_service_audio_language_v3(self, text, service, audio_language, recognition_language):
        # logging.info(f'verify_service_audio: service: {service} audio_language: {audio_language}')
        voices = self.get_voice_list_service_audio_language_v3(service, audio_language)
        self.assertGreaterEqual(len(voices), 1, f'at least one voice for service {service}, language {audio_language}')

        # pick 3 random voices
        max_voices = 3
        if len(voices) > max_voices:
            voices = random.sample(voices, max_voices)
        for voice in voices:
            self.verify_voice_v3(voice, text, recognition_language)

    def verify_service_japanese(self, service: Service):
        source_text = self.JAPANESE_INPUT_TEXT
        self.verify_service_audio_language(source_text, service, AudioLanguage.ja_JP, 'ja-JP')

    def verify_service_chinese(self, service: Service):
        source_text = self.CHINESE_INPUT_TEXT
        self.verify_service_audio_language(source_text, service, AudioLanguage.zh_CN, 'zh-CN')

    def verify_service_korean(self, service: Service):
        source_text = self.KOREAN_INPUT_TEXT
        self.verify_service_audio_language(source_text, service, AudioLanguage.ko_KR, 'ko-KR')

    def test_voice_list_v3(self):
        # pytest tests/test_audio.py -k test_voice_list_v3
        voice_list_v3 = self.voice_list_v3
        # there should be more than 1000 voices in total
        self.assertTrue(len(voice_list_v3) > 1000)

        # check Azure voices
        # ==================

        # search for some particular voices
        azure_voices = [x for x in voice_list_v3 if x.service == Service.Azure]
        mandarin_azure_voices = [x for x in azure_voices if AudioLanguage.zh_CN in x.audio_languages]
        self.assertTrue(len(mandarin_azure_voices) > 10)

        # pprint.pprint(mandarin_azure_voices)

        xiaochen = [x for x in mandarin_azure_voices if 'Xiaochen' in x.name]
        logger.debug(f'xiaochen voices: {pprint.pformat(xiaochen)}')
        self.assertIn(len(xiaochen), [3, 4], str(xiaochen)) # there is a regular and a multilingual
        # and also a DragonHD, and DragonHD V1

        xiaochen_single_language = [x for x in xiaochen if len(x.audio_languages) == 1][0]
        self.assertEqual(xiaochen_single_language.audio_languages, [AudioLanguage.zh_CN])

        xiaochen_multilingual = [x for x in xiaochen if len(x.audio_languages) > 1][0]
        self.assertTrue(len(xiaochen_multilingual.audio_languages) > 1)
        self.assertTrue(AudioLanguage.zh_CN in xiaochen_multilingual.audio_languages)
        self.assertTrue(AudioLanguage.fr_FR in xiaochen_multilingual.audio_languages)

        # check OpenAI voices
        # ===================
        openai_voices = [x for x in voice_list_v3 if x.service == Service.OpenAI]
        self.assertTrue(len(openai_voices) >= 6)
        # choose random voice
        openai_voice = random.choice(openai_voices)
        self.assertTrue(len(openai_voice.audio_languages) >= 57) # at least 57 locales supportedn

        # check ElevenLabs voices
        # =======================
        elevenlabs_voices = [x for x in voice_list_v3 if x.service == Service.ElevenLabs]
        self.assertTrue(len(elevenlabs_voices) >= 15)
        mandarin_elevenlabs_voices = [x for x in elevenlabs_voices if AudioLanguage.zh_CN in x.audio_languages]
        self.assertTrue(len(mandarin_elevenlabs_voices) > 10)


    def test_french_google(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.fr_FR, 'fr-FR')

    def test_french_azure(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.fr_FR, 'fr-FR')

    def test_french_watson(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Watson, AudioLanguage.fr_FR, 'fr-FR')

    def test_french_vocalware(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.VocalWare, AudioLanguage.fr_FR, 'fr-FR')        

    def test_english_amazon(self):
        source_text = 'I am not interested.'
        self.verify_service_audio_language(source_text, Service.Amazon, AudioLanguage.en_GB, 'en-GB')

    def test_french_amazon(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Amazon, AudioLanguage.fr_FR, 'fr-FR')        

    def test_mandarin_google(self):
        source_text = self.CHINESE_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.zh_CN, 'zh-CN')

    def test_mandarin_azure(self):
        source_text = self.CHINESE_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.zh_CN, 'zh-CN') 

    def test_azure_standard_voice_deprecated(self):
        # standard voices should raise an error
        service = "Azure"
        source_text = "流暢"
        voice_key= {
            "name": "Microsoft Server Speech Text to Speech Voice (ja-JP, HarukaRUS)"
        }
        options = {} 

        with self.assertRaises(cloudlanguagetools.errors.RequestError) as cm:
            self.manager.get_tts_audio(source_text, service, voice_key, options)

        # self.assertEqual(str(cm.exception), 'Azure Standard voices are not supported anymore, please switch to Neural voices.')
        self.assertIn('Unsupported', str(cm.exception))

    def test_mandarin_azure_xiaochen_multilingual(self):
        # search for some particular voices
        azure_voices = [x for x in self.voice_list_v3 if x.service == Service.Azure]
        mandarin_azure_voices = [x for x in azure_voices if AudioLanguage.zh_CN in x.audio_languages]

        xiaochen = [x for x in mandarin_azure_voices if 'Xiaochen' in x.name]
        self.assertIn(len(xiaochen), [3, 4]) # there is a regular and a multilingual, and dragonhd, 
        # and dragonhd latest

        xiaochen_single_language = [x for x in xiaochen if len(x.audio_languages) == 1][0]
        xiaochen_multilingual = [x for x in xiaochen if len(x.audio_languages) > 1][0]

        # check that single language voice can generate chinese
        self.verify_voice_v3(xiaochen_single_language, self.CHINESE_INPUT_TEXT, 'zh-CN')

        # check that multilingual voice can generate chinese and french
        self.verify_voice_v3(xiaochen_multilingual, self.CHINESE_INPUT_TEXT, 'zh-CN')
        self.verify_voice_v3(xiaochen_multilingual, self.FRENCH_INPUT_TEXT, 'fr-FR')

    def test_openai_multilingual_v3(self):
        # get random voice
        openai_voices = [x for x in self.voice_list_v3 if x.service == Service.OpenAI]
        selected_voice = random.choice(openai_voices)

        source_text = 'This is the best restaurant in town.'
        self.verify_voice_v3(selected_voice, source_text, 'en-US')

        source_text = self.CHINESE_INPUT_TEXT
        self.verify_voice_v3(selected_voice, source_text, 'zh-CN')

    def test_elevenlabs_multilingual_v3(self):
        # get random voice
        elevenlabs_voices = [x for x in self.voice_list_v3 if x.service == Service.ElevenLabs]
        selected_voice = random.choice(elevenlabs_voices)

        source_text = 'This is the best restaurant in town.'
        self.verify_voice_v3(selected_voice, source_text, 'en-US')

        # chinese seems to be unreliable
        # source_text = self.CHINESE_INPUT_TEXT
        # self.verify_voice_v3(selected_voice, source_text, 'zh-CN')

        source_text = self.FRENCH_INPUT_TEXT
        self.verify_voice_v3(selected_voice, source_text, 'fr-FR')


    @pytest.mark.skip('watson does not support chinese anymore')
    def test_mandarin_watson(self):
        # pytest tests/test_audio.py -s --log-cli-level=DEBUG -k test_mandarin_watson
        source_text = '老人家'
        self.verify_service_audio_language(source_text, Service.Watson, AudioLanguage.zh_CN, 'zh-CN')

    def test_mandarin_amazon(self):
        source_text = '老人家'
        self.verify_service_audio_language(source_text, Service.Amazon, AudioLanguage.zh_CN, 'zh-CN')

    def test_mandarin_cereproc(self):
        # pytest test_audio.py -k test_mandarin_cereproc
        source_text = '老人家'
        self.verify_service_audio_language(source_text, Service.CereProc, AudioLanguage.zh_CN, 'zh-CN')

    def test_mandarin_alibaba(self):
        # pytest test_audio.py -k test_mandarin_alibaba
        source_text = '老人家'
        self.verify_service_audio_language_v3(source_text, Service.Alibaba, AudioLanguage.zh_CN, 'zh-CN')

    def test_english_alibaba(self):
        # pytest test_audio.py -k test_english_alibaba
        source_text = 'I am not interested.'
        self.verify_service_audio_language_v3(source_text, Service.Alibaba, AudioLanguage.en_GB, 'en-GB')

    @skip_unreliable_clt_test()
    def test_mandarin_vocalware(self):
        # pytest test_audio.py -k test_mandarin_vocalware
        
        source_text = '你好'
        self.verify_service_audio_language(source_text, Service.VocalWare, AudioLanguage.zh_CN, 'zh-CN')

    def test_cantonese_google(self):
        source_text = self.CHINESE_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.zh_HK, 'zh-HK')

    def test_cantonese_azure(self):
        source_text = '天氣預報'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.zh_HK, 'zh-HK')

    def test_cantonese_simplified_azure(self):
        source_text = '天氣預報'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.yue_CN, 'zh-HK')        

    def test_korean_naver(self):
        # pytest test_audio.py -k test_korean_naver
        source_text = self.KOREAN_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Naver, AudioLanguage.ko_KR, 'ko-KR')

    def test_japanese_naver(self):
        # pytest test_audio.py -k test_japanese_naver
        source_text = self.JAPANESE_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.Naver, AudioLanguage.ja_JP, 'ja-JP')

    def test_japanese_naver_error(self):
        # pytest test_audio.py -k test_japanese_naver_error

        source_text = '瑩'
        service = 'Naver'
        voice_key = {"name": "ntomoko"}
        options = {}

        self.assertRaises(cloudlanguagetools.errors.RequestError, 
                          self.manager.get_tts_audio,
                          source_text, service, voice_key, options )


    def test_vietnamese_fptai(self):
        # pytest test_audio.py -k test_vietnamese_fptai
        source_text = 'thì giá là bao nhiêu'
        self.verify_service_audio_language(source_text, Service.FptAi, AudioLanguage.vi_VN, 'vi-VN')

    def test_english_naver(self):
        # pytest test_audio.py -k test_english_naver
        source_text = 'this is the first sentence'
        # source_text = 'hello'
        self.verify_service_audio_language(source_text, Service.Naver, AudioLanguage.en_US, 'en-US')

    def test_english_vocalware(self):
        # pytest test_audio.py -k test_english_vocalware
        source_text = 'this is the first sentence'
        # source_text = 'hello'
        self.verify_service_audio_language(source_text, Service.VocalWare, AudioLanguage.en_US, 'en-US')


    def test_ssml_english_google(self):
        # pytest tests/test_audio.py -k test_ssml_english_google
        if not CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE:
            pytest.skip('you must set CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes')

        source_text = 'hello <break time="50ms"/>world'
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.en_US, 'en-US')

    @skip_unreliable_clt_test()
    def test_ssml_english_azure(self):
        # pytest tests/test_audio.py -k test_ssml_english_azure
        source_text = 'hello <break time="200ms"/>world'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.en_US, 'en-US')

    def test_ssml_english_amazon(self):
        # pytest test_audio.py -k test_ssml_english_amazon

        us_standard_neural_voices = [x for x in self.voice_list_v3 if 
                  x.service == Service.Amazon and
                  x.voice_key['engine'] in ['standard', 'neural'] and 
            AudioLanguage.en_US in x.audio_languages]

        # choose random voice from standard_neural_voices
        standard_neural_voice = random.choice(us_standard_neural_voices)
        source_text = 'hello <break time="200ms"/>world'
        self.verify_voice_v3(standard_neural_voice, source_text, 'en-US')


    def test_ssml_english_watson(self):
        # pytest test_audio.py -k test_ssml_english_watson
        source_text = 'hello <break time="200ms"/>world'
        self.verify_service_audio_language(source_text, Service.Watson, AudioLanguage.en_US, 'en-US')

    def test_ssml_english_cereproc(self):
        # pytest test_audio.py -k test_ssml_english_cereproc
        if not CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE:
            pytest.skip('you must set CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes')

        source_text = 'hello <break time="200ms"/>my friends'
        self.verify_service_audio_language(source_text, Service.CereProc, AudioLanguage.en_GB, 'en-GB')

    def test_english_forvo(self):
        # pytest test_audio.py -k test_english_forvo
        source_text = 'absolutely'
        self.verify_service_audio_language(source_text, Service.Forvo, AudioLanguage.en_US, 'en-US')

    @pytest.mark.skip('not stable')
    def test_english_cereproc(self):
        # pytest test_audio.py -rPP -k test_english_cereproc
        source_text = 'absolutely'
        self.verify_service_audio_language(source_text, Service.CereProc, AudioLanguage.en_GB, 'en-GB')

    def test_english_forvo_preferred_user(self):
        # pytest test_audio.py -rPP -k test_english_forvo_preferred_user
        source_text = 'vehicle'
        service = 'Forvo'
        voice_key = {
            "country_code": "ANY",
            "language_code": "en",
            'preferred_user': 'lizchiu'
        }        
        options = {}
        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'en-GB')
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))

    def test_french_forvo(self):
        # pytest test_audio.py -k test_french_forvo
        source_text = 'absolument'
        self.verify_service_audio_language(source_text, Service.Forvo, AudioLanguage.fr_FR, 'fr-FR')

    def test_portugal_portuguese_forvo(self):
        # pytest test_audio.py -k test_brazilian_portuguese_forvo
        source_text = 'obrigado'
        self.verify_service_audio_language(source_text, Service.Forvo, AudioLanguage.pt_PT, 'pt-PT')

    def test_brazilian_portuguese_forvo(self):
        # pytest test_audio.py -k test_brazilian_portuguese_forvo
        source_text = 'obrigado'
        self.verify_service_audio_language(source_text, Service.Forvo, AudioLanguage.pt_BR, 'pt-BR')

    @pytest.mark.skip(reason="wait for clarification on github")
    def test_egyptian_arabic_forvo(self):
        # https://github.com/Vocab-Apps/anki-hyper-tts/issues/245
        source_text = 'باب'
        self.verify_service_audio_language(source_text, Service.Forvo, AudioLanguage.ar_EG, 'ar-EG')

    @pytest.mark.skip(reason="recognition doesn't work for bengali, but bn-ANY voice should be OK")
    def test_bengali_any_country_forvo(self):
        # https://github.com/Vocab-Apps/anki-hyper-tts/issues/223
        source_text = 'কলকাতা'
        self.verify_service_audio_language(source_text, Service.Forvo, AudioLanguage.bn_ANY, 'bn-IN')

    def test_mandarin_forvo(self):
        # pytest tests/test_audio.py -k test_mandarin_forvo
        source_text = '你好'
        self.verify_service_audio_language(source_text, Service.Forvo, AudioLanguage.zh_CN, 'zh-CN')

    def test_french_cereproc(self):
        # pytest test_audio.py -k test_french_cereproc
        source_text = 'absolument'
        self.verify_service_audio_language(source_text, Service.CereProc, AudioLanguage.fr_FR, 'fr-FR')

    def test_french_forvo_not_found(self):
        # pytest test_audio.py -k test_french_forvo_not_found
        source_text = 'wordnotfound'
        self.assertRaises(cloudlanguagetools.errors.NotFoundError, self.verify_service_audio_language, source_text, Service.Forvo, AudioLanguage.fr_FR, 'fr-FR')

    @pytest.mark.skip(reason="voicen service has disappeared")
    def test_russian_voicen(self):
        # pytest test_audio.py -k test_russian_voicen
        source_text = 'улица'
        self.verify_service_audio_language(source_text, Service.Voicen, AudioLanguage.ru_RU, 'ru-RU')

    @pytest.mark.skip(reason="voicen service has disappeared")
    def test_turkish_voicen(self):
        # pytest test_audio.py -k test_turkish_voicen
        source_text = 'kahvaltı'
        self.verify_service_audio_language(source_text, Service.Voicen, AudioLanguage.tr_TR, 'tr-TR')

    def test_azure_options(self):
        service = 'Azure'
        source_text = self.FRENCH_INPUT_TEXT

        voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
        }

        options = {'rate': 0.8, 'pitch': -10}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.recognize_and_verify_text(
            audio_temp_file, source_text, 'fr-FR', cloudlanguagetools.options.AudioFormat.mp3)

    def test_azure_format_ogg(self):
        service = 'Azure'
        source_text = self.FRENCH_INPUT_TEXT

        voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
        }

        options = {'rate': 0.8, 'pitch': -10, 'format': 'ogg_opus'}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.assertTrue(audio_utils.is_ogg_opus_format(audio_temp_file.name))
        
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'fr-FR', audio_format=cloudlanguagetools.options.AudioFormat.ogg_opus)
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))        

    def verify_wav_voice(self, voice: cloudlanguagetools.ttsvoice.TtsVoice_v3, text: str, recognition_language: str):
        # assert that the wav format is in the list of supported formats
        self.assertTrue(cloudlanguagetools.options.AudioFormat.wav.name in 
                        voice.options[cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER]['values'])
        options = {cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: cloudlanguagetools.options.AudioFormat.wav.name}
        audio_temp_file = self.manager.get_tts_audio(text, voice.service, voice.voice_key, options)
        audio_utils.assert_is_wav_format(self, audio_temp_file.name)

        self.recognize_and_verify_text(
            audio_temp_file, 
            text, 
            recognition_language, 
            cloudlanguagetools.options.AudioFormat.wav)

    def test_azure_format_wav(self):
        fr_voice = self.get_voice_by_service_and_name(Service.Azure, 'Denise')
        self.verify_wav_voice(fr_voice, self.FRENCH_INPUT_TEXT, 'fr-FR')

    def test_amazon_format_wav(self):
        fr_voice = self.get_voice_by_service_and_name(Service.Amazon, 'Mathieu')
        self.verify_wav_voice(fr_voice, self.FRENCH_INPUT_TEXT, 'fr-FR')

    def test_amazon_generative(self):
        amy_generative_voice = self.get_voice_by_lambda(Service.Amazon, 
            lambda x: x.voice_key['engine'] == 'generative' and 'Amy' in x.name)
        self.verify_voice_v3(amy_generative_voice, self.ENGLISH_INPUT_TEXT, 'en-GB')

    def test_elevenlabs_format_wav(self):
        fr_voice = self.get_voice_by_lambda(Service.ElevenLabs, 
            lambda x: 'Rachel' in x.name and x.voice_key['model_id'] == 'eleven_multilingual_v2')
        self.verify_wav_voice(fr_voice, self.FRENCH_INPUT_TEXT, 'fr-FR')        

    def test_google_format_wav(self):
        fr_voice = self.get_voice_by_lambda(Service.Google, 
            lambda x: AudioLanguage.fr_FR in x.audio_languages and 'Journey' not in x.name, assert_unique=False)
        self.verify_wav_voice(fr_voice, self.FRENCH_INPUT_TEXT, 'fr-FR')

    def test_naver_format_wav(self):
        ko_voice = self.get_voice_by_lambda(Service.Naver,
            lambda x: AudioLanguage.ko_KR in x.audio_languages, assert_unique=False)
        self.verify_wav_voice(ko_voice, self.KOREAN_INPUT_TEXT, 'ko-KR')

    def test_openai_format_wav(self):
        ko_voice = self.get_voice_by_lambda(Service.OpenAI,
            lambda x: AudioLanguage.en_US in x.audio_languages, assert_unique=False)
        self.verify_wav_voice(ko_voice, self.ENGLISH_INPUT_TEXT, 'en-US')

    def test_watson_format_wav(self):
        en_voice = self.get_voice_by_lambda(Service.Watson,
            lambda x: AudioLanguage.en_US in x.audio_languages, assert_unique=False)
        self.verify_wav_voice(en_voice, self.ENGLISH_INPUT_TEXT, 'en-US')

    def test_google_chirp3_english(self):
        chirp_en_voice = self.get_voice_by_lambda(Service.Google,
            lambda x: x.name == 'en-US-Chirp3-HD-Charon', assert_unique=True)
        self.verify_voice_v3(chirp_en_voice, self.ENGLISH_INPUT_TEXT, 'en-US')

    def test_google_chirp_hd_english(self):
        chirp_en_voice = self.get_voice_by_lambda(Service.Google,
            lambda x: x.name == 'en-US-Chirp-HD-O', assert_unique=True)
        self.verify_voice_v3(chirp_en_voice, self.ENGLISH_INPUT_TEXT, 'en-US')        

    def test_google_chirp3_mandarin(self):
        chirp_zh_voice = self.get_voice_by_lambda(Service.Google,
            lambda x: x.name == 'cmn-CN-Chirp3-HD-Leda', assert_unique=True)
        self.verify_voice_v3(chirp_zh_voice, self.CHINESE_INPUT_TEXT_2, 'zh-CN')

    @pytest.mark.skip(reason="journey voice seems to be gone")
    def test_google_voice_journey_old(self):
        service = 'Google'
        source_text = self.ENGLISH_INPUT_TEXT

        voice_key = {
            'name': 'en-US-Journey-F', 
            'language_code': 'en-US', 
            'ssml_gender': 'FEMALE'}

        # seems to return:
        # google.api_core.exceptions.InvalidArgument: 400 This voice currently only supports LINEAR16 and MULAW output.
        # ensure that exception is properly wrapped
        self.assertRaises(cloudlanguagetools.errors.RequestError, self.manager.get_tts_audio, source_text, service, voice_key, {})

    def test_google_format_ogg(self):
        service = 'Google'
        source_text = self.FRENCH_INPUT_TEXT

        voice_key = {
            'language_code': 'fr-FR', 
            'name': 'fr-FR-Wavenet-E', 
            'ssml_gender': 'FEMALE'
        }

        options = {'format': 'ogg_opus'}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        file_type = magic.from_file(audio_temp_file.name)
        self.assertIn('Ogg data, Opus', file_type)
        
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'fr-FR', audio_format=cloudlanguagetools.options.AudioFormat.ogg_opus)
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))        

    def test_amazon_format_ogg(self):
        service = 'Amazon'
        source_text = self.FRENCH_INPUT_TEXT

        voice_key = {'engine': 'neural', 'voice_id': 'Gabrielle'}

        options = {'format': 'ogg_vorbis'}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        file_type = magic.from_file(audio_temp_file.name)
        self.assertIn('Ogg data', file_type)
        
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'fr-FR', audio_format=cloudlanguagetools.options.AudioFormat.ogg_vorbis)
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))        

    def test_azure_ampersand(self):
        service = 'Azure'
        source_text = 'In my ignorance I had never heard country & western music.'

        voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)"
        }

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, {})
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'en-US')
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))        

    def test_fptai_options(self):
        service = 'FptAi'
        source_text = 'xin chào bạn của tôi'

        voice_key = {
            "voice_id": "std_leminh"
        }

        options = {'speed': 0.5}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'vi-VN')
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))

    def test_elevenlabs_english(self):
        source_text = 'This is the best restaurant in town.'
        self.verify_service_audio_language(source_text, Service.ElevenLabs, AudioLanguage.en_US, 'en-US')

    def test_elevenlabs_english_all_voices_charlotte(self):
        # pytest tests/test_audio.py -s --log-cli-level=INFO -k test_elevenlabs_english_all_voices_charlotte
        source_text = 'This is the best restaurant in town.'
        voice_list = self.get_voice_list_service_audio_language(Service.ElevenLabs, AudioLanguage.en_US)
        # pprint.pprint(voice_list)
        selected_voice_candidates = [x for x in voice_list if x['audio_language_code'] == 'en_US' and x['service'] == 'ElevenLabs']
        selected_voice_candidates = [x for x in selected_voice_candidates if 'Charlotte' in x['voice_name']]
        pprint.pprint(selected_voice_candidates)
        logger.info(f'number of voices: {len(selected_voice_candidates)}')
        # self.assertTrue(False)
        for voice in selected_voice_candidates:
            voice_str = f"{voice['voice_name']} {voice['voice_key']}"
            logger.info(f"testing voice {voice_str}")
            self.verify_voice(voice, source_text, 'en-US')
            logger.info(f'voice: {voice_str} passed')

    def test_elevenlabs_french(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.ElevenLabs, AudioLanguage.fr_FR, 'fr-FR')


    def test_elevenlabs_spanish(self):
        source_text = 'No me gusta la comida.'
        self.verify_service_audio_language(source_text, Service.ElevenLabs, AudioLanguage.es_ES, 'es-ES')

    def test_elevenlabs_italian(self):
        source_text = 'Non mi piace il cibo.'
        self.verify_service_audio_language(source_text, Service.ElevenLabs, AudioLanguage.it_IT, 'it-IT')

    def test_elevenlabs_german(self):
        source_text = 'Ich mag das Essen nicht.'
        self.verify_service_audio_language(source_text, Service.ElevenLabs, AudioLanguage.de_DE, 'de-DE')

    def test_elevenlabs_german(self):
        source_text = 'Ich mag das Essen nicht.'
        self.verify_service_audio_language(source_text, Service.ElevenLabs, AudioLanguage.de_DE, 'de-DE')        

    @skip_unreliable_clt_test()
    def test_elevenlabs_japanese(self):
        self.verify_service_japanese(Service.ElevenLabs)

    @skip_unreliable_clt_test()
    def test_elevenlabs_chinese(self):
        self.verify_service_chinese(Service.ElevenLabs)

    @skip_unreliable_clt_test()
    def test_elevenlabs_korean(self):
        self.verify_service_korean(Service.ElevenLabs)

    def test_openai_english(self):
        source_text = 'This is the best restaurant in town.'
        self.verify_service_audio_language_v3(source_text, Service.OpenAI, AudioLanguage.en_US, 'en-US')

    @pytest.mark.skip(reason="detection of openai french is unreliable")
    def test_openai_french(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.OpenAI, AudioLanguage.fr_FR, 'fr-FR')

    def test_openai_ballad(self):
        # ballad seems to open support gpt-4o-mini-tts
        service = 'OpenAI'
        source_text = self.ENGLISH_INPUT_TEXT

        voice_key = {
            "name": "ballad"
        }
        options = {}
        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.recognize_and_verify_text(
            audio_temp_file, source_text, 'en-US', cloudlanguagetools.options.AudioFormat.mp3)

    def test_openai_model_options(self):
        # ballad should only have gpt-4o-mini-tts
        voice_ballad = self.get_voice_by_lambda(Service.OpenAI,
            lambda x: x.name == 'ballad', assert_unique=True)
        self.assertEqual(voice_ballad.options['model']['values'], ['gpt-4o-mini-tts'])

        voice_verse = self.get_voice_by_lambda(Service.OpenAI,
            lambda x: x.name == 'verse', assert_unique=True)
        self.assertEqual(voice_verse.options['model']['values'], ['gpt-4o-mini-tts'])        

        # alloy should have all options
        voice_alloy = self.get_voice_by_lambda(Service.OpenAI,
            lambda x: x.name == 'alloy', assert_unique=True)
        self.assertEqual(voice_alloy.options['model']['values'], ['gpt-4o-mini-tts',
            'tts-1-hd',
            'tts-1'])

    @pytest.mark.skip(reason="this is a test of unsupported cases")
    def test_openai_unsupported(self):
        service = 'OpenAI'
        source_text = self.ENGLISH_INPUT_TEXT

        voice_key = {
            # "name": "onyx"
            "name": "verse"
        }
        options = {'model': 'tts-1-hd'}
        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.recognize_and_verify_text(
            audio_temp_file, source_text, 'en-US', cloudlanguagetools.options.AudioFormat.mp3)


    def test_openai_english_gpt4o_mini(self):
        service = 'OpenAI'
        source_text = self.ENGLISH_INPUT_TEXT

        voice_key = {
            "name": "onyx"
        }
        options = {'model': 'gpt-4o-mini-tts'}
        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.recognize_and_verify_text(
            audio_temp_file, source_text, 'en-US', cloudlanguagetools.options.AudioFormat.mp3)

    def test_openai_english_gpt4o_instructions(self):
        service = 'OpenAI'
        source_text = self.ENGLISH_INPUT_TEXT

        voice_key = {
            "name": "onyx"
        }
        options = {
            'model': 'gpt-4o-mini-tts',
            'instructions': """
Accent/Affect: Warm, refined, and gently instructive, reminiscent of a friendly art instructor.

Tone: Calm, encouraging, and articulate, clearly describing each step with patience.

Pacing: Slow and deliberate, pausing often to allow the listener to follow instructions comfortably.

Emotion: Cheerful, supportive, and pleasantly enthusiastic; convey genuine enjoyment and appreciation of art.

Pronunciation: Clearly articulate artistic terminology (e.g., "brushstrokes," "landscape," "palette") with gentle emphasis.

Personality Affect: Friendly and approachable with a hint of sophistication; speak confidently and reassuringly, guiding users through each painting step patiently and warmly."""}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.recognize_and_verify_text(
            audio_temp_file, source_text, 'en-US', cloudlanguagetools.options.AudioFormat.mp3)

    @skip_unreliable_clt_test() # rate limiting on gemini
    def test_gemini_english(self):
        """Test Gemini TTS with English"""
        source_text = self.ENGLISH_INPUT_TEXT
        self.verify_service_audio_language_v3(source_text, Service.Gemini, AudioLanguage.en_US, 'en-US')

    @skip_unreliable_clt_test() # rate limiting on gemini
    def test_gemini_french(self):
        """Test Gemini TTS with French"""
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language_v3(source_text, Service.Gemini, AudioLanguage.fr_FR, 'fr-FR')

    @skip_unreliable_clt_test() # rate limiting on gemini
    def test_gemini_spanish(self):
        """Test Gemini TTS with Spanish"""
        source_text = self.SPANISH_INPUT_TEXT
        self.verify_service_audio_language_v3(source_text, Service.Gemini, AudioLanguage.es_ES, 'es-ES')

    @skip_unreliable_clt_test() # rate limiting on gemini
    def test_gemini_voice_options(self):
        """Test Gemini TTS with different voice and model options"""
        service = 'Gemini'
        source_text = self.ENGLISH_INPUT_TEXT

        # Test with specific voice and pro model
        voice_key = {
            "name": "Kore"
        }
        options = {'model': 'gemini-2.5-pro-preview-tts'}
        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.recognize_and_verify_text(
            audio_temp_file, source_text, 'en-US', cloudlanguagetools.options.AudioFormat.wav)

    @skip_unreliable_clt_test() # rate limiting on gemini
    def test_gemini_different_voices(self):
        """Test Gemini TTS with different voice characteristics"""
        service = 'Gemini'
        source_text = 'This is a test of different Gemini voices.'

        voices_to_test = ['Zephyr', 'Puck', 'Charon', 'Kore']
        
        for voice_name in voices_to_test:
            voice_key = {"name": voice_name}
            options = {'model': 'gemini-2.5-flash-preview-tts'}
            
            audio_temp_file = self.get_tts_audio_with_retry(source_text, service, voice_key, options)
            
            # Verify file was created and has content
            self.assertIsNotNone(audio_temp_file)
            file_size = os.path.getsize(audio_temp_file.name)
            self.assertGreater(file_size, 1000, f'Audio file for voice {voice_name} should be at least 1KB')
            
            # Verify it's an audio file
            file_type = magic.from_file(audio_temp_file.name, mime=True)
            self.assertIn('audio', file_type, f'File for voice {voice_name} should be audio format')

    @skip_unreliable_clt_test() # rate limiting on gemini
    def test_gemini_ogg_format(self):
        """Test Gemini TTS with OGG format"""
        service = 'Gemini'
        source_text = self.ENGLISH_INPUT_TEXT
        
        # Test with OGG format
        voice_key = {
            "name": "Zephyr"
        }
        options = {
            'model': 'gemini-2.5-flash-preview-tts',
            'audio_format': 'ogg_opus'
        }
        
        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)
        
        # Verify file was created and has content
        self.assertIsNotNone(audio_temp_file)
        file_size = os.path.getsize(audio_temp_file.name)
        self.assertGreater(file_size, 1000, 'OGG audio file should be at least 1KB')
        
        # Verify it's an OGG audio file
        file_type = magic.from_file(audio_temp_file.name, mime=True)
        self.assertIn('ogg', file_type, 'File should be OGG format')            