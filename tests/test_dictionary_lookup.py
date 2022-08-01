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
        
    def test_wenlin_definitions(self):
        service = Service.Wenlin

        definitions_lookup_options = [x for x in self.dictionary_lookup_list if x.service == service and
            x.language == Language.zh_cn and 
            x.lookup_type == DictionaryLookupType.Definitions]
        self.assertEqual(len(definitions_lookup_options), 1)
        lookup_option = definitions_lookup_options[0]

        result = self.manager.get_dictionary_lookup('仓库', service.name, lookup_option.get_lookup_key())

        self.assertEqual(result, ['warehouse; storehouse'])

