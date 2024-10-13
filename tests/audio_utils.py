import sys
import os
import re
import magic

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.options
import cloudlanguagetools.constants

def speech_to_text(manager, audio_temp_file, language, audio_format=cloudlanguagetools.options.AudioFormat.mp3):
    result = manager.services[cloudlanguagetools.constants.Service.Azure].speech_to_text(audio_temp_file.name, audio_format, language=language)
    return result

def sanitize_recognized_text(recognized_text):
    recognized_text = re.sub('<[^<]+?>', '', recognized_text)
    result_text = recognized_text.replace('.', '').\
        replace('。', '').\
        replace('?', '').\
        replace('？', '').\
        replace('您', '你').\
        replace('&', 'and').\
        replace(',', '').\
        replace(':', '').lower()
    return result_text

def is_mp3_format(filename):
    mime_type = magic.from_file(filename)
    expected_mime_type_str = 'MPEG ADTS, layer III'    
    return expected_mime_type_str in mime_type

def is_ogg_opus_format(filename):
    mime_type = magic.from_file(filename)
    expected_mime_type_str = 'Ogg data, Opus audio,'
    return expected_mime_type_str in mime_type

def assert_is_wav_format(self, filename):
    mime_type = magic.from_file(filename)
    expected_mime_type_str = 'PCM'
    self.assertTrue(expected_mime_type_str in mime_type, f'checking for WAV format: expected [{expected_mime_type_str}] in mime type: [{mime_type}]')