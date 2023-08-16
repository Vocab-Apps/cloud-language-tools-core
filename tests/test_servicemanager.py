import os
import sys
import logging
import unittest
import pytest
import json
import pprint

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.constants
from cloudlanguagetools.languages import Language
from cloudlanguagetools.constants import Service
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()

    def test_service_cost(self):
        self.assertEqual(self.manager.service_cost('abcd', 'Azure', cloudlanguagetools.constants.RequestType.translation), 4)
        self.assertEqual(self.manager.service_cost('abcd', 'Epitran', cloudlanguagetools.constants.RequestType.transliteration), 0)
        self.assertEqual(self.manager.service_cost('abcd', 'Naver', cloudlanguagetools.constants.RequestType.translation), 4)
        self.assertEqual(self.manager.service_cost('abcd', 'Naver', cloudlanguagetools.constants.RequestType.audio), 24)
        self.assertEqual(self.manager.service_cost('abcd', 'MandarinCantonese', cloudlanguagetools.constants.RequestType.transliteration), 0)


    def test_language_data_json_v2(self):
        language_data = self.manager.get_language_data_json_v2()
        
        # check free translation services
        free_translation_options = language_data['free']['translation_options']
        # check that libretranslate is there
        free_translation_services = list(set([option['service'] for option in free_translation_options]))
        self.assertEqual(free_translation_services, []) # libretranslate removed

        # check free transliteration services
        free_transliteration_options = language_data['free']['transliteration_options']
        free_transliteration_services = list(set([option['service'] for option in free_transliteration_options]))
        free_transliteration_services.sort()
        self.assertEqual(free_transliteration_services, ['Epitran', 'MandarinCantonese', 'PyThaiNLP'])