import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import google.cloud.texttospeech
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.google


class MockVoiceData:
    def __init__(self, name, language_code='en-US', ssml_gender=google.cloud.texttospeech.SsmlVoiceGender.FEMALE):
        self.name = name
        self.language_codes = [language_code]
        self.ssml_gender = ssml_gender


class TestGoogleVoicePitchSupport(unittest.TestCase):

    def test_neural2_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Neural2-A'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_news_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-News-K'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_wavenet_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Wavenet-A'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_standard_supports_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Standard-A'))
        self.assertTrue(voice.supports_pitch())
        self.assertIn('pitch', voice.get_options())

    def test_chirp_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Chirp3-HD-Leda'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())

    def test_chirp_variant_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('ar-XA-Chirp3-HD-Leda'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())

    def test_studio_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Studio-O'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())

    def test_journey_no_pitch(self):
        voice = cloudlanguagetools.google.GoogleVoice(MockVoiceData('en-US-Journey-F'))
        self.assertFalse(voice.supports_pitch())
        self.assertNotIn('pitch', voice.get_options())


if __name__ == '__main__':
    unittest.main()
