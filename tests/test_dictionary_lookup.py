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
from cloudlanguagetools.constants import DictionaryLookupType
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestDictionaryLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                            datefmt='%Y%m%d-%H:%M:%S',
                            stream=sys.stdout,
                            level=logging.DEBUG)

        cls.manager = get_manager()
        cls.dictionary_lookup_list = cls.manager.get_dictionary_lookup_options()
        
    def test_service_list(self):
        definitions_lookup_options = [x for x in self.dictionary_lookup_list if 
            x.language == Language.zh_cn and 
            x.target_language == Language.en and
            x.lookup_type == DictionaryLookupType.Definitions]        

        self.assertEqual(len(definitions_lookup_options), 2)

        pprint.pprint(definitions_lookup_options)

        lookup_option_azure = [x for x in definitions_lookup_options if x.service == Service.Azure][0]
        self.assertEqual(lookup_option_azure.get_lookup_name(), 'Azure (Chinese (Simplified) to English), Definitions')

        lookup_option_azure = [x for x in definitions_lookup_options if x.service == Service.Wenlin][0]
        self.assertEqual(lookup_option_azure.get_lookup_name(), 'Wenlin (Chinese (Simplified) to English), Definitions')


    def test_wenlin_definitions(self):
        service = Service.Wenlin

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.Definitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('仓库', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, ['warehouse; storehouse'])

        result = self.manager.get_dictionary_lookup('啊', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result,  ['used as phrase suffix',
            'in enumeration',
            'in direct address and exclamation',
            'indicating obviousness/impatience',
            'for confirmation',
            'indicating elation',
            'indicating doubt or questioning',
            'indicating puzzled surprise',
            'indicating agreement/approval'])        

    def test_wenlin_not_found(self):
        service = Service.Wenlin

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.Definitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        self.assertRaises(cloudlanguagetools.errors.NotFoundError, 
            self.manager.get_dictionary_lookup, '仓库仓库', service.name, lookup_option.get_lookup_key())


    def test_wenlin_part_of_speech(self):
        service = Service.Wenlin

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.PartOfSpeech]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('仓库', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, ['p.w.'])

        result = self.manager.get_dictionary_lookup('啊', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result,  ['intj.', 'm.p.'])


    def test_wenlin_measure_word(self):
        service = Service.Wenlin

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.MeasureWord]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('仓库', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, ['⁴zuò [座]'])

        result = self.manager.get_dictionary_lookup('学生', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, ['ge/míng/²wèi [个/名/位]'])

    def test_wenlin_part_of_speech_definitions(self):
        service = Service.Wenlin

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.PartOfSpeechDefinitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('学生', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, {'n.': ['student; pupil', 'disciple; follower', 'boy; lad']})


    def test_azure_definitions(self):
        service = Service.Azure

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.Definitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('仓库', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, ['warehouse', 'storehouse', 'depot', 'repository', 'storage'])

        result = self.manager.get_dictionary_lookup('啊', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result,  ['ah', 'Oh', 'huh', 'o', 'yes'])

    def test_azure_partofspeech(self):
        service = Service.Azure

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.PartOfSpeech]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('仓库', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, ['noun'])

        result = self.manager.get_dictionary_lookup('啊', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result,  ['noun', 'prep'])

    def test_azure_partofspeech_definitions(self):
        service = Service.Azure

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.PartOfSpeechDefinitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('学生', service.name, lookup_option.get_lookup_key())
        self.assertEqual(result, {'noun': ['students', 'pupils', 'college students']})


    def test_azure_french(self):
        service = Service.Azure

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.fr and 
            x.target_language == Language.en and 
            x.lookup_type == DictionaryLookupType.Definitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('boulangerie', service.name, lookup_option.get_lookup_key())
        self.assertIn(result, [['bakery', 'baked goods', 'baked', 'baking'],
                               ['bakery']])


    def test_azure_notfound(self):
        service = Service.Azure

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.fr and 
            x.target_language == Language.en and 
            x.lookup_type == DictionaryLookupType.Definitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        self.assertRaises(cloudlanguagetools.errors.NotFoundError, 
            self.manager.get_dictionary_lookup, 'cemotnexistepas', service.name, lookup_option.get_lookup_key())

