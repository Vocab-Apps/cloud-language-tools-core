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

GEMINI_VOICES = [
    ('Zephyr', 'Bright', cloudlanguagetools.constants.Gender.Any),
    ('Puck', 'Upbeat', cloudlanguagetools.constants.Gender.Any),
    ('Charon', 'Informative', cloudlanguagetools.constants.Gender.Any),
    ('Kore', 'Firm', cloudlanguagetools.constants.Gender.Any),
    ('Fenrir', 'Excitable', cloudlanguagetools.constants.Gender.Any),
    ('Leda', 'Youthful', cloudlanguagetools.constants.Gender.Any),
    ('Orus', 'Firm', cloudlanguagetools.constants.Gender.Any),
    ('Aoede', 'Breezy', cloudlanguagetools.constants.Gender.Any),
    ('Callirrhoe', 'Easy-going', cloudlanguagetools.constants.Gender.Any),
    ('Autonoe', 'Bright', cloudlanguagetools.constants.Gender.Any),
    ('Enceladus', 'Breathy', cloudlanguagetools.constants.Gender.Any),
    ('Iapetus', 'Clear', cloudlanguagetools.constants.Gender.Any),
    ('Umbriel', 'Easy-going', cloudlanguagetools.constants.Gender.Any),
    ('Algieba', 'Smooth', cloudlanguagetools.constants.Gender.Any),
    ('Despina', 'Smooth', cloudlanguagetools.constants.Gender.Any),
    ('Erinome', 'Clear', cloudlanguagetools.constants.Gender.Any),
    ('Algenib', 'Gravelly', cloudlanguagetools.constants.Gender.Any),
    ('Rasalgethi', 'Informative', cloudlanguagetools.constants.Gender.Any),
    ('Laomedeia', 'Upbeat', cloudlanguagetools.constants.Gender.Any),
    ('Achernar', 'Soft', cloudlanguagetools.constants.Gender.Any),
    ('Alnilam', 'Firm', cloudlanguagetools.constants.Gender.Any),
    ('Schedar', 'Even', cloudlanguagetools.constants.Gender.Any),
    ('Gacrux', 'Mature', cloudlanguagetools.constants.Gender.Any),
    ('Pulcherrima', 'Forward', cloudlanguagetools.constants.Gender.Any),
    ('Achird', 'Friendly', cloudlanguagetools.constants.Gender.Any),
    ('Zubenelgenubi', 'Casual', cloudlanguagetools.constants.Gender.Any),
    ('Vindemiatrix', 'Gentle', cloudlanguagetools.constants.Gender.Any),
    ('Sadachbia', 'Lively', cloudlanguagetools.constants.Gender.Any),
    ('Sadaltager', 'Knowledgeable', cloudlanguagetools.constants.Gender.Any),
    ('Sulafat', 'Warm', cloudlanguagetools.constants.Gender.Any),
]

def get_tts_voice_list():
    """Legacy method for backwards compatibility"""
    return []

def build_tts_voice_v3(voice_name, description, gender):
    """Build a TtsVoice_v3 instance for a Gemini voice"""
    return cloudlanguagetools.ttsvoice.TtsVoice_v3(
        name=f'{voice_name} ({description})',
        voice_key={
            'name': voice_name
        },
        options=VOICE_OPTIONS,
        service=cloudlanguagetools.constants.Service.Gemini,
        gender=gender,
        audio_languages=TTS_SUPPORTED_LANGUAGES,
        service_fee=cloudlanguagetools.constants.ServiceFee.paid
    )

class GeminiService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.service = cloudlanguagetools.constants.Service.Gemini
        self.api_key_required = True

    def configure(self, config):
        self.config = config
        self.api_key = config.get('api_key', None)
        logger.debug(f'Configuring Gemini service with api_key: {self.api_key[:20] if self.api_key else None}...')
        if self.api_key is None:
            raise cloudlanguagetools.errors.AuthenticationError('api_key not set')

    def get_tts_voice_list(self):
        return get_tts_voice_list()

    def get_tts_voice_list_v3(self):
        """Return list of TtsVoice_v3 instances for all Gemini voices"""
        result = []
        for voice_name, description, gender in GEMINI_VOICES:
            voice = build_tts_voice_v3(voice_name, description, gender)
            result.append(voice)
        return result

    def get_tts_audio(self, text, voice_key, options):
        """Generate TTS audio using Google Gemini API"""
        
        # Extract voice name from voice_key dict
        if isinstance(voice_key, dict) and 'name' in voice_key:
            voice_name = voice_key['name']
        else:
            raise cloudlanguagetools.errors.RequestError(f'Invalid voice key format: {voice_key}')
        
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
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice_name
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
            logger.debug(f'Making Gemini TTS request to: {url}')
            logger.debug(f'Request payload: {json.dumps(payload, indent=2)}')
            
            response = self.post_request(url, 
                                       json=payload, 
                                       headers=headers, 
                                       params=params)
            
            logger.debug(f'Response status: {response.status_code}')
            
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
                # More detailed error with actual response structure
                logger.error(f'Full response: {json.dumps(response_data, indent=2)}')
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