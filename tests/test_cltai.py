"""CLT-AI API integration tests: these make real (paid) API calls.
run with: uv run pytest tests/test_cltai.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.servicemanager
import cloudlanguagetools.encryption
import cloudlanguagetools.cltai.agent
from cloudlanguagetools.constants import Service, Gender
from cloudlanguagetools.cltai import (create_client, CltAPIVersion, CltAIError, SoundRequest, SoundResult,
    TranslateRequest, TransliterateRequest, TranscribeRequest, LlmRequest)
import audio_utils


def sanitize(text):
    return audio_utils.sanitize_recognized_text(text).replace('!', '').replace('、', '').replace('，', '').strip()


class TestCltAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manager = cloudlanguagetools.servicemanager.ServiceManager(cloudlanguagetools.encryption.load_configuration())
        cls.clt = create_client(CltAPIVersion.v1, manager=manager)

    # sound
    # =====

    def test_sound_defaults(self):
        # pytest tests/test_cltai.py -k test_sound_defaults
        # no service / gender specified: Azure, female, main locale
        result = self.clt.sound(SoundRequest(text='今日はいい天気ですね', language='ja'))
        self.assertEqual(result.service, Service.Azure)
        self.assertEqual(result.audio_language.name, 'ja_JP')
        voice = [v for v in self.clt.list_voices(language='ja', service='Azure') if v.voice_key == result.voice_key][0]
        self.assertEqual(voice.gender, Gender.Female)
        self.assertTrue(audio_utils.is_mp3_format(result.audio_path))
        transcription = self.clt.transcribe(TranscribeRequest(audio=result))
        self.assertEqual(sanitize(transcription.text), sanitize('今日はいい天気ですね'))

    def test_sound_pinned_voice_ogg(self):
        # pytest tests/test_cltai.py -k test_sound_pinned_voice_ogg
        voice_key = {'name': 'Microsoft Server Speech Text to Speech Voice (fr-FR, HenriNeural)'}
        resolved = self.clt.validate_sound(text='Bonjour', language='fr', service='Azure', voice_key=voice_key)
        self.assertEqual(resolved.voice_key, voice_key)
        result = self.clt.sound(SoundRequest(text='Il fait beau aujourd\'hui', language='fr', service='Azure',
            voice_key=voice_key, options={'rate': 0.9}, format='ogg_opus'))
        self.assertTrue(result.audio_path.endswith('.ogg'))
        self.assertTrue(audio_utils.is_ogg_opus_format(result.audio_path))
        self.assertEqual(result.options, {'rate': 0.9})

    def test_sound_converted_format(self):
        # pytest tests/test_cltai.py -k test_sound_converted_format
        # Google doesn't produce ogg_vorbis natively, the client converts from mp3
        result = self.clt.sound(text='Guten Morgen', language='de', service='Google', format='ogg_vorbis')
        self.assertEqual(result.service, Service.Google)
        self.assertTrue(result.audio_path.endswith('.ogg'))

    def test_sound_gender_and_locale(self):
        resolved = self.clt.validate_sound(text='hello', language='en', audio_language='en_GB', gender='Male', service='Azure')
        self.assertEqual(resolved.audio_language.name, 'en_GB')
        voice = [v for v in self.clt.list_voices(audio_language='en_GB', service='Azure') if v.voice_key == resolved.voice_key][0]
        self.assertEqual(voice.gender, Gender.Male)

    def test_sound_invalid_options(self):
        with self.assertRaisesRegex(CltAIError, 'rate'):
            self.clt.validate_sound(text='bonjour', language='fr', service='Azure', options={'rate': 10.0})
        with self.assertRaisesRegex(CltAIError, 'invalid options'):
            self.clt.validate_sound(text='bonjour', language='fr', service='Azure', options={'unknown_option': 1})
        with self.assertRaisesRegex(CltAIError, 'voice_name'):
            self.clt.validate_sound(text='bonjour', language='fr', service='Azure', voice_name='Nonexistent Voice')
        # OpenAI options model: speed range is 0.25 - 4.0
        with self.assertRaisesRegex(CltAIError, 'speed'):
            self.clt.validate_sound(text='bonjour', language='fr', service='OpenAI', voice_name='alloy', options={'speed': 5})

    def test_describe_voice_options(self):
        schema = self.clt.describe_voice_options('Azure', voice_key={'name': 'Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)'})
        self.assertIn('rate', schema['properties'])
        self.assertIn('pitch', schema['properties'])

    # translate
    # =========

    def test_translate(self):
        # pytest tests/test_cltai.py -k test_translate
        result = self.clt.translate(TranslateRequest(text='Je ne suis pas intéressé.', source_language='fr', target_language='en'))
        self.assertEqual(result.service, Service.DeepL)
        self.assertIn(sanitize(result.text), ["i'm not interested", 'i am not interested'])
        result = self.clt.translate(text='Je ne suis pas intéressé.', source_language='fr', target_language='en', service='Azure')
        self.assertEqual(result.service, Service.Azure)
        services = [s.service for s in self.clt.list_translation_services('fr', 'en')]
        self.assertEqual(services[0], Service.DeepL)
        self.assertIn(Service.Google, services)

    # transliterate
    # =============

    def test_transliterate_pinyin(self):
        # pytest tests/test_cltai.py -k test_transliterate_pinyin
        result = self.clt.transliterate(TransliterateRequest(text='成本很低', language='zh_cn'))
        self.assertEqual(result.service, Service.MandarinCantonese)
        self.assertEqual(result.text, 'chéngběn hěn dī')
        result = self.clt.transliterate(text='成本很低', language='zh_cn', transliteration_name='tone numbers')
        self.assertEqual(result.text, 'cheng2ben3 hen3 di1')

    def test_transliterate_jyutping(self):
        result = self.clt.transliterate(text='好', language='yue', transliteration_name='jyutping')
        self.assertEqual(result.service, Service.MandarinCantonese)
        self.assertEqual(result.text, 'hóu')
        result = self.clt.transliterate(text='好', language='yue', transliteration_name='tone numbers')
        self.assertEqual(result.text, 'hou2')

    def test_transliterate_hides_secrets(self):
        for option in self.clt.list_transliterations(service='EasyPronunciation'):
            self.assertNotIn('api_key', option.key)

    # llm
    # ===

    def test_llm(self):
        # pytest tests/test_cltai.py -k test_llm
        result = self.clt.llm(LlmRequest(prompt='What is the French word for "apple"? Answer with the word only, lowercase, no article.'))
        self.assertEqual(result.service, Service.OpenAI)
        self.assertEqual(sanitize(result.text), 'pomme')
        with self.assertRaisesRegex(CltAIError, 'model'):
            self.clt.validate_llm(prompt='hi', options={'model': 'not-a-model'})


class TestCltAIAgent(unittest.TestCase):
    """CLT-AI Agent with a real OpenAI model"""
    @classmethod
    def setUpClass(cls):
        manager = cloudlanguagetools.servicemanager.ServiceManager(cloudlanguagetools.encryption.load_configuration())
        cls.clt = create_client(CltAPIVersion.v1, manager=manager)
        cls.agent = cloudlanguagetools.cltai.agent.CltAIAgent(cls.clt)

    def test_codegen_pinyin(self):
        # pytest tests/test_cltai.py -k test_codegen_pinyin
        transformation = self.agent.generate_transformation('generate pinyin for the Chinese field',
            sample_row={'Chinese': '你好', 'Pinyin': '', 'English': 'hello'})
        self.assertEqual(transformation.output_fields, ['Pinyin'])
        self.assertEqual(transformation.input_fields, ['Chinese'])
        results = transformation.run_rows(self.clt, [{'Chinese': '成本很低', 'Pinyin': '', 'English': ''}, {'Chinese': '', 'Pinyin': '', 'English': ''}],
            stop_on_error=True)
        self.assertEqual(results[0]['Pinyin'], 'chéngběn hěn dī')
        self.assertNotIn('Pinyin', results[1])

    def test_codegen_japanese_audio(self):
        # pytest tests/test_cltai.py -k test_codegen_japanese_audio
        transformation = self.agent.generate_transformation(
            'generate Japanese audio with female voice for the Kanji field, output to the Sound field',
            sample_row={'Kanji': '猫', 'Sound': ''})
        output = transformation.run(self.clt, {'Kanji': '犬', 'Sound': ''})
        self.assertIsInstance(output['Sound'], SoundResult)
        self.assertEqual(output['Sound'].service, Service.Azure)
        # the voice is pinned in the code, results are repeatable
        output_2 = transformation.run(self.clt, {'Kanji': '鳥', 'Sound': ''})
        self.assertEqual(output['Sound'].voice_key, output_2['Sound'].voice_key)

    def test_codegen_ask_user(self):
        # pytest tests/test_cltai.py -k test_codegen_ask_user
        questions = []
        def ask_user(question):
            questions.append(question)
            return 'the source column is "Term" (French), write the translation to "Meaning"'
        transformation = self.agent.generate_transformation('add the english translation', available_fields=['Term', 'Notes', 'Meaning'],
            ask_user=ask_user)
        self.assertEqual(transformation.input_fields, ['Term'])
        self.assertEqual(transformation.output_fields, ['Meaning'])
        output = transformation.run(self.clt, {'Term': 'pomme', 'Notes': '', 'Meaning': ''})
        self.assertIn('apple', output['Meaning'].lower())

    def test_instant_standing_instructions(self):
        # pytest tests/test_cltai.py -k test_instant_standing_instructions
        response = self.agent.run_instant('成本很低',
            standing_instructions='if I give you chinese text, translate it to english, give me the pinyin, and generate audio')
        self.assertEqual(len(response.sounds), 1)
        self.assertTrue(os.path.isfile(response.sounds[0].audio_path))
        self.assertIn('chéngběn', response.text)
        self.assertIn('cost', response.text.lower())
