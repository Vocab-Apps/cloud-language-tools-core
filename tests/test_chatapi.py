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
import cloudlanguagetools.chatapi
from cloudlanguagetools.languages import Language


def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestChatAPI(unittest.TestCase):
    def setUp(self):
        self.chatapi = cloudlanguagetools.chatapi.ChatAPI()

    def sanitize_text(self, recognized_text):
        result_text = recognized_text.replace('.', '').\
            replace('。', '').\
            replace('?', '').\
            replace('？', '').\
            replace('您', '你').\
            replace(':', '').lower()
        return result_text

    def test_translate(self):
        possible_translations = [
            "i am not interested",
            "i'm not interested"
        ]

        query = cloudlanguagetools.chatapi.TranslateQuery(
            input_text='Je ne suis pas intéressé.',
            source_language=Language.fr,
            target_language=Language.en
        )

        result = self.chatapi.translate(query)
        self.assertIn(self.sanitize_text(result), possible_translations)


    def test_transliterate(self):
        # chinese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='你好',
            language=Language.zh_cn
        )
        result = self.chatapi.transliterate(query)
        self.assertEqual(result, 'nǐhǎo')

        # japanese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='おはようございます',
            language=Language.ja
        )
        self.assertEqual(self.chatapi.transliterate(query), 'ohayo– gozaimasu')