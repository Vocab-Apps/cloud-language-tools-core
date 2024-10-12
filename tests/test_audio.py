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

import audio_utils

CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE = os.environ.get('CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE', 'no') == 'yes'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.options
from cloudlanguagetools.languages import Language
from cloudlanguagetools.languages import AudioLanguage
from cloudlanguagetools.constants import Service

logger = logging.getLogger(__name__)

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()

    return manager



def skip_unreliable_clt_test():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE:
                pytest.skip(f'you must set CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes')
            return func(*args, **kwargs)
        return wrapper
    return decorator


class TestAudio(unittest.TestCase):

    ENGLISH_INPUT_TEXT = 'This is the best restaurant in town.'
    FRENCH_INPUT_TEXT = 'Bonjour'
    JAPANESE_INPUT_TEXT = 'こんにちは'
    CHINESE_INPUT_TEXT = '你好'
    KOREAN_INPUT_TEXT = '안녕하세요'

    @classmethod
    def setUpClass(cls):
        cls.manager = get_manager()
        cls.language_list = cls.manager.get_language_list()
        num_tries = 3
        success = False
        while success == False and num_tries >= 0:
            num_tries -= 1
            try:
                cls.voice_list = cls.manager.get_tts_voice_list_json()
                cls.voice_list_v3 = cls.manager.get_tts_voice_list_v3()
                success = True
            except requests.exceptions.ReadTimeout as e:
                logging.exception(f'could not get voice list, timeout')
                time.sleep(1)
        
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

    def verify_voice(self, voice, text, recognition_language):
        return self.verify_voice_internal(voice['voice_key'], voice['service'], text, recognition_language)

    def verify_voice_v3(self, voice, text, recognition_language):
        voice_key = voice.voice_key
        voice_service = voice.service.name
        return self.verify_voice_internal(voice_key, voice_service, text, recognition_language)

    def verify_voice_internal(self, voice_key, voice_service, text, recognition_language):

        max_tries = 3
        num_tries = max_tries
        get_tts_audio_success = False

        while get_tts_audio_success != True and num_tries >= 0:
            num_tries -= 1
            try:
                logging.info(f"attempting to retrieve audio from {voice_service}, attempts: {num_tries}")
                audio_temp_file = self.manager.get_tts_audio(text, voice_service, voice_key, {})
                get_tts_audio_success = True
            except cloudlanguagetools.errors.TimeoutError as exception:
                time.sleep(1) # allow retry

        if num_tries < 0:
            raise Exception(f"could not retrieve audio from {voice_service} after {max_tries} tries")

        # check file format
        is_mp3 = audio_utils.is_mp3_format(audio_temp_file.name)
        if not is_mp3:
            mime_type = magic.from_file(audio_temp_file.name)
            logger.error(f'found mime type: {mime_type}')
            # dump file to console
            f = open(audio_temp_file.name, "r")
            print(f.read())

        self.assertTrue(is_mp3)
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, recognition_language)
        assert_text = f"service {voice_service} voice_key: {voice_key}"
        self.assertEqual(audio_utils.sanitize_recognized_text(text), audio_utils.sanitize_recognized_text(audio_text), msg=assert_text)

    def verify_service_audio_language(self, text, service, audio_language, recognition_language):
        # logging.info(f'verify_service_audio: service: {service} audio_language: {audio_language}')
        voices = self.get_voice_list_service_audio_language(service, audio_language)
        self.assertGreaterEqual(len(voices), 1, f'at least one voice for service {service}, language {audio_language}')
        # pick 3 random voices
        max_voices = 3
        if len(voices) > max_voices:
            voices = random.sample(voices, max_voices)
        for voice in voices:
            self.verify_voice(voice, text, recognition_language)

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
        self.assertTrue(len(xiaochen) == 2) # there is a regular and a multilingual

        xiaochen_single_language = [x for x in xiaochen if len(x.audio_languages) == 1][0]
        self.assertEquals(xiaochen_single_language.audio_languages, [AudioLanguage.zh_CN])

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

        self.assertEquals(str(cm.exception), 'Azure Standard voices are not supported anymore, please switch to Neural voices.')

    def test_mandarin_azure_xiaochen_multilingual(self):
        # search for some particular voices
        azure_voices = [x for x in self.voice_list_v3 if x.service == Service.Azure]
        mandarin_azure_voices = [x for x in azure_voices if AudioLanguage.zh_CN in x.audio_languages]

        xiaochen = [x for x in mandarin_azure_voices if 'Xiaochen' in x.name]
        self.assertTrue(len(xiaochen) == 2) # there is a regular and a multilingual

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
        source_text = 'hello <break time="200ms"/>world'
        self.verify_service_audio_language(source_text, Service.Amazon, AudioLanguage.en_US, 'en-US')

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
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'fr-FR')
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))

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

    def test_azure_format_wav(self):
        service = 'Azure'
        source_text = self.FRENCH_INPUT_TEXT

        voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
        }
        options = {'format': 'wav'}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        self.assertTrue(audio_utils.is_wav_format(audio_temp_file.name))
        
        audio_text = audio_utils.speech_to_text(self.manager, audio_temp_file, 'fr-FR', audio_format=cloudlanguagetools.options.AudioFormat.wav)
        self.assertEqual(audio_utils.sanitize_recognized_text(source_text), audio_utils.sanitize_recognized_text(audio_text))                

    def test_google_voice_journey(self):
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
            "voice_id": "leminh"
        }

        options = {'speed': -0.5}

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
        self.verify_service_audio_language(source_text, Service.OpenAI, AudioLanguage.en_US, 'en-US')

    @pytest.mark.skip(reason="detection of openai french is unreliable")
    def test_openai_french(self):
        source_text = self.FRENCH_INPUT_TEXT
        self.verify_service_audio_language(source_text, Service.OpenAI, AudioLanguage.fr_FR, 'fr-FR')
