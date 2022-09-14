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
        self.assertEqual(self.manager.service_cost('abcd', 'LibreTranslate', cloudlanguagetools.constants.RequestType.translation), 0)
        self.assertEqual(self.manager.service_cost('abcd', 'Epitran', cloudlanguagetools.constants.RequestType.transliteration), 0)
        self.assertEqual(self.manager.service_cost('abcd', 'Naver', cloudlanguagetools.constants.RequestType.translation), 4)
        self.assertEqual(self.manager.service_cost('abcd', 'Naver', cloudlanguagetools.constants.RequestType.audio), 24)
        self.assertEqual(self.manager.service_cost('abcd', 'MandarinCantonese', cloudlanguagetools.constants.RequestType.transliteration), 0)

