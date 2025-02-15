import sys
import os
import re
import magic
import pydub
import tempfile
import openai

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.options
import cloudlanguagetools.constants

def speech_to_text(manager, audio_temp_file, language, audio_format=cloudlanguagetools.options.AudioFormat.mp3):
    result = manager.services[cloudlanguagetools.constants.Service.Azure].speech_to_text(audio_temp_file.name, audio_format, language=language)
    return result

def convert_to_wav(audio_temp_file, audio_format) -> tempfile.NamedTemporaryFile:
    if audio_format == cloudlanguagetools.options.AudioFormat.mp3:
        sound = pydub.AudioSegment.from_mp3(audio_temp_file.name)
    elif audio_format == cloudlanguagetools.options.AudioFormat.ogg_opus:
        sound = pydub.AudioSegment.from_ogg(audio_temp_file.name)
    elif audio_format == cloudlanguagetools.options.AudioFormat.ogg_vorbis:
        sound = pydub.AudioSegment.from_ogg(audio_temp_file.name)

    # convert to wav
    wav_tempfile = tempfile.NamedTemporaryFile(prefix='clt_speech_recognition_', suffix='.wav')
    # https://github.com/Azure-Samples/cognitive-services-speech-sdk/issues/756
    # this indicates that converting to 16khz helps avoid this issue:
    # No speech could be recognized: NoMatchDetails(reason=NoMatchReason.InitialSilenceTimeout)
    sound = sound.set_frame_rate(16000)
    sound.export(wav_tempfile.name, format="wav", parameters=["-ar", "16000"])

    return wav_tempfile    

def speech_to_text_azure_wav(manager, audio_temp_file, language, audio_format):
    wav_tempfile = convert_to_wav(audio_temp_file, audio_format)

    result = manager.services[cloudlanguagetools.constants.Service.Azure].speech_to_text(
        wav_tempfile.name, 
        cloudlanguagetools.options.AudioFormat.wav, 
        language=language)
    return result    

def speech_to_text_openai(manager, audio_temp_file, audio_format):
    wav_tempfile = convert_to_wav(audio_temp_file, audio_format)
    client = manager.services[cloudlanguagetools.constants.Service.OpenAI].client
    # client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    with open(wav_tempfile.name, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcript.text


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