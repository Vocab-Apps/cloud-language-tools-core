import os
import sys
import logging
import unittest
import pytest
import json
import pprint
import audio_utils

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools
import cloudlanguagetools.servicemanager
import cloudlanguagetools.chatapi
import cloudlanguagetools.chatmodel

logger = logging.getLogger(__name__)

def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestChatModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manager = get_manager()

    def setUp(self):
        self.message_list = []
        self.chat_model = cloudlanguagetools.chatmodel.ChatModel(self.manager)
        self.chat_model.set_send_message_callback(self.send_message_fn)        

    def send_message_fn(self, message):
        self.message_list.append(message)
    
    def test_french_translation(self):
        # pytest --log-cli-level=DEBUG tests/test_chatmodel.py -k test_french_translation

        instruction = "When given a sentence in French, translate it to English"
        self.chat_model.set_instruction(instruction)

        self.chat_model.process_message("Je ne suis pas intéressé.")
        self.assertEquals(self.message_list, ["I'm not interested."])


    def test_chinese_translation_transliteration(self):
        # pytest --log-cli-level=DEBUG tests/test_chatmodel.py -k test_chinese_translation_transliteration

        instruction = "When given a sentence in Chinese, translate it to English, then transliterate the Chinese"
        self.chat_model.set_instruction(instruction)

        self.chat_model.process_message("成本很低")
        self.assertEquals(self.message_list, ["The cost is low.", 'chéngběn hěn dī'])