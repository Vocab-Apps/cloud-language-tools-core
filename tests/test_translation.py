import os
import sys
import logging
import unittest
import pytest
import json
import pprint
import time
import requests
import backoff

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.languages import Language
from cloudlanguagetools.constants import Service
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestTranslation(unittest.TestCase):
    
    @classmethod
    @backoff.on_exception(backoff.expo,
                        requests.exceptions.RequestException,
                        max_time=60)
    def get_all_language_data(cls):
        cls.language_list = cls.manager.get_language_list()
        cls.translation_language_list = cls.manager.get_translation_language_list_json()
        cls.transliteration_language_list = cls.manager.get_transliteration_language_list_json()
        cls.tokenization_options = cls.manager.get_tokenization_options_json()

    @classmethod
    def setUpClass(cls):
        cls.manager = get_manager()
        cls.get_all_language_data()

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

    def sanitize_text(self, recognized_text):
        result_text = recognized_text.replace('.', '').\
            replace('。', '').\
            replace('?', '').\
            replace('？', '').\
            replace('您', '你').\
            replace(':', '').lower()
        return result_text

    def translate_text(self, service, source_text, source_language, target_language, expected_result):
        source_language_list = [x for x in self.translation_language_list if x['language_code'] == source_language.name and x['service'] == service.name]
        self.assertEqual(1, len(source_language_list))
        target_language_list = [x for x in self.translation_language_list if x['language_code'] == target_language.name and x['service'] == service.name]
        self.assertEqual(1, len(target_language_list))

        from_language_key = source_language_list[0]['language_id']
        to_language_key = target_language_list[0]['language_id']

        # now, translate
        translated_text = self.manager.get_translation(source_text, service.name, from_language_key, to_language_key)


        translated_text = self.sanitize_text(translated_text)

        if isinstance(expected_result, list):
            # multiple possible accepted translations
            expected_results = [self.sanitize_text(x) for x in expected_result]
            self.assertIn(translated_text, expected_results)
        else:
            # single value
            expected_result = self.sanitize_text(expected_result)
            self.assertEqual(expected_result, translated_text)

    def test_translate_chinese(self):
        # pytest test_translation.py -k test_translate_chinese
        self.translate_text(Service.Azure, '送外卖的人', Language.zh_cn, Language.en, ['the person who delivers the takeaway', 
        'people who deliver food', 'people who deliver takeaways', 'the person who delivered the takeaway', 'food delivery people',
        'delivery people'])
        self.translate_text(Service.Google, '中国有很多外国人', Language.zh_cn, Language.en, 'There are many foreigners in China')
        self.translate_text(Service.Azure, '成本很低', Language.zh_cn, Language.fr, 'Le coût est faible')
        self.translate_text(Service.Google, '换登机牌', Language.zh_cn, Language.fr, 
            ["Changer la carte d'embarquement", 
             "changer de carte d'embarquement", 
             "changer la carte d'embarquement",
             "échanger la carte d'embarquement"])
        self.translate_text(Service.Amazon, '换登机牌', Language.zh_cn, Language.fr, 
            ["utilisez votre carte d'embarquement", # seems wrong, but amazon returns this occasionally
             "modifier la carte d'embar", # seems wrong, but amazon returns this occasionally
             "carte d'embarquement", 
             "modifier la carte d'embarquement", 
             "changer la carte d'embarquement",
             "échangez votre carte d'embarquement",
             "modifiez votre carte d'embarquement"])

    def test_translate_chinese_amazon(self):
        self.translate_text(Service.Amazon, '中国有很多外国人', Language.zh_cn, Language.en, ['there are many foreigners in china', 'there are a lot of foreigners in china'])

    def test_translate_naver(self):
        # pytest test_translation.py -k test_translate_naver
        self.translate_text(Service.Naver, '천천히 말해 주십시오', Language.ko, Language.en, 'Please speak slowly.')
        self.translate_text(Service.Naver, 'Please speak slowly', Language.en, Language.ko, 
            ['천천히 말씀해 주세요', 
             '천천히 말해주세요'])

        self.translate_text(Service.Naver, '천천히 말해 주십시오', Language.ko, Language.fr, 
        [ "s'il vous plaît, parlez lentement", 
          "parlez lentement, s'il vous plaît",
          'parlez lentement'])

        self.translate_text(Service.Naver, 'Veuillez parler lentement.', Language.fr, Language.ko, '천천히 말씀해 주세요')        

    @pytest.mark.skip('2022/07 seems to work now')
    def test_translate_naver_unsupported_pair(self):
        # pytest test_translation.py -k test_translate_naver_unsupported_pair
        self.assertRaises(cloudlanguagetools.errors.RequestError, self.translate_text, Service.Naver, 'Veuillez parler lentement.', Language.fr, Language.th, 'Please speak slowly.')

    def test_translate_deepl(self):
        # pytest tests/test_translation.py -rPP -k test_translate_deepl
        self.translate_text(Service.DeepL, 'Please speak slowly', Language.en, Language.fr, 'Veuillez parler lentement')
        self.translate_text(Service.DeepL, 'Je ne suis pas intéressé.', Language.fr, Language.en, ["""I'm not interested.""", 'i am not interested'])
        self.translate_text(Service.DeepL, '送外卖的人', Language.zh_cn, Language.en, ['delivery person', 'takeaway delivery people'])

    def test_translate_portuguese_deepl(self):
        # pytest tests/test_translation.py -rPP -k test_translate_portuguese_deepl
        self.translate_text(Service.DeepL, 'Please speak slowly', Language.en, Language.pt_pt, 'por favor, fale devagar')
        self.translate_text(Service.DeepL, 'Please speak slowly', Language.en, Language.pt_br, 'por favor, fale devagar')

        self.translate_text(Service.DeepL, 'por favor, fale devagar', Language.pt_pt, Language.fr, 'veuillez parler lentement')
        self.translate_text(Service.DeepL, 'por favor, fale devagar', Language.pt_br, Language.fr, 'veuillez parler lentement')        

    
    # 2022/09/13: argos service disabled
    # def test_translate_chinese_argos(self):
    #     self.translate_text(Service.ArgosTranslate, '中国有很多外国人', Language.zh_cn, Language.en, 'there are many foreigners in china')

    # def test_translate_french_argos(self):
    #     self.translate_text(Service.ArgosTranslate, 'Please speak slowly', Language.en, Language.fr, 'Veuillez parler lentement.')

    @pytest.mark.skip('2023/08 libretranslate disabled')
    def test_translate_french_libretranslate(self):
        self.translate_text(Service.LibreTranslate, 'Please speak slowly', Language.en, Language.fr, 'Veuillez parler lentement.')        

    @pytest.mark.skip('2023/08 libretranslate disabled')
    def test_translate_chinese_libretranslate(self):
        self.translate_text(Service.LibreTranslate, '中国有很多外国人', Language.zh_cn, Language.en, 'there are many foreigners in china')

    def test_translate_all(self):
        # pytest test_translation.py -rPP -k test_translate_all
        # pytest test_translation.py --capture=no --log-cli-level=INFO -k test_translate_all

        source_text = '成本很低'
        from_language = Language.zh_cn.name
        to_language =  Language.fr.name
        result = self.manager.get_all_translations(source_text, from_language, to_language)
        self.assertTrue('Azure' in result)
        self.assertTrue('Google' in result)

        possible_french_translations = [
            'Très faible coût',
            'Le coût est faible',
            'Le coût est très faible',
            'à bas prix', 
            'Faible coût', 
            'À bas prix', 
            'faible coût', 
            'très faible coût',
            'Le coût est très bas.'
        ]

        self.assertIn(result['Azure'], possible_french_translations)
        self.assertIn(result['Google'], possible_french_translations)

    def test_translate_all_bug_vi(self):
        # pytest test_translation.py -rPP -k test_translate_all_bug_vi
        # pytest test_translation.py --capture=no --log-cli-level=INFO -k test_translate_all

        source_text = '<b><span style="font-weight: 400;">Thấy ghê … sao ám tui hoài vậy?</span></b>'
        from_language = Language.vi.name
        to_language =  Language.en.name
        result = self.manager.get_all_translations(source_text, from_language, to_language)
        pprint.pprint(result)
        self.assertTrue('Azure' in result)
        self.assertTrue('Google' in result)

    def test_transliteration_azure_custom(self):
        # pytest tests/test_translation.py -k test_transliteration_azure_custom
        
        # chinese
        source_text = '成本很低'
        service = 'Azure'
        # transliteration_key = transliteration_option['transliteration_key']
        transliteration_key = {
            'language_id': 'zh-Hans', 
            'from_script': 'Hans', 
            'to_script': 'Latn',
        }
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertIn(result, ['chéng běn hěn dī', 'chéngběn hěndī'])

        transliteration_key = {
            'language_id': 'zh-Hant', 
            'from_script': 'Hans', 
            'to_script': 'Hant',
        }
        result = self.manager.get_transliteration('讲话', service, transliteration_key)
        self.assertEqual(result, '講話')

    def test_transliteration_azure(self):
        # pytest tests/test_translation.py -k test_transliteration_azure
        
        # chinese
        source_text = '成本很低'
        from_language = Language.zh_cn.name
        service = 'Azure'
        transliteration_candidates = [
            x for x in self.transliteration_language_list 
            if x['language_code'] == from_language 
            and x['service'] == service
            and 'to Latin' in x['transliteration_shortname']]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertIn(result, ['chéng běn hěn dī', 'chéngběn hěndī'])

        # thai
        source_text = 'ประเทศไทย'
        service = 'Azure'
        from_language = Language.th.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertEqual(len(transliteration_candidates), 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('prathetthai', result)

    def test_pinyin_jyutping(self):
        # pytest tests/test_translation.py -k test_pinyin_jyutping
        # test direct access to the pinyin and jyuting functions (special case)


        # pinyin
        # ------

        source_text = '成本很低'
        result = self.manager.get_pinyin(source_text, False, False)
        self.assertEqual(result, {'word_list': ['成本', '很', '低'], 'solutions': [['chéngběn'], ['hěn'], ['dī']]})

        # try with corrections
        corrections = [
            {
                'chinese': '低',
                'pinyin': 'di4'
            }
        ]
        result = self.manager.get_pinyin(source_text, False, False, corrections=corrections)
        self.assertEqual(result, {'word_list': ['成本', '很', '低'], 'solutions': [['chéngběn'], ['hěn'], ['dì', 'dī']]})

        # jyutping
        # --------

        source_text = '全身按摩'
        expected_result = {'word_list': ['全身', '按摩'], 'solutions': [['cyùnsān'], ['ônmō']]}
        result = self.manager.get_jyutping(source_text, False, False)
        self.assertEqual(result, expected_result)

        # try with corrections
        corrections = [
            {
                'chinese': '按摩',
                'jyutping': 'on1mo1'
            }
        ]        
        result = self.manager.get_jyutping(source_text, False, False, corrections=corrections)
        self.assertEqual(result, {'word_list': ['全身', '按摩'], 'solutions': [['cyùnsān'], ['ōnmō', 'ônmō']]})


    def test_transliteration_mandarincantonese(self):
        # pytest tests/test_translation.py -k test_transliteration_mandarincantonese
        
        # chinese
        source_text = '成本很低'
        from_language = Language.zh_cn.name
        service = 'MandarinCantonese'
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language 
            and x['service'] == service 
            and x['transliteration_key']['tone_numbers'] == False
            and x['transliteration_key']['spaces'] == False]

        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('chéngběn hěn dī', result)

        # tone numbers
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language 
            and x['service'] == service 
            and x['transliteration_key']['tone_numbers'] == True
            and x['transliteration_key']['spaces'] == False]
        self.assertTrue(len(transliteration_candidates) == 1) 
        transliteration_option = transliteration_candidates[0]       
        transliteration_key = transliteration_option['transliteration_key']

        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('cheng2ben3 hen3 di1', result)

        # jyutping
        # '我出去攞野食'

        source_text = '我出去攞野食'
        from_language = Language.yue.name

        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language 
            and x['service'] == service 
            and x['transliteration_key']['tone_numbers'] == False
            and x['transliteration_key']['spaces'] == False]

        self.assertTrue(len(transliteration_candidates) == 1)

        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ngǒ cēothêoi ló jěsik', result)

    def verify_easypronunciation_english(self, input, expected_output):
        service = cloudlanguagetools.constants.Service.EasyPronunciation.name

        source_text = input
        from_language = Language.en.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language \
            and x['service'] == service \
            and x['transliteration_key'].get('variant', None) == None]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual(expected_output, result)


    def test_transliteration_easypronunciation(self):
        # pytest test_translation.py -rPP -k test_transliteration_easypronunciation

        # easypronunciation IPA test
        test_easy_pronunciation = True
        if not test_easy_pronunciation:
            return

        service = cloudlanguagetools.constants.Service.EasyPronunciation.name

        # french
        source_text = 'l’herbe est plus verte ailleurs'
        from_language = Language.fr.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('lɛʁb‿ ɛ ply vɛʁt‿ ajœʁ', result)

        # english
        source_text = 'do you have a boyfriend'
        from_language = Language.en.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        #self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertIn(result, ['ˈduː ˈjuː ˈhæv ə ˈbɔɪˌfɹɛnd', 'ˈduː jə həv ə ˈbɔɪˌfɹɛnd'])        

        self.verify_easypronunciation_english('take', 'ˈteɪk')
        self.verify_easypronunciation_english('poor', 'ˈpʊr')
        self.verify_easypronunciation_english('self', 'ˈsɛlf')

        # italian
        source_text = 'Piacere di conoscerla.'
        from_language = Language.it.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertIn(result, ['pjaˈtʃere di konoʃʃerla', 'pjaˈtʃere di koˈnoʃʃerla'])

        # japanese - Kana
        source_text = 'おはようございます'
        from_language = Language.ja.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service and 'Kana' in x['transliteration_name']]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('おはよー ございます', result)

        # japanese - romaji
        source_text = 'おはようございます'
        from_language = Language.ja.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service and 'Romaji' in x['transliteration_name']]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ohayo– gozaimasu', result)

        # portuguese - portugal
        source_text = 'Posso olhar a cozinha?'
        from_language = Language.pt_pt.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˈpɔsu oˈʎaɾ ɐ kuˈziɲɐ', result)

        # portuguese - brazil
        source_text = 'Perdi a minha carteira.'
        from_language = Language.pt_br.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('peʁˈdʒi a ˈmiɲɐ kaʁˈtejɾɐ', result)

        # spanish
        source_text = '¿A qué hora usted cierra?'
        from_language = Language.es.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertIn(result, ['a ˈke ˈoɾa u̯sˈtɛð ˈsjɛra', 'a ˈke ˈoɾa wsˈteð ˈsjera'])

        # german
        source_text = 'Können Sie mir das auf der Karte zeigen?'
        from_language = Language.de.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˈkœ.nən ˈziː ˈmiːɐ̯ das ˈaʊ̯f deːɐ ˈkar.tə ˈtsaɪ̯.ɡn̩', result)        

        # russian
        source_text = 'Могу я посмотреть меню?'
        from_language = Language.ru.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language and x['service'] == service]
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertIn(result, ['mɐ.ˈɡu ˈjæ pə.smɐ.ˈtrʲetʲ mʲɪ.ˈnʲʉ', 'mɐ.ˈɡu ˈja pə.smɐ.ˈtrʲetʲ mʲɪ.ˈnʲʉ'])


    def test_transliteration_easypronunciation_english_british_american(self):
        # pytest tests/test_translation.py -rPP -k test_transliteration_easypronunciation_english_british_american

        service = cloudlanguagetools.constants.Service.EasyPronunciation.name
        from_language = Language.en.name

        # british english
        # ===============

        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language \
            and x['service'] == service \
            and x['transliteration_key'].get('variant', None) == 'British']
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']

        source_text = 'car'
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˈkɑː', result)
        
        source_text = 'lot'
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˈlɒt', result)

        source_text = 'aluminium'
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˌæljəˈmɪniəm', result)

        # american english
        # ================

        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language \
            and x['service'] == service \
            and x['transliteration_key'].get('variant', None) == 'American']
        self.assertTrue(len(transliteration_candidates) == 1)
        transliteration_option = transliteration_candidates[0]
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']

        source_text = 'car'
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˈkɑːr', result)
        
        source_text = 'lot'
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˈlɑːt', result)

        source_text = 'aluminium'
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual('ˌæljəˈmɪniːəm', result)


    def verify_transliteration(self, source_text, transliteration_option, expected_output):
        service = transliteration_option['service']
        transliteration_key = transliteration_option['transliteration_key']
        result = self.manager.get_transliteration(source_text, service, transliteration_key)
        self.assertEqual(expected_output, result)        


    def verify_transliteration_single_option(self, from_language, source_text, service, expected_result):
        from_language_name = from_language.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language_name and x['service'] == service]
        self.assertEqual(len(transliteration_candidates), 1)
        transliteration_option = transliteration_candidates[0]
        self.verify_transliteration(source_text, transliteration_option, expected_result)


    def verify_transliteration_multiple_options(self, from_language, source_text, service, expected_result_list):
        from_language_name = from_language.name
        transliteration_candidates = [x for x in self.transliteration_language_list if x['language_code'] == from_language_name and x['service'] == service]

        actual_result_list = []
        for transliteration_option in transliteration_candidates:
            transliteration_key = transliteration_option['transliteration_key']
            result = self.manager.get_transliteration(source_text, service, transliteration_key)
            actual_result_list.append(result)

        # sort both actual and expected
        actual_result_list.sort()
        expected_result_list.sort()

        self.assertEqual(actual_result_list, expected_result_list)


    def test_transliteration_epitran(self):
        # pytest test_translation.py -rPP -k test_transliteration_epitran

        service = cloudlanguagetools.constants.Service.Epitran.name

        # french
        self.verify_transliteration_multiple_options(Language.fr, 'l’herbe est plus verte ailleurs', service, ['l’ɛʀbə ɛst plys vɛʀtə elœʀ', 'l’hɛrbɛ ɛst plys vɛrtɛ elœrs'])

        # english 
        self.verify_transliteration_single_option(Language.en, 'do you have a boyfriend', service, 'du ju hæv ə bojfɹɛnd')

        # german
        self.verify_transliteration_multiple_options(Language.de, 'Können Sie mir das auf der Karte zeigen?', 
            service, 
            ['kønnən siː mir das awf dər karte t͡sajeːɡən?',
            'kønən siː miʁ das auf deʁ kaɐte t͡saieɡən?',
            'kœnɛːn ziː miːr daːs aʊ̯f dɛːr kaːrtɛː t͡saɪ̯ɡɛːn?'])

        # spanish
        self.verify_transliteration_single_option(Language.es, '¿A qué hora usted cierra?', service, '¿a ke oɾa usted siera?')

    def test_transliteration_pythainlp(self):
        # pytest test_translation.py -rPP -k test_transliteration_pythainlp

        service = cloudlanguagetools.constants.Service.PyThaiNLP.name

        # thai
        self.verify_transliteration_multiple_options(Language.th, 'สวัสดี', service, ['s a ˧ . w a t̚ ˨˩ . d iː ˧', 'sawatdi'])

