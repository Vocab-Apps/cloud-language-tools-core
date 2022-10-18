import os
import sys
import logging
import unittest
import pprint

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

class TestMockServices(unittest.TestCase):
    
    def test_language_data(self):
        if os.environ.get('CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES', 'no') != 'yes':
            return

        manager = get_manager()
        language_data = manager.get_language_data_json()
        self.assertTrue(len(language_data) > 0)
