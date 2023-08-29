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

import audio_utils

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

class TestAudio(unittest.TestCase):

    FRENCH_INPUT_TEXT = "On a volé mes affaires."
    JAPANESE_INPUT_TEXT = 'おはようございます'
    CHINESE_INPUT_TEXT = '老人家'
    KOREAN_INPUT_TEXT = '여보세요'

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
        voice_key = voice['voice_key']

        max_tries = 3
        num_tries = max_tries
        get_tts_audio_success = False

        while get_tts_audio_success != True and num_tries >= 0:
            num_tries -= 1
            try:
                logging.info(f"attempting to retrieve audio from {voice['service']}, attempts: {num_tries}")
                audio_temp_file = self.manager.get_tts_audio(text, voice['service'], voice_key, {})
                get_tts_audio_success = True
            except cloudlanguagetools.errors.TimeoutError as exception:
                time.sleep(1) # allow retry

        if num_tries < 0:
            raise Exception(f"could not retrieve audio from {voice['service']} after {max_tries} tries")

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
        assert_text = f"service {voice['service']} voice_key: {voice['voice_key']}"
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
        source_text = '老人家'
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.zh_CN, 'zh-CN')

    def test_mandarin_azure(self):
        source_text = '你好'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.zh_CN, 'zh-CN') 

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

    def test_mandarin_vocalware(self):
        # pytest test_audio.py -k test_mandarin_vocalware
        source_text = '你好'
        self.verify_service_audio_language(source_text, Service.VocalWare, AudioLanguage.zh_CN, 'zh-CN')

    def test_cantonese_google(self):
        source_text = '天氣預報'
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
        # pytest test_audio.py -k test_ssml_english_google
        source_text = 'hello <break time="200ms"/>world'
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.en_US, 'en-US')

    def test_ssml_english_azure(self):
        # pytest test_audio.py -k test_ssml_english_azure
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

    def test_elevenlabs_japanese(self):
        self.verify_service_japanese(Service.ElevenLabs)

    def test_elevenlabs_chinese(self):
        self.verify_service_chinese(Service.ElevenLabs)

    def test_elevenlabs_korean(self):
        self.verify_service_korean(Service.ElevenLabs)