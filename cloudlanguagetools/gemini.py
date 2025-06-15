import json
import requests
import tempfile
import base64
import logging
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.errors
from cloudlanguagetools.languages import AudioLanguage
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gemini-2.5-flash-preview-tts'
DEFAULT_VOICE = 'Kore'

VOICE_OPTIONS = {
    'model': {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': [
            'gemini-2.5-flash-preview-tts',
            'gemini-2.5-pro-preview-tts'
        ],
        'default': DEFAULT_MODEL
    },
    'voice_name': {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': [
            'Kore',
            'Zephyr',
            'Puck',
            'Charon'
        ],
        'default': DEFAULT_VOICE
    },
    cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': [
            cloudlanguagetools.options.AudioFormat.wav.name
        ],
        'default': cloudlanguagetools.options.AudioFormat.wav.name
    }
}

# Gemini TTS supports 24+ languages
TTS_SUPPORTED_LANGUAGES = [
    AudioLanguage.en_US,
    AudioLanguage.fr_FR,
    AudioLanguage.de_DE,
    AudioLanguage.es_ES,
    AudioLanguage.it_IT,
    AudioLanguage.pt_BR,
    AudioLanguage.ru_RU,
    AudioLanguage.ja_JP,
    AudioLanguage.ko_KR,
    AudioLanguage.zh_CN,
    AudioLanguage.hi_IN,
    AudioLanguage.ar_XA,
    AudioLanguage.nl_NL,
    AudioLanguage.pl_PL,
    AudioLanguage.sv_SE,
    AudioLanguage.da_DK,
    AudioLanguage.nb_NO,
    AudioLanguage.fi_FI,
    AudioLanguage.tr_TR,
    AudioLanguage.th_TH,
    AudioLanguage.vi_VN,
    AudioLanguage.uk_UA,
    AudioLanguage.cs_CZ,
    AudioLanguage.hu_HU
]

class GeminiVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_name, audio_language):
        self.service = cloudlanguagetools.constants.Service.Gemini
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.audio_language = audio_language
        self.name = voice_name
        self.gender = cloudlanguagetools.constants.Gender.Any
        
    def get_voice_key(self):
        return f'gemini_tts_{self.name.lower()}_{self.audio_language.name}'
        
    def get_voice_shortname(self):
        return self.name
        
    def get_options(self):
        return VOICE_OPTIONS

def get_tts_voice_list():
    voices = []
    for language in TTS_SUPPORTED_LANGUAGES:
        for voice_name in VOICE_OPTIONS['voice_name']['values']:
            voice = GeminiVoice(voice_name, language)
            voices.append(voice)
    return voices

class GeminiService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.service = cloudlanguagetools.constants.Service.Gemini
        self.api_key_required = True

    def configure(self, config):
        self.config = config
        self.api_key = config.get('api_key', None)
        if self.api_key is None:
            raise cloudlanguagetools.errors.AuthenticationError('api_key not set')

    def get_tts_voice_list(self):
        return get_tts_voice_list()

    def get_tts_audio(self, text, voice_key, options):
        """Generate TTS audio using Google Gemini API"""
        
        # Parse voice key to extract voice name and language
        voice_parts = voice_key.split('_')
        if len(voice_parts) < 4:
            raise cloudlanguagetools.errors.RequestError(f'Invalid voice key format: {voice_key}')
        
        voice_name = voice_parts[2].capitalize()
        
        # Get model and format from options
        model = options.get('model', DEFAULT_MODEL)
        
        # Prepare request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": text
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": voice_name
                        }
                    }
                }
            }
        }

        # Make API request
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        headers = {
            'Content-Type': 'application/json'
        }
        params = {
            'key': self.api_key
        }

        try:
            response = self.post_request(url, 
                                       json=payload, 
                                       headers=headers, 
                                       params=params)
            
            if response.status_code >= 400:
                error_msg = f'Gemini TTS request failed with status {response.status_code}: {response.text}'
                logger.error(error_msg)
                raise cloudlanguagetools.errors.RequestError(error_msg)

            response_data = response.json()
            
            # Extract audio data
            if 'candidates' not in response_data or len(response_data['candidates']) == 0:
                raise cloudlanguagetools.errors.RequestError('No audio candidates in response')
            
            candidate = response_data['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                raise cloudlanguagetools.errors.RequestError('No content parts in response')
            
            # Find the audio part
            audio_part = None
            for part in candidate['content']['parts']:
                if 'inline_data' in part and part['inline_data'].get('mime_type', '').startswith('audio/'):
                    audio_part = part
                    break
            
            if audio_part is None:
                raise cloudlanguagetools.errors.RequestError('No audio data found in response')
            
            # Decode base64 audio data
            audio_data = base64.b64decode(audio_part['inline_data']['data'])
            
            # Create temporary file
            output_temp_file = tempfile.NamedTemporaryFile(prefix='clt_gemini_audio_', suffix='.wav')
            with open(output_temp_file.name, 'wb') as f:
                f.write(audio_data)
            
            return output_temp_file
            
        except requests.exceptions.Timeout:
            raise cloudlanguagetools.errors.TimeoutError('Timeout while retrieving Gemini TTS audio')
        except requests.exceptions.RequestException as e:
            error_msg = f'Request error while retrieving Gemini TTS audio: {str(e)}'
            logger.exception(error_msg)
            raise cloudlanguagetools.errors.RequestError(error_msg)
        except Exception as e:
            error_msg = f'Unexpected error while retrieving Gemini TTS audio: {str(e)}'
            logger.exception(error_msg)
            raise cloudlanguagetools.errors.RequestError(error_msg)