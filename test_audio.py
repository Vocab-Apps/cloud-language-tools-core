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
    
    def verify_voice(self, voice, text, recognition_language):
        voice_key = voice['voice_key']
        audio_temp_file = self.manager.get_tts_audio(text, voice['service'], voice_key, {})
        audio_text = self.speech_to_text(audio_temp_file, recognition_language)
        self.assertEqual(text, audio_text)
        logging.info(f"verified service {voice['service']} voice {voice['voice_key']}")

    def verify_service_audio_language(self, text, service, audio_language):
        voices = self.get_voice_list_service_audio_language(Service.Google, AudioLanguage.fr_FR)
        for voice in voices:
            self.verify_voice(voice, text, audio_language)

    def test_french_google(self):
        source_text = 'Je ne suis pas intéressé.'
        self.verify_service_audio_language(source_text, Service.Google, 'fr-FR')


    # python -m pytest test_audio.py -s -k 'test_french'
    def test_french(self):
        source_text = 'Je ne suis pas intéressé.'
        source_language = Language.fr

        voices = self.get_voice_list_for_language(source_language)
        self.assertTrue(len(voices) > 1)

        voices = voices[0:1]

        for voice in voices:
            voice_key = voice['voice_key']
            audio_temp_file = self.manager.get_tts_audio(source_text, voice['service'], voice_key, {})
            audio_text = self.speech_to_text(audio_temp_file, 'fr-FR')
            print(audio_text)
            self.assertEqual(source_text, audio_text)



