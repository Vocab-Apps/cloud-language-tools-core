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
        self.audio_list = [] # list of tempfile.NamedTemporaryFile
        self.error_list = []
        logger.info('creating chat model')
        self.chat_model = cloudlanguagetools.chatmodel.ChatModel(self.manager)
        self.chat_model.set_send_message_callback(self.send_message_fn, self.send_audio_fn, self.send_error_fn)

    def send_error_fn(self, message):
        self.error_list.append(message)

    def send_message_fn(self, message):
        self.message_list.append(message)
    
    def send_audio_fn(self, audio_tempfile):
        self.audio_list.append(audio_tempfile)
    
    def verify_single_audio_message(self, expected_audio_message, recognition_language):
        self.assertEquals(len(self.audio_list), 1)  
        recognized_text = audio_utils.speech_to_text(self.manager, self.audio_list[0], recognition_language)
        self.assertEquals(audio_utils.sanitize_recognized_text(recognized_text), expected_audio_message)
        self.audio_list = []

    def verify_messages(self, expected_message_list):
        self.assertEquals(self.message_list, expected_message_list)
        self.message_list = []

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


    def test_chinese_translation_breakdown(self):
        # pytest --log-cli-level=DEBUG tests/test_chatmodel.py -k test_chinese_translation_breakdown

        instruction = "When given a sentence in Chinese, translate it to English, then breakdown the chinese sentence"
        self.chat_model.set_instruction(instruction)

        self.chat_model.process_message("成本很低")
        self.assertEquals(self.message_list, ["The cost is low.", """成本: chéngběn, (manufacturing, production etc) costs
很: hěn, very much
低: dī, lower (one's head)"""])


    def test_chinese_translation_audio(self):
        # pytest --log-cli-level=DEBUG tests/test_chatmodel.py -k test_chinese_translation_audio

        instruction = "When given a sentence in Chinese, translate it to English, and pronounce the chinese sentence."
        self.chat_model.set_instruction(instruction)

        self.chat_model.process_message("成本很低")
        self.assertEquals(self.message_list, ["The cost is low."])

        self.assertEquals(len(self.audio_list), 1)  
        recognized_text = audio_utils.speech_to_text(self.manager, self.audio_list[0], 'zh-CN')
        self.assertEquals(audio_utils.sanitize_recognized_text(recognized_text), '成本很低')

    def test_cantonese_audio(self):
        # pytest --log-cli-level=DEBUG tests/test_chatmodel.py -k test_cantonese_audio
        # pytest --log-cli-level=INFO tests/test_chatmodel.py -k test_cantonese_audio

        self.chat_model.process_message('pronounce "天氣預報" in cantonese')
        self.verify_single_audio_message('天氣預報', 'zh-HK')


    def test_cantonese_instructions(self):
        """test whether the model can follow steps repeatedly when given new input sentences"""
        instructions = 'when I give you a sentence in cantonese, pronounce it using Azure service, then translate it into english, and break down the cantonese sentence into words'
        self.chat_model.set_instruction(instructions)

        # first input sentence
        self.chat_model.process_message('呢條路係行返屋企嘅路')
        self.verify_single_audio_message('呢條路係行返屋企嘅路', 'zh-HK')
        self.verify_messages(['This road is the way home',
"""呢: nèi, this
條路: tìulou, road
係: hai, Oh, yes
行返: hàngfáan, Walk back
屋企: ūkkéi, home
嘅: gê, target
路: lou, road"""])

        # second input sentence
        self.chat_model.process_message('我最頂唔順嗰樣嘢')
        self.verify_single_audio_message('我最頂唔順果樣嘢', 'zh-HK')
        self.verify_messages(["I can't stand that kind of stuff the most",
"""我: ngǒ, I
最頂: zêoidíng, Top
唔: m, No
順: seon, shun
嗰: gó, that
樣: joeng, shape
嘢: jě, stuff"""])

        # third input sentence
        self.chat_model.process_message('黑社會')
        self.verify_single_audio_message('黑社會', 'zh-HK')
        self.verify_messages(["I can't stand that kind of stuff the most",
            """黑社會: hāksěwúi, underworld"""])        
