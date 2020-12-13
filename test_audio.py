import unittest
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

    def test_french(self):
        source_text = 'Je ne suis pas intéressé.'
        source_language = Language.fr

        voices = self.get_voice_list_for_language(source_language)

        self.assertTrue(len(voices) > 1)
        print(voices)



