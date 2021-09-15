import sys
import logging
import unittest
import pprint
import secrets
import cloudlanguagetools
import cloudlanguagetools.servicemanager
from cloudlanguagetools.constants import Language
from cloudlanguagetools.constants import Service
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager(secrets.config)
    manager.configure()    
    manager.load_data()
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                            datefmt='%Y%m%d-%H:%M:%S',
                            stream=sys.stdout,
                            level=logging.DEBUG)

        self.manager = get_manager()
        self.language_data = self.manager.get_language_data_json()

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