import unittest
import cloudlanguagetools
import cloudlanguagetools.servicemanager

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()

    def test_translate(self):
        source_text = 'Je ne suis pas intéressé.'
        translated_text = self.manager.get_translation(source_text, cloudlanguagetools.constants.Service.Azure.name, 'fr', 'en')
        self.assertEqual(translated_text, 'I\'m not interested.')

    def test_get_translation_language_list_json(self):
        translation_language_list = self.manager.get_translation_language_list()