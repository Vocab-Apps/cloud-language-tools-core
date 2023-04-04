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
import cloudlanguagetools.errors

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.manager = get_manager()


    def sanitize_text(self, translation_text):
        result_text = translation_text.replace('.', '').\
            replace(',', '').\
            replace('。', '').\
            replace('?', '').\
            replace('？', '').\
            replace('您', '你').\
            replace(':', '').lower()
        return result_text

    def test_single_prompt(self):
        prompt = 'translate to French: speak slowly please.'
        response, tokens = self.manager.openai_single_prompt(prompt)
        self.assertEqual(self.sanitize_text("Parlez lentement s'il vous plaît."), self.sanitize_text(response))