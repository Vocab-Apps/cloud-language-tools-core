import unittest
import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.constants import Language
from cloudlanguagetools.constants import Service

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()
        self.language_list = self.manager.get_language_list()
        self.translation_language_list = self.manager.get_translation_language_list_json()

    def test_language_list(self):
        self.assertTrue(len(self.language_list) > 0)
        # check for the presence of a few languages
        self.assertEqual('French', self.language_list['fr'])
        self.assertEqual('Chinese (Simplified)', self.language_list['zh_cn'])
        self.assertEqual('Thai', self.language_list['th'])
        self.assertEqual('Chinese (Cantonese, Traditional)', self.language_list['yue'])
        self.assertEqual('Chinese (Traditional)', self.language_list['zh_tw'])

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

        # chinese traditional (most cantonese text will be recognized as traditional/taiwan)
        self.assertEqual(Language.zh_tw, self.manager.detect_language(['你住得好近一個機場']))
        

    def test_translate(self):
        source_text = 'Je ne suis pas intéressé.'
        translated_text = self.manager.get_translation(source_text, cloudlanguagetools.constants.Service.Azure.name, 'fr', 'en')
        self.assertEqual(translated_text, "I'm not interested.")

    def translate_text(self, service, source_text, source_language, target_language, expected_result):
        source_language_list = [x for x in self.translation_language_list if x['language_code'] == source_language.name and x['service'] == service.name]
        self.assertEqual(1, len(source_language_list))
        target_language_list = [x for x in self.translation_language_list if x['language_code'] == target_language.name and x['service'] == service.name]
        self.assertEqual(1, len(target_language_list))

        from_language_key = source_language_list[0]['language_id']
        to_language_key = target_language_list[0]['language_id']

        # now, translate
        translated_text = self.manager.get_translation(source_text, service.name, from_language_key, to_language_key)
        self.assertEqual(expected_result, translated_text)

    def test_translate_chinese(self):
        self.translate_text(Service.Azure, '送外卖的人', Language.zh_cn, Language.en, 'The person who delivered the takeaway')
        self.translate_text(Service.Google, '中国有很多外国人', Language.zh_cn, Language.en, 'There are many foreigners in China')
        self.translate_text(Service.Azure, '成本很低', Language.zh_cn, Language.fr, 'Le coût est faible')

    def test_get_translation_language_list_json(self):
        translation_language_list = self.manager.get_translation_language_list()