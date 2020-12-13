import unittest
import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.constants import Language

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()

    def test_detection(self):
        source_text = 'Je ne suis pas intéressé.'
        self.assertEqual(Language.fr, self.manager.detect_language([source_text]))

        source_list = [
        'Pouvez-vous me faire le change ?',
        'Pouvez-vous débarrasser la table, s\'il vous plaît?',
        "I'm not interested"
        ]    
        # french should still win
        self.assertEqual(Language.fr, self.manager.detect_language(source_list))

        # chinese
        self.assertEqual(Language.zh_cn, self.manager.detect_language(['我试着每天都不去吃快餐']))

    def test_translate(self):
        source_text = 'Je ne suis pas intéressé.'
        translated_text = self.manager.get_translation(source_text, cloudlanguagetools.constants.Service.Azure.name, 'fr', 'en')
        self.assertEqual(translated_text, "I'm not interested.")

    def test_get_translation_language_list_json(self):
        translation_language_list = self.manager.get_translation_language_list()