import json
import requests
import tempfile
import logging
import pprint

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)

def get_translation_language_enum(language_id):
    # print(f'language_id: {language_id}')
    watson_language_id_map = {
        'fr-CA': 'fr_ca',
        'id': 'id_',
        'pt': 'pt_pt',
        'sr': 'sr_cyrl',
        'zh':'zh_cn',
        'zh-TW': 'zh_tw'

    }
    if language_id in watson_language_id_map:
        language_id = watson_language_id_map[language_id]
    return cloudlanguagetools.languages.Language[language_id]

def get_audio_language_enum(voice_language):
    watson_audio_id_map = {
        'ar-MS': 'ar_XA'
    }
    language_enum_name = voice_language.replace('-', '_')
    if voice_language in watson_audio_id_map:
        language_enum_name = watson_audio_id_map[voice_language]
    return cloudlanguagetools.languages.AudioLanguage[language_enum_name]

class WatsonTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.Watson
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id

class WatsonVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        self.service = cloudlanguagetools.constants.Service.Watson
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.audio_language = get_audio_language_enum(voice_data['language'])
        self.name = voice_data['name']
        self.description = voice_data['description']
        self.description = voice_data['description']
        self.gender = cloudlanguagetools.constants.Gender[voice_data['gender'].capitalize()]


    def get_voice_key(self):
        return {
            'name': self.name
        }

    def get_voice_shortname(self):
        is_dnn = ''
        if 'Dnn' in self.description:
            is_dnn = ' (Dnn)'
        return self.description.split(':')[0] + is_dnn

    def get_options(self):
        return {
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.ogg_opus.name,
                    cloudlanguagetools.options.AudioFormat.ogg_vorbis.name,
                    cloudlanguagetools.options.AudioFormat.wav.name
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }
        }

class WatsonService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        self.translator_key = config['translator_api_key']
        self.translator_url = config['translator_url']
        self.speech_key = config['speech_api_key']
        self.speech_url = config['speech_url']
    
    def get_tts_voice_list(self):
        return []

    def get_translation_languages(self):
        response = requests.get(self.translator_url + '/v3/languages?version=2018-05-01', auth=('apikey', self.translator_key), timeout=cloudlanguagetools.constants.RequestTimeout)
        return response.json()

    def get_translation_language_list(self):
        # 2025/04: watson translation API has been decommisioned
        return []

    def list_voices(self):
        response = requests.get(self.speech_url + '/v1/voices', auth=('apikey', self.speech_key), timeout=cloudlanguagetools.constants.RequestTimeout)
        data = response.json()
        logger.debug(f'voices: {data}')
        return data['voices']

    def get_tts_voice_list(self):
        result = []

        voice_list = self.list_voices()
        for voice in voice_list:
            try:
                result.append(WatsonVoice(voice))
                logger.debug(f'added voice {voice}')
            except KeyError:
                logging.error(f'could not process voice for {voice}', exc_info=True)

        return result

    def get_tts_audio(self, text, voice_key, options):
        response_format_parameter, audio_format = self.get_request_audio_format({
            AudioFormat.mp3: 'audio/mp3',
            AudioFormat.ogg_opus: 'audio/ogg;codecs=opus',
            AudioFormat.ogg_vorbis: 'audio/ogg;codecs=vorbis',
            AudioFormat.wav: 'audio/wav;rate=48000'
        }, options, AudioFormat.mp3)

        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        base_url = self.speech_url
        url_path = '/v1/synthesize'
        voice_name = voice_key["name"]
        constructed_url = base_url + url_path + f'?voice={voice_name}'
        headers = {
            'Content-Type': 'application/json',
            'Accept': response_format_parameter
        }

        data = {
            'text': text
        }

        response = requests.post(constructed_url, data=json.dumps(data), auth=('apikey', self.speech_key), headers=headers, timeout=cloudlanguagetools.constants.RequestTimeout)

        if response.status_code == 200:
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file

        # otherwise, an error occured
        error_message = f"Status code: {response.status_code} reason: {response.reason} voice: [{voice_name}]]"
        raise cloudlanguagetools.errors.RequestError(error_message)


    def get_transliteration_language_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):
        body = {
            'text': text,
            'source': from_language_key,
            'target': to_language_key
        }
        response = requests.post(self.translator_url + '/v3/translate?version=2018-05-01', auth=('apikey', self.translator_key), json=body, timeout=cloudlanguagetools.constants.RequestTimeout)

        if response.status_code == 200:
            # {'translations': [{'translation': 'Le coût est très bas.'}], 'word_count': 2, 'character_count': 4}
            data = response.json()
            return data['translations'][0]['translation']

        error_message = error_message = f'Watson: could not translate text [{text}] from {from_language_key} to {to_language_key} ({response.json()})'
        raise cloudlanguagetools.errors.RequestError(error_message)