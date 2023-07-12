import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.options
import cloudlanguagetools.constants

def speech_to_text(manager, audio_temp_file, language, audio_format=cloudlanguagetools.options.AudioFormat.mp3):
    result = manager.services[cloudlanguagetools.constants.Service.Azure].speech_to_text(audio_temp_file.name, audio_format, language=language)
    return result