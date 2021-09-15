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