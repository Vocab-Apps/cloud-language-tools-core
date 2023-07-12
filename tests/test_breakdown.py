import os
import sys
import logging
import unittest
import pprint
import requests
import time
import json

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

class TestBreakdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                            datefmt='%Y%m%d-%H:%M:%S',
                            stream=sys.stdout,
                            level=logging.DEBUG)

        cls.manager = get_manager()

        num_tries = 3
        success = False
        while success == False and num_tries >= 0:
            num_tries -= 1
            try:
                cls.language_data = cls.manager.get_language_data_json()
                success = True
            except requests.exceptions.ReadTimeout as e:
                logging.exception(f'could not get language data, timeout')
                time.sleep(1)

        

    def test_language_list(self):
        self.assertTrue(len(self.language_data['language_list']) > 0)
        # check for the presence of a few languages
        self.assertEqual('French', self.language_data['language_list']['fr'])
        self.assertEqual('Chinese (Simplified)', self.language_data['language_list']['zh_cn'])
        self.assertEqual('Thai', self.language_data['language_list']['th'])
        self.assertEqual('Chinese (Cantonese, Traditional)', self.language_data['language_list']['yue'])
        self.assertEqual('Chinese (Traditional)', self.language_data['language_list']['zh_tw'])    

    def test_breakdown_thai(self):
        # pytest test_breakdown.py -s -rPP -k test_breakdown_thai
        # pytest test_breakdown.py -s --log-cli-level=DEBUG -k test_breakdown_thai

        text = 'ดิฉันอายุยี่สิบเจ็ดปีค่ะ'
        source_language = 'th'
        target_language = 'en'

        # choose breakdown
        tokenization_service = 'PyThaiNLP'
        tokenization_candidates = [x for x in self.language_data['tokenization_options'] if x['language_code'] == source_language and x['service'] == tokenization_service]
        self.assertEqual(len(tokenization_candidates), 1)
        tokenization_option = tokenization_candidates[0]

        # choose transliteration
        transliteration_service = 'PyThaiNLP'
        transliteration_candidates = [x for x in self.language_data['transliteration_options'] if x['language_code'] == source_language and x['service'] == transliteration_service]
        transliteration_option = transliteration_candidates[0]

        # choose translation
        translation_service = 'Azure'
        source_language_id = [x for x in self.language_data['translation_options'] if x['language_code'] == source_language and x['service'] == translation_service][0]['language_id']
        target_language_id = [x for x in self.language_data['translation_options'] if x['language_code'] == target_language and x['service'] == translation_service][0]['language_id']
        translation_option = {
            'service': translation_service,
            'source_language_id': source_language_id,
            'target_language_id': target_language_id
        }

        # run the breakdown
        breakdown_result = self.manager.get_breakdown(text, tokenization_option, translation_option, transliteration_option)
        pprint.pprint(breakdown_result)

        expected_output = [{'lemma': 'ดิฉัน',
        'token': 'ดิฉัน',
        'translation': 'I',
        'transliteration': 'dichan'},
        {'lemma': 'อายุ',
        'token': 'อายุ',
        'translation': 'age',
        'transliteration': 'ayu'},
        {'lemma': 'ยี่สิบ',
        'token': 'ยี่สิบ',
        'translation': 'twenty',
        'transliteration': 'yisip'},
        {'lemma': 'เจ็ด',
        'token': 'เจ็ด',
        'translation': 'seven',
        'transliteration': 'chet'},
        {'lemma': 'ปี', 'token': 'ปี', 'translation': 'year', 'transliteration': 'pi'},
        {'lemma': 'ค่ะ',
        'token': 'ค่ะ',
        'translation': 'yes',
        'transliteration': 'kha'}]

        self.assertEqual(breakdown_result, expected_output)

        # try same breakdown with spaces, result should be the same
        text = 'ดิฉัน อายุ ยี่สิบเจ็ดปีค่ะ'
        breakdown_result = self.manager.get_breakdown(text, tokenization_option, translation_option, transliteration_option)
        self.assertEqual(breakdown_result, expected_output)

        # add punctuation
        text = 'ดิฉัน, อายุ ยี่สิบเจ็ดปีค่ะ'
        breakdown_result = self.manager.get_breakdown(text, tokenization_option, translation_option, transliteration_option)
        self.assertEqual(breakdown_result, expected_output)        


    def test_breakdown_english(self):
        # pytest test_breakdown.py -s -rPP -k test_breakdown_english

        text = "I was reading today's paper."
        source_language = 'en'
        target_language = 'fr'

        # choose breakdown
        tokenization_service = 'Spacy'
        tokenization_candidates = [x for x in self.language_data['tokenization_options'] if x['language_code'] == source_language and x['service'] == tokenization_service]
        self.assertEqual(len(tokenization_candidates), 1)
        tokenization_option = tokenization_candidates[0]

        # choose transliteration
        transliteration_service = 'Epitran'
        transliteration_candidates = [x for x in self.language_data['transliteration_options'] if x['language_code'] == source_language and x['service'] == transliteration_service]
        transliteration_option = transliteration_candidates[0]

        # choose translation
        translation_service = 'Azure'
        source_language_id = [x for x in self.language_data['translation_options'] if x['language_code'] == source_language and x['service'] == translation_service][0]['language_id']
        target_language_id = [x for x in self.language_data['translation_options'] if x['language_code'] == target_language and x['service'] == translation_service][0]['language_id']
        translation_option = {
            'service': translation_service,
            'source_language_id': source_language_id,
            'target_language_id': target_language_id
        }

        # run the breakdown
        breakdown_result = self.manager.get_breakdown(text, tokenization_option, translation_option, transliteration_option)
        pprint.pprint(breakdown_result)

        expected_output = [{'lemma': 'I',
        'pos_description': 'pronoun, personal',
        'token': 'I',
        'translation': 'Je',
        'transliteration': 'aj'},
        {'lemma': 'be',
        'pos_description': 'verb, past tense',
        'token': 'was',
        'translation': 'être',
        'transliteration': 'wɑz'},
        {'lemma': 'read',
        'pos_description': 'verb, gerund or present participle',
        'token': 'reading',
        'translation': 'lire',
        'transliteration': 'ɹɛdɪŋ'},
        {'lemma': 'today',
        'pos_description': 'noun, singular or mass',
        'token': 'today',
        'translation': 'Aujourd’hui',
        'transliteration': 'tədej'},
        {'lemma': "'s", 'pos_description': 'possessive ending', 'token': "'s"},
        {'lemma': 'paper',
        'pos_description': 'noun, singular or mass',
        'token': 'paper',
        'translation': 'papier',
        'transliteration': 'pejpɹ̩'},
        {'lemma': '.',
        'pos_description': 'punctuation mark, sentence closer',
        'token': '.'}]

        self.assertEqual(breakdown_result, expected_output)

    def test_tokenization_pythainlp(self):
        # pytest test_breakdown.py -rPP -k test_tokenization_pythainlp

        service = cloudlanguagetools.constants.Service.PyThaiNLP.name

        tokenization_candidates = [x for x in self.language_data['tokenization_options'] if x['language_code'] == Language.th.name and x['service'] == service]
        self.assertEqual(len(tokenization_candidates), 1)
        tokenization_option = tokenization_candidates[0]

        # thai
        tokenization_result = self.manager.get_tokenization('ดิฉันอายุยี่สิบเจ็ดปีค่ะ', service, tokenization_option['tokenization_key'])
        
        expected_result = [
            {'token': 'ดิฉัน', 'lemma': 'ดิฉัน', 'can_translate': True, 'can_transliterate': True}, 
            {'token': 'อายุ', 'lemma': 'อายุ', 'can_translate': True, 'can_transliterate': True},
            {'token': 'ยี่สิบ', 'lemma': 'ยี่สิบ', 'can_translate': True, 'can_transliterate': True},
            {'token': 'เจ็ด', 'lemma': 'เจ็ด', 'can_translate': True, 'can_transliterate': True},
            {'token': 'ปี', 'lemma': 'ปี', 'can_translate': True, 'can_transliterate': True},
            {'token': 'ค่ะ', 'lemma': 'ค่ะ', 'can_translate': True, 'can_transliterate': True}
        ]

        self.assertEqual(tokenization_result, expected_result)

    def test_tokenization_spacy(self):
        # pytest test_breakdown.py -rPP -k test_tokenization_spacy

        service = cloudlanguagetools.constants.Service.Spacy.name

        language = Language.en.name
        tokenization_candidates = [x for x in self.language_data['tokenization_options'] if x['language_code'] == language and x['service'] == service]
        self.assertEqual(len(tokenization_candidates), 1)
        tokenization_option = tokenization_candidates[0]

        # english
        # =======

        text = "I was reading today's paper."
        tokenization_result = self.manager.get_tokenization(text, service, tokenization_option['tokenization_key'])
        # pprint.pprint(tokenization_result)
        
        expected_result = [{'can_translate': True,
            'can_transliterate': True,
            'lemma': 'I',
            'pos_description': 'pronoun, personal',
            'token': 'I'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'be',
            'pos_description': 'verb, past tense',
            'token': 'was'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'read',
            'pos_description': 'verb, gerund or present participle',
            'token': 'reading'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'today',
            'pos_description': 'noun, singular or mass',
            'token': 'today'},
            {'can_translate': False,
            'can_transliterate': False,
            'lemma': "'s",
            'pos_description': 'possessive ending',
            'token': "'s"},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'paper',
            'pos_description': 'noun, singular or mass',
            'token': 'paper'},
            {'can_translate': False,
            'can_transliterate': False,
            'lemma': '.',
            'pos_description': 'punctuation mark, sentence closer',
            'token': '.'}]
        self.assertEqual(tokenization_result, expected_result)        

    def test_tokenization_spacy_french(self):
        # pytest test_breakdown.py -rPP -k test_tokenization_spacy_french

        self.maxDiff = None

        service = cloudlanguagetools.constants.Service.Spacy.name

        # french
        # ======

        language = Language.fr.name
        tokenization_candidates = [x for x in self.language_data['tokenization_options'] if x['language_code'] == language and x['service'] == service]
        self.assertEqual(len(tokenization_candidates), 1)
        tokenization_option = tokenization_candidates[0]

        text = "Le nouveau plan d’investissement du gouvernement."
        tokenization_result = self.manager.get_tokenization(text, service, tokenization_option['tokenization_key'])
        # pprint.pprint(tokenization_result)
        
        expected_result = [{'can_translate': True,
            'can_transliterate': True,
            'lemma': 'le',
            'pos_description': 'determiner',
            'token': 'Le'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'nouveau',
            'pos_description': 'adjective',
            'token': 'nouveau'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'plan',
            'pos_description': 'noun',
            'token': 'plan'},
            {'can_translate': False,
            'can_transliterate': False,
            'lemma': 'd’',
            'pos_description': 'adposition',
            'token': 'd’'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'investissement',
            'pos_description': 'noun',
            'token': 'investissement'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'de',
            'pos_description': 'adposition',
            'token': 'du'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': 'gouvernement',
            'pos_description': 'noun',
            'token': 'gouvernement'},
            {'can_translate': False,
            'can_transliterate': False,
            'lemma': '.',
            'pos_description': 'punctuation',
            'token': '.'}]

        self.assertEqual(tokenization_result, expected_result)                


    def test_tokenization_spacy_chinese(self):
        # pytest test_breakdown.py -rPP -k test_tokenization_spacy_chinese

        service = cloudlanguagetools.constants.Service.Spacy.name

        language = Language.zh_cn.name
        tokenization_options = [x for x in self.language_data['tokenization_options'] if x['language_code'] == language and x['service'] == service]

        text = "送外卖的人"

        expected_result_chars = [{'can_translate': True,
            'can_transliterate': True,
            'lemma': '送',
            'token': '送'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': '外',
            'token': '外'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': '卖',
            'token': '卖'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': '的',
            'token': '的'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': '人',
            'token': '人'}]

        expected_result_words = [{'can_translate': True,
            'can_transliterate': True,
            'lemma': '送',
            'token': '送'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': '外卖',
            'token': '外卖'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': '的',
            'token': '的'},
            {'can_translate': True,
            'can_transliterate': True,
            'lemma': '人',
            'token': '人'}]

        self.assertEqual(self.manager.get_tokenization(text, service, tokenization_options[0]['tokenization_key']), expected_result_words)
        self.assertEqual(self.manager.get_tokenization(text, service, tokenization_options[1]['tokenization_key']), expected_result_chars)
        self.assertEqual(self.manager.get_tokenization(text, service, tokenization_options[2]['tokenization_key']), expected_result_words)        