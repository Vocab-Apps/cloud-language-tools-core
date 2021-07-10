import json
import requests
import urllib
import hashlib
import tempfile
import uuid
import operator
import pydub

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

NAVER_VOICE_SPEED_DEFAULT = 0
NAVER_VOICE_PITCH_DEFAULT = 0

class VocalWareVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, name, gender, language_id, voice_id, engine_id):
        self.service = cloudlanguagetools.constants.Service.VocalWare
        self.audio_language = audio_language
        self.name = name
        self.gender = gender
        self.language_id = language_id
        self.voice_id = voice_id
        self.engine_id = engine_id

    def get_voice_key(self):
        return {
            'language_id': self.language_id,
            'voice_id': self.voice_id,
            'engine_id': self.engine_id
        }

    def get_voice_shortname(self):
        return f'{self.name}'

    def get_options(self):
        return {}


class VocalWareService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, secret_phrase, account_id, api_id):
        self.secret_phrase = secret_phrase
        self.account_id = account_id
        self.api_id = api_id

    def get_translation(self, text, from_language_key, to_language_key):
        raise cloudlanguagetools.errors.RequestError('not supported')

    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        urlencoded_text = urllib.parse.unquote_plus(text)

        checksum_input = f"""{voice_key['engine_id']}{voice_key['language_id']}{voice_key['voice_id']}{urlencoded_text}{self.secret_phrase}"""
        checksum = hashlib.md5(checksum_input.encode('utf-8')).hexdigest()

        url_parameters = f"""EID={voice_key['engine_id']}&LID={voice_key['language_id']}&VID={voice_key['voice_id']}&TXT={urlencoded_text}&ACC={self.account_id}&API={self.api_id}&CS={checksum}"""
        url = f"""http://www.vocalware.com/tts/gen.php?{url_parameters}"""


        # alternate_data = 'speaker=clara&text=vehicle&volume=0&speed=0&pitch=0&format=mp3'
        response = requests.get(url, timeout=cloudlanguagetools.constants.RequestTimeout)
        if response.status_code == 200:
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file

        response_data = response.content
        error_message = f'Status code: {response.status_code}: {response_data}'
        raise cloudlanguagetools.errors.RequestError(error_message)

    def get_tts_voice_list(self):
        # returns list of TtSVoice
        return [
            VocalWareVoice(cloudlanguagetools.constants.AudioLanguage.en_US, 'Dave (US)', cloudlanguagetools.constants.Gender.Male, 1, 2, 2),            
        ]

    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   