import json
import requests
import tempfile
import logging
import os
import base64

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors


def get_audio_language_enum(language_iso, country_iso):
    cereproc_audio_id_map = {
        'ro_ro': 'ro_RO',
        'no_NO': 'nb_NO'
    }
    language_enum_name = f'{language_iso}_{country_iso}'
    if language_enum_name in cereproc_audio_id_map:
        language_enum_name = cereproc_audio_id_map[language_enum_name]
    return cloudlanguagetools.languages.AudioLanguage[language_enum_name]

class CereProcVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        self.service = cloudlanguagetools.constants.Service.CereProc
        self.audio_language = get_audio_language_enum(voice_data['language_iso'], voice_data['country_iso'])
        self.name = voice_data['name']
        self.region = voice_data['region']
        self.accent = voice_data['accent']
        self.gender = cloudlanguagetools.constants.Gender[voice_data['gender'].capitalize()]

    def get_voice_shortname(self):
        return f'{self.name} ({self.accent})'

    def get_voice_key(self):
        return {
            'name': self.name
        }

    def get_options(self):
        return {}

class CereProcService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        self.username = config['username']
        self.password = config['password']
    

    def get_access_token(self):
        combined = f'{self.username}:{self.password}'
        auth_string = base64.b64encode(combined.encode('utf-8')).decode('utf-8')
        headers = {'authorization': f'Basic {auth_string}'}

        auth_url = 'https://api.cerevoice.com/v2/auth'
        response = requests.get(auth_url, headers=headers, 
            timeout=cloudlanguagetools.constants.RequestTimeout)

        access_token = response.json()['access_token']        
        return access_token
    
    def get_auth_headers(self):
        headers={'Authorization': f'Bearer {self.get_access_token()}'}
        return headers

    def get_translation_language_list(self):
        return []

    def list_voices(self):
        list_voices_url = 'https://api.cerevoice.com/v2/voices'
        
        response = requests.get(list_voices_url, headers=self.get_auth_headers(), 
            timeout=(cloudlanguagetools.constants.ReadTimeout, cloudlanguagetools.constants.RequestTimeout))
        data = response.json()
        return data['voices']

    def get_tts_voice_list(self):
        result = []

        voice_list = self.list_voices()
        for voice in voice_list:
            try:
                result.append(CereProcVoice(voice))
            except KeyError:
                logging.error(f'could not process voice for {voice}', exc_info=True)

        return result

    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        voice_name = voice_key['name']
        url = f'https://api.cerevoice.com/v2/speak?voice={voice_name}&audio_format=mp3'


        ssml_text = f"""<?xml version="1.0" encoding="UTF-8"?>
<speak xmlns="http://www.w3.org/2001/10/synthesis">{text}</speak>""".encode(encoding='utf-8')

        # logging.debug(f'querying url: {url}')
        response = requests.post(url, data=ssml_text, headers=self.get_auth_headers(), timeout=cloudlanguagetools.constants.RequestTimeout)

        if response.status_code == 200:
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file

        # otherwise, an error occured
        error_message = f"Status code: {response.status_code} reason: {response.reason} voice: [{voice_name}]]"
        raise cloudlanguagetools.errors.RequestError(error_message)


    def get_transliteration_language_list(self):
        return []
