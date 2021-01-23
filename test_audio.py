import unittest
import logging
import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.constants import Language
from cloudlanguagetools.constants import AudioLanguage
from cloudlanguagetools.constants import Service

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager

class TestAudio(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()
        self.language_list = self.manager.get_language_list()
        self.voice_list = self.manager.get_tts_voice_list_json()

    def get_voice_list_for_language(self, language):
        subset = [x for x in self.voice_list if x['language_code'] == language.name]
        return subset

    def get_voice_list_service_audio_language(self, service, audio_language):
        subset = [x for x in self.voice_list if x['audio_language_code'] == audio_language.name and x['service'] == service.name]
        return subset        

    def speech_to_text(self, audio_temp_file, language):
        result = self.manager.services[Service.Azure.name].speech_to_text(audio_temp_file.name, language)
        return result
    
    def sanitize_recognized_text(self, recognized_text):
        result_text = recognized_text.replace('.', '').replace('。', '').replace('?', '').replace('？', '')
        return result_text

    def verify_voice(self, voice, text, recognition_language):
        voice_key = voice['voice_key']
        audio_temp_file = self.manager.get_tts_audio(text, voice['service'], voice_key, {})
        audio_text = self.speech_to_text(audio_temp_file, recognition_language)
        assert_text = f"service {voice['service']} voice_key: {voice['voice_key']}"
        self.assertEqual(self.sanitize_recognized_text(text), self.sanitize_recognized_text(audio_text), msg=assert_text)

    def verify_service_audio_language(self, text, service, audio_language, recognition_language):
        voices = self.get_voice_list_service_audio_language(Service.Google, audio_language)
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

    def test_mandarin_google(self):
        source_text = '老人家'
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.zh_CN, 'zh-CN')

    def test_mandarin_azure(self):
        source_text = '老人家'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.zh_CN, 'zh-CN') 

    def test_cantonese_google(self):
        source_text = '天氣預報'
        self.verify_service_audio_language(source_text, Service.Google, AudioLanguage.zh_HK, 'zh-HK')

    def test_cantonese_azure(self):
        source_text = '天氣預報'
        self.verify_service_audio_language(source_text, Service.Azure, AudioLanguage.zh_HK, 'zh-HK')


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