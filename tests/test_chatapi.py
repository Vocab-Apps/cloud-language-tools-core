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
from cloudlanguagetools.languages import CommonLanguage


def get_manager():
    manager = cloudlanguagetools.servicemanager.ServiceManager()
    manager.configure_default()
    return manager

class TestChatAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manager = get_manager()
        cls.chatapi = cloudlanguagetools.chatapi.ChatAPI(cls.manager)

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

        query = cloudlanguagetools.chatapi.TranslateLookupQuery(
            input_text='Je ne suis pas intéressé.',
            source_language=CommonLanguage.fr,
            target_language=CommonLanguage.en
        )

        result = self.chatapi.translate(query)
        self.assertIn(self.sanitize_text(result), possible_translations)


    def test_transliterate_chinese(self):
        # chinese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='你好',
            language=CommonLanguage.zh_cn
        )
        result = self.chatapi.transliterate(query)
        self.assertEqual(result, 'nǐhǎo')

    def test_transliterate_chinese_pinyin(self):
        # chinese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='成本很低',
            language=CommonLanguage.zh_cn
        )
        result = self.chatapi.transliterate(query)
        self.assertEqual(result, 'chéngběn hěn dī')

    def test_transliterate_japanese(self):
        # japanese
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='おはようございます',
            language=CommonLanguage.ja
        )
        self.assertEqual(self.chatapi.transliterate(query), 'ohayo– gozaimasu')

    def test_transliterate_french(self):
        # french
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='l’herbe est plus verte ailleurs',
            language=CommonLanguage.fr
        )
        self.assertEqual(self.chatapi.transliterate(query), 'lɛʁb‿ ɛ ply vɛʁt‿ ajœʁ')


    def test_transliterate_thai(self):
        # thai
        query = cloudlanguagetools.chatapi.TransliterateQuery(
            input_text='สวัสดี',
            language=CommonLanguage.th
        )
        self.assertEqual(self.chatapi.transliterate(query), 'sawatdi')

    def test_dictionary_lookup_french(self):
        # french
        query = cloudlanguagetools.chatapi.TranslateLookupQuery(
            input_text='bonjour',
            source_language=CommonLanguage.fr,
            target_language=CommonLanguage.en
        )
        result = self.chatapi.dictionary_lookup(query)
        self.assertIn(result, ['hello', 'Hello / Hi / morning / greetings / Hey'])

    def test_dictionary_lookup_chinese(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_dictionary_lookup_chinese

        # chinese
        query = cloudlanguagetools.chatapi.TranslateLookupQuery(
            input_text='彩虹',
            source_language=CommonLanguage.zh_cn,
            target_language=CommonLanguage.en,
            service=cloudlanguagetools.constants.Service.Wenlin
        )
        result = self.chatapi.dictionary_lookup(query)
        self.assertEqual(result, 'rainbow')

    def test_translate_or_lookup_chinese(self):
        # pytest --log-cli-level=INFO tests/test_chatapi.py -k test_translate_or_lookup_chinese

        # chinese
        query = cloudlanguagetools.chatapi.TranslateLookupQuery(
            input_text='彩虹',
            source_language=CommonLanguage.zh_cn,
            target_language=CommonLanguage.en
        )
        result = self.chatapi.translate_or_lookup(query)
        self.assertEqual(result, 'rainbow')

        query = cloudlanguagetools.chatapi.TranslateLookupQuery(
            input_text='成本很低',
            source_language=CommonLanguage.zh_cn,
            target_language=CommonLanguage.en
        )
        result = self.chatapi.translate_or_lookup(query)
        self.assertEqual(result, 'The cost is low.')

    def assert_audio_matches(self, audio_temp_file, expected_text, azure_language):
        recognized_text = audio_utils.speech_to_text(self.chatapi.manager, audio_temp_file, azure_language)
        self.assertEqual(audio_utils.sanitize_recognized_text(recognized_text), audio_utils.sanitize_recognized_text(expected_text))

    def test_audio_french(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_french
        # french
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='bonjour',
            language=CommonLanguage.fr
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.mp3)
        self.assertTrue(audio_utils.is_mp3_format(audio_temp_file.name))
        self.assert_audio_matches(audio_temp_file, 'bonjour', 'fr-FR')

    def test_audio_chinese(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_chinese
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='老人家',
            language=CommonLanguage.zh_cn
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.mp3)
        self.assertTrue(audio_utils.is_mp3_format(audio_temp_file.name))
        self.assert_audio_matches(audio_temp_file, '老人家', 'zh-CN')

        
    def test_audio_recognition(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_recognition
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='老人家',
            language=CommonLanguage.zh_cn
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.mp3)
        recognized_text = self.chatapi.recognize_audio(audio_temp_file, cloudlanguagetools.options.AudioFormat.mp3)
        self.assertEqual(recognized_text, '老人家')

    def test_audio_recognition_french_ogg(self):
        # pytest --log-cli-level=DEBUG tests/test_chatapi.py -k test_audio_recognition_french_ogg
        query = cloudlanguagetools.chatapi.AudioQuery(
            input_text='bonjour',
            language=CommonLanguage.fr
        )
        audio_temp_file = self.chatapi.audio(query, cloudlanguagetools.options.AudioFormat.ogg_opus)
        self.assertTrue(audio_utils.is_ogg_opus_format(audio_temp_file.name))
        recognized_text = self.chatapi.recognize_audio(audio_temp_file, cloudlanguagetools.options.AudioFormat.ogg_opus)
        self.assertEqual(audio_utils.sanitize_recognized_text(recognized_text), 'bonjour')

    def test_breakdown_chinese(self):
        query = cloudlanguagetools.chatapi.BreakdownQuery(
            input_text='成本很低',
            language=CommonLanguage.zh_cn
        )
        result = self.chatapi.breakdown(query)
        expected_output = """成本: chéngběn, (manufacturing, production etc) costs
很: hěn, very much
低: dī, lower (one's head)"""
        self.assertEqual(result, expected_output)

    def test_breakdown_english(self):
        query = cloudlanguagetools.chatapi.BreakdownQuery(
            input_text="I was reading today's paper.",
            language=CommonLanguage.en,
            translation_language=CommonLanguage.fr
        )
        result = self.chatapi.breakdown(query)
        expected_output = """I: ˈaɪ, I (pronoun, personal)
was: /be ˈwəz, être (verb, past tense)
reading: /read ˈɹiːdɪŋ, lire (verb, gerund or present participle)
today: təˈdeɪ, aujourd'hui (noun, singular or mass)
's: (possessive ending)
paper: ˈpeɪpə˞, papier (noun, singular or mass)
.: (punctuation mark, sentence closer)"""
        self.assertEqual(result, expected_output)        