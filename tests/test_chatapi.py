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
import cloudlanguagetools.options
from cloudlanguagetools.languages import Language


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


    def test_transliterate_chinese(self):
        # chinese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='你好',
            language=Language.zh_cn
        )
        result = self.chatapi.transliterate(query)
        self.assertEqual(result, 'nǐhǎo')

    def test_transliterate_chinese_pinyin(self):
        # chinese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='成本很低',
            language=Language.zh_cn
        )
        result = self.chatapi.transliterate(query)
        self.assertEqual(result, 'chéngběn hěn dī')

    def test_transliterate_japanese(self):
        # japanese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='おはようございます',
            language=Language.ja
        )
        self.assertEqual(self.chatapi.transliterate(query), 'ohayo– gozaimasu')

    def test_transliterate_french(self):
        # french
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='l’herbe est plus verte ailleurs',
            language=Language.fr
        )
        self.assertEqual(self.chatapi.transliterate(query), 'lɛʁb‿ ɛ ply vɛʁt‿ ajœʁ')


    def test_transliterate_thai(self):
        # thai
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='สวัสดี',
            language=Language.th
        )
        self.assertEqual(self.chatapi.transliterate(query), 'sawatdi')

    def test_dictionary_lookup_french(self):
        # french
        query = cloudlanguagetools.chatapi.DictionaryLookup(
            input_text='bonjour',
            language=Language.fr,
        )
        result = self.chatapi.dictionary_lookup(query)
        self.assertEqual(result, 'hello')

    def test_dictionary_lookup_chinese(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_dictionary_lookup_chinese

        # chinese
        query = cloudlanguagetools.chatapi.DictionaryLookup(
            input_text='彩虹',
            language=Language.zh_cn,
            service=cloudlanguagetools.constants.Service.Wenlin
        )
        result = self.chatapi.dictionary_lookup(query)
        self.assertEqual(result, 'rainbow')

    def assert_audio_matches(self, audio_temp_file, expected_text, azure_language):
        recognized_text = audio_utils.speech_to_text(self.chatapi.manager, audio_temp_file, azure_language)
        self.assertEqual(audio_utils.sanitize_recognized_text(recognized_text), audio_utils.sanitize_recognized_text(expected_text))

    def test_audio_french(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_french
        # french
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='bonjour',
            language=Language.fr
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.mp3)
        self.assertTrue(audio_utils.is_mp3_format(audio_temp_file.name))
        self.assert_audio_matches(audio_temp_file, 'bonjour', 'fr-FR')

    def test_audio_chinese(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_chinese
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='老人家',
            language=Language.zh_cn
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.mp3)
        self.assertTrue(audio_utils.is_mp3_format(audio_temp_file.name))
        self.assert_audio_matches(audio_temp_file, '老人家', 'zh-CN')

        
    def test_audio_recognition(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_recognition
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='老人家',
            language=Language.zh_cn
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.mp3)
        recognized_text = self.chatapi.recognize_audio(audio_temp_file, cloudlanguagetools.options.AudioFormat.mp3)
        self.assertEqual(recognized_text, '老人家')

    def test_audio_recognition_french_ogg(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_recognition_french_ogg
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='bonjour',
            language=Language.fr
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.ogg_opus)
        self.assertTrue(audio_utils.is_ogg_opus_format(audio_temp_file.name))
        recognized_text = self.chatapi.recognize_audio(audio_temp_file, cloudlanguagetools.options.AudioFormat.ogg_opus)
        self.assertEqual(audio_utils.sanitize_recognized_text(recognized_text), 'bonjour')