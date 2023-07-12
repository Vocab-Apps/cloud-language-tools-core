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
        self.chat_model = cloudlanguagetools.chatmodel.ChatModel(self.manager)

    
    def test_translation(self):
        # pytest --log-cli-level=DEBUG tests/test_chatmodel.py -k test_translation

        message_list = []
        def get_send_message_lambda():
            def send_message(message):
                message_list.append(message)
            return send_message

        instruction = "When given a sentence in French, translate it to English"
        self.chat_model.set_instruction(instruction)
        self.chat_model.set_send_message_callback(get_send_message_lambda())

        self.chat_model.process_message("Je ne suis pas intéressé.")
        self.assertEquals(message_list, ["I'm not interested."])
