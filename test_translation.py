import unittest
import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.constants import Language
from cloudlanguagetools.constants import Service
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure()    
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()
        self.language_list = self.manager.get_language_list()
        self.translation_language_list = self.manager.get_translation_language_list_json()
        self.transliteration_language_list = self.manager.get_transliteration_language_list_json()

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

    def test_translate_error(self):
        source_text = 'Je ne suis pas intéressé.'
        self.assertRaises(cloudlanguagetools.errors.RequestError, self.manager.get_translation, source_text, cloudlanguagetools.constants.Service.Azure.name, 'fr', 'zh_cn')

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
        self.translate_text(Service.Google, '换登机牌', Language.zh_cn, Language.fr, "Changer de carte d'embarquement")

    def test_translate_naver(self):
        # pytest test_translation.py -k test_translate_naver
        self.translate_text(Service.Naver, '천천히 말해 주십시오', Language.ko, Language.en, 'Please speak slowly.')
        self.translate_text(Service.Naver, 'Please speak slowly', Language.en, Language.ko, '천천히 말씀해 주세요.')

        self.translate_text(Service.Naver, '천천히 말해 주십시오', Language.ko, Language.fr, 'Parlez lentement.')
        self.translate_text(Service.Naver, 'Veuillez parler lentement.', Language.fr, Language.ko, '천천히 말씀해 주세요.')        

    def test_translate_naver_unsupported_pair(self):
        # pytest test_translation.py -k test_translate_naver_unsupported_pair
        self.assertRaises(cloudlanguagetools.errors.RequestError, self.translate_text, Service.Naver, 'Veuillez parler lentement.', Language.fr, Language.th, 'Please speak slowly.')

    def test_translate_all(self):
        source_text = '成本很低'
        from_language = Language.zh_cn.name
        to_language =  Language.fr.name
        result = self.manager.get_all_translations(source_text, from_language, to_language)
        self.assertTrue('Azure' in result)
        self.assertTrue('Google' in result)
        self.assertTrue('Watson' in result)
        self.assertEqual(result['Azure'], 'Le coût est faible')
        self.assertEqual(result['Google'], 'Coût très bas')
        self.assertEqual(result['Watson'], 'Le coût est très bas.')

    def test_transliteration(self):
        
        # chinese
        source_text = '成本很低'
        from_language = Language.zh_cn.name
        service = 'Azure'
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('chéng běn hěn dī', result)

        # thai
        source_text = 'ประเทศไทย'
        from_language = Language.th.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('prathetthai', result)

        # french IPA
        test_easy_pronunciation = False
        if test_easy_pronunciation:
            source_text = 'l’herbe est plus verte ailleurs'
            from_language = Language.fr.name
            transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language]
            self.assertTrue(len(transliteration_candidates) == 1)
            transliteration_option = transliteration_candidates[0]
            service = transliteration_option['service']
            transliteration_key = transliteration_option['transliteration_key']
            result = self.manager.get_transliteration(source_text, service, transliteration_key)
            self.assertEqual('lɛʁb‿ ɛ ply vɛʁt‿ ajœʁ', result)
