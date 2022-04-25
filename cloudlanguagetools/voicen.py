import json
import requests
import tempfile
import logging

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

class VoicenVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_id, audio_language, gender, name):
        self.service = cloudlanguagetools.constants.Service.Voicen
        self.audio_language = audio_language
        self.name = name
        self.gender = gender
        self.voice_id = voice_id


    def get_voice_key(self):
        return {
            'voice_id': self.voice_id,
            'lang': self.audio_language.lang.name
        }

    def get_voice_shortname(self):
        return f'{self.name}'

    def get_options(self):
        return {}

class VoicenService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, api_key):
        self.api_key = api_key

    def get_translation_language_list(self):
        return []

    def get_tts_voice_list(self):
        result = [
            VoicenVoice('325640', cloudlanguagetools.languages.AudioLanguage.az_AZ, cloudlanguagetools.constants.Gender.Female, 'Aytac'),
            VoicenVoice('325641', cloudlanguagetools.languages.AudioLanguage.az_AZ, cloudlanguagetools.constants.Gender.Female, 'Aynur'),
            VoicenVoice('325642', cloudlanguagetools.languages.AudioLanguage.az_AZ, cloudlanguagetools.constants.Gender.Male, 'Ramin'),
            VoicenVoice('325643', cloudlanguagetools.languages.AudioLanguage.az_AZ, cloudlanguagetools.constants.Gender.Male, 'Elchin'),
            VoicenVoice('325648', cloudlanguagetools.languages.AudioLanguage.az_AZ, cloudlanguagetools.constants.Gender.Male, 'Kamil'),
            VoicenVoice('325647', cloudlanguagetools.languages.AudioLanguage.tr_TR, cloudlanguagetools.constants.Gender.Female, 'Zeynep'),
            VoicenVoice('325646', cloudlanguagetools.languages.AudioLanguage.tr_TR, cloudlanguagetools.constants.Gender.Male, 'Mesut'),
            VoicenVoice('325644', cloudlanguagetools.languages.AudioLanguage.tr_TR, cloudlanguagetools.constants.Gender.Female, 'Sibel'),
            VoicenVoice('325645', cloudlanguagetools.languages.AudioLanguage.ru_RU, cloudlanguagetools.constants.Gender.Female, 'Anna'),
        ]
        return result

    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        request_url = 'https://tts.voicen.com/api/v1/jobs/text/'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            'text': text,
            'lang': voice_key['lang'],
            'voice_id': voice_key['voice_id']
        }

        response = requests.post(request_url, data=data, headers=headers, timeout=cloudlanguagetools.constants.RequestTimeout)
        print(response.content)
        return

        if response.status_code == 200:
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file

        # otherwise, an error occured
        error_message = f"Status code: {response.status_code} reason: {response.reason} voice: [{voice_name}]]"
        raise cloudlanguagetools.errors.RequestError(error_message)


    def get_transliteration_language_list(self):
        return []
