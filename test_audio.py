import unittest
import logging
import random
import re
import sys
import magic
import pytest
import secrets
import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.languages import Language
from cloudlanguagetools.languages import AudioLanguage
from cloudlanguagetools.constants import Service

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager(secrets.config)
    manager.configure()    
    return manager

class TestAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = get_manager()
        cls.language_list = cls.manager.get_language_list()
        cls.voice_list = cls.manager.get_tts_voice_list_json()

        logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                            datefmt='%Y%m%d-%H:%M:%S',
                            stream=sys.stdout,
                            level=logging.DEBUG)
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

    def speech_to_text(self, audio_temp_file, language, audio_format=cloudlanguagetools.constants.AudioFormat.mp3):
        result = self.manager.services[Service.Azure.name].speech_to_text(audio_temp_file.name, language, audio_format)
        return result
    
    def sanitize_recognized_text(self, recognized_text):
        recognized_text = re.sub('<[^<]+?>', '', recognized_text)
        result_text = recognized_text.replace('.', '').\
            replace('。', '').\
            replace('?', '').\
            replace('？', '').\
            replace('您', '你').\
            replace('&', 'and').\
            replace(',', '').\
            replace(':', '').lower()
        return result_text

    def verify_voice(self, voice, text, recognition_language):
        voice_key = voice['voice_key']
        audio_temp_file = self.manager.get_tts_audio(text, voice['service'], voice_key, {})
        # check MIME type
        mime_type = magic.from_file(audio_temp_file.name)
        self.assertIn('MPEG ADTS, layer III', mime_type)
        audio_text = self.speech_to_text(audio_temp_file, recognition_language)
        assert_text = f"service {voice['service']} voice_key: {voice['voice_key']}"
        self.assertEqual(self.sanitize_recognized_text(text), self.sanitize_recognized_text(audio_text), msg=assert_text)

    def verify_service_audio_language(self, text, service, audio_language, recognition_language):
        # logging.info(f'verify_service_audio: service: {service} audio_language: {audio_language}')
        voices = self.get_voice_list_service_audio_language(service, audio_language)
        # pick 3 random voices
        max_voices = 3
        if len(voices) > max_voices:
            voices = random.sample(voices, max_voices)
        for voice in voices:
            self.verify_voice(voice, text, recognition_language)

    def test_french_google(self):
        source_text = 'Je ne suis pas intéressé.'
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.fr_FR, 'fr-FR')

    def test_french_azure(self):
        source_text = 'Je ne suis pas intéressé.'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.fr_FR, 'fr-FR')

    def test_french_watson(self):
        source_text = 'Je ne suis pas intéressé.'
        self.verify_service_audio_language(source_text, Service.Watson, AudioLanguage.fr_FR, 'fr-FR')

    def test_french_vocalware(self):
        source_text = 'Je ne suis pas intéressé.'
        self.verify_service_audio_language(source_text, Service.VocalWare, AudioLanguage.fr_FR, 'fr-FR')        

    def test_english_amazon(self):
        source_text = 'I am not interested.'
        self.verify_service_audio_language(source_text, Service.Amazon, AudioLanguage.en_GB, 'en-GB')

    def test_french_amazon(self):
        source_text = 'Je ne suis pas intéressé.'
        self.verify_service_audio_language(source_text, Service.Amazon, AudioLanguage.fr_FR, 'fr-FR')        

    def test_mandarin_google(self):
        source_text = '老人家'
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.zh_CN, 'zh-CN')

    def test_mandarin_azure(self):
        source_text = '你好'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.zh_CN, 'zh-CN') 

    def test_mandarin_watson(self):
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

    def test_korean_naver(self):
        # pytest test_audio.py -k test_korean_naver
        source_text = '여보세요'
        self.verify_service_audio_language(source_text, Service.Naver, AudioLanguage.ko_KR, 'ko-KR')

    def test_japanese_naver(self):
        # pytest test_audio.py -k test_japanese_naver
        source_text = 'おはようございます'
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
        source_text = 'Tôi bị mất cái ví.'
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
        audio_text = self.speech_to_text(audio_temp_file, 'en-GB')
        self.assertEqual(self.sanitize_recognized_text(source_text), self.sanitize_recognized_text(audio_text))

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

    def test_russian_voicen(self):
        # pytest test_audio.py -k test_russian_voicen
        source_text = 'улица'
        self.verify_service_audio_language(source_text, Service.Voicen, AudioLanguage.ru_RU, 'ru-RU')

    def test_turkish_voicen(self):
        # pytest test_audio.py -k test_turkish_voicen
        source_text = 'kahvaltı'
        self.verify_service_audio_language(source_text, Service.Voicen, AudioLanguage.tr_TR, 'tr-TR')

    def test_azure_options(self):
        service = 'Azure'
        source_text = 'Je ne suis pas intéressé.'

        voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
        }

        options = {'rate': 0.8, 'pitch': -10}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)
        audio_text = self.speech_to_text(audio_temp_file, 'fr-FR')
        self.assertEqual(self.sanitize_recognized_text(source_text), self.sanitize_recognized_text(audio_text))

    def test_azure_format_ogg(self):
        service = 'Azure'
        source_text = 'Je ne suis pas intéressé.'

        voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)"
        }

        options = {'rate': 0.8, 'pitch': -10, 'format': 'ogg'}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        file_type = magic.from_file(audio_temp_file.name)
        self.assertIn('Ogg data, Opus', file_type)
        
        audio_text = self.speech_to_text(audio_temp_file, 'fr-FR', audio_format=cloudlanguagetools.constants.AudioFormat.ogg)
        self.assertEqual(self.sanitize_recognized_text(source_text), self.sanitize_recognized_text(audio_text))        

    def test_google_format_ogg(self):
        service = 'Google'
        source_text = 'Je ne suis pas intéressé.'

        voice_key = {
            'language_code': 'fr-FR', 
            'name': 'fr-FR-Wavenet-E', 
            'ssml_gender': 'FEMALE'
        }

        options = {'format': 'ogg'}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)

        file_type = magic.from_file(audio_temp_file.name)
        self.assertIn('Ogg data, Opus', file_type)
        
        audio_text = self.speech_to_text(audio_temp_file, 'fr-FR', audio_format=cloudlanguagetools.constants.AudioFormat.ogg)
        self.assertEqual(self.sanitize_recognized_text(source_text), self.sanitize_recognized_text(audio_text))        

    def test_azure_ampersand(self):
        service = 'Azure'
        source_text = 'In my ignorance I had never heard country & western music.'

        voice_key = {
            "name": "Microsoft Server Speech Text to Speech Voice (en-US, AriaNeural)"
        }

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, {})
        audio_text = self.speech_to_text(audio_temp_file, 'en-US')
        self.assertEqual(self.sanitize_recognized_text(source_text), self.sanitize_recognized_text(audio_text))        

    def test_fptai_options(self):
        service = 'FptAi'
        source_text = 'Tôi bị mất cái ví.'

        voice_key = {
            "voice_id": "leminh"
        }

        options = {'speed': -0.5}

        audio_temp_file = self.manager.get_tts_audio(source_text, service, voice_key, options)
        audio_text = self.speech_to_text(audio_temp_file, 'vi-VN')
        self.assertEqual(self.sanitize_recognized_text(source_text), self.sanitize_recognized_text(audio_text))