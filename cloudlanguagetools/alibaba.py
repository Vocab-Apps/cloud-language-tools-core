import json
import requests
import time
import datetime
import uuid
import urllib
import hmac
import base64
import logging
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.errors
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)

ALIBABA_VOICE_SPEED_DEFAULT = 0
ALIBABA_VOICE_PITCH_DEFAULT = 0


class AlibabaService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.access_token = None
        
    def configure(self, config):
        self.access_key_id = config['access_key_id']
        self.access_key_secret = config['access_key_secret']
        self.app_key = config['app_key']

    def refresh_token(self):
        logger.info("refreshing token")
        params = {
            "AccessKeyId": self.access_key_id,
            "Action": "CreateToken",
            "Version": "2019-07-17",
            "Format": "JSON",
            "RegionId": "ap-southeast-1",
            "Timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": str(uuid.uuid4())
        }

        # sort by keys alphabetically
        params = dict(sorted(params.items()))
        # timestamp needs to be double-quoted by the end
        params["Timestamp"] = urllib.parse.quote(params["Timestamp"], safe='')
        
        # urlencode with noop lambda for no quoting - we will quote later
        params_str = urllib.parse.urlencode(params, quote_via=lambda a, b, c, d: a)
        
        # this is always /, as we always hit the path / on the API
        url_encoded = urllib.parse.quote("/", safe='')
        str_to_sign = f"GET&{url_encoded}&{urllib.parse.quote(params_str, safe='')}"
        str_to_sign = str_to_sign.encode("utf-8")
        
        key = self.access_key_secret + "&"
        key = key.encode("utf-8")
        
        # calculate HMAC-SHA1 digest and convert to base64
        dig = hmac.new(key, str_to_sign, "sha1").digest()
        dig = base64.standard_b64encode(dig).decode("utf-8")
        
        # signature also needs to be quoted
        signature = urllib.parse.quote(dig, safe='')
        params_str = f"Signature={signature}&{params_str}"
        
        response = requests.get(f"http://nlsmeta.ap-southeast-1.aliyuncs.com/?{params_str}")
        
        if response.status_code != 200:
            logger.warning(f"Token request failed: {response.text}")
            raise cloudlanguagetools.errors.RequestError("Token request failed", None, response.text)
            
        data = response.json()
        self.access_token = data["Token"]
        logger.info(f"Got access token: {self.access_token}")

    def get_tts_audio(self, text, voice_key, options):
        if not self.access_token or self.access_token["ExpireTime"] <= int(time.time()):
            self.refresh_token()

        speed = int(options.get('speed', ALIBABA_VOICE_SPEED_DEFAULT))
        pitch = int(options.get('pitch', ALIBABA_VOICE_PITCH_DEFAULT))
        voice = voice_key['name']

        params = {
            "format": "mp3",
            "appkey": self.app_key,
            "speech_rate": speed,
            "pitch_rate": pitch,
            "text": text,
            "token": self.access_token["Id"],
            "voice": voice
        }

        response = requests.get(
            "https://nls-gateway-ap-southeast-1.aliyuncs.com/stream/v1/tts",
            params=params,
            timeout=cloudlanguagetools.constants.RequestTimeout
        )

        if response.status_code != 200:
            data = response.json()
            error_message = data.get('message', str(data))
            logger.warning(error_message)
            raise cloudlanguagetools.errors.RequestError(text, voice, error_message)

        if response.headers['Content-Type'] != 'audio/mpeg':
            logger.warning(f'Unexpected response type. Response as text: {response.text}')
            raise cloudlanguagetools.errors.RequestError(
                text, voice,
                f'Got bad content type in response: {response.headers["Content-Type"]}'
            )

        return response.content

    def get_tts_voice_list(self):
        # returns list of TtsVoice
        return []

    def get_tts_voice_list_v3(self) -> List[cloudlanguagetools.ttsvoice.TtsVoice_v3]:
        result = []

        # Standard voices for all scenarios
        result.extend([
            cloudlanguagetools.ttsvoice.TtsVoice_v3(
                name='Xiaoyun',
                voice_key={'name': 'xiaoyun'},
                options={
                    'speed': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'pitch': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'volume': {'type': 'number_int', 'min': 0, 'max': 100, 'default': 50},
                    'audio_format': {'type': 'list', 'values': ['pcm', 'wav', 'mp3'], 'default': 'pcm'}
                },
                service=cloudlanguagetools.constants.Service.Alibaba,
                gender=cloudlanguagetools.constants.Gender.Female,
                audio_languages=[cloudlanguagetools.languages.AudioLanguage.zh_CN],
                service_fee=cloudlanguagetools.constants.ServiceFee.paid
            ),
            # Add more standard voices
            cloudlanguagetools.ttsvoice.TtsVoice_v3(
                name='Xiaogang',
                voice_key={'name': 'xiaogang'},
                options={
                    'speed': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'pitch': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'volume': {'type': 'number_int', 'min': 0, 'max': 100, 'default': 50},
                    'audio_format': {'type': 'list', 'values': ['pcm', 'wav', 'mp3'], 'default': 'pcm'}
                },
                service=cloudlanguagetools.constants.Service.Alibaba,
                gender=cloudlanguagetools.constants.Gender.Male,
                audio_languages=[cloudlanguagetools.languages.AudioLanguage.zh_CN],
                service_fee=cloudlanguagetools.constants.ServiceFee.paid
            ),
            # English voices
            cloudlanguagetools.ttsvoice.TtsVoice_v3(
                name='Harry (British)',
                voice_key={'name': 'harry'},
                options={
                    'speed': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'pitch': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'volume': {'type': 'number_int', 'min': 0, 'max': 100, 'default': 50},
                    'audio_format': {'type': 'list', 'values': ['pcm', 'wav', 'mp3'], 'default': 'pcm'}
                },
                service=cloudlanguagetools.constants.Service.Alibaba,
                gender=cloudlanguagetools.constants.Gender.Male,
                audio_languages=[cloudlanguagetools.languages.AudioLanguage.en_GB],
                service_fee=cloudlanguagetools.constants.ServiceFee.paid
            ),
            # Dialect voices
            cloudlanguagetools.ttsvoice.TtsVoice_v3(
                name='Shanshan (Cantonese)',
                voice_key={'name': 'shanshan'},
                options={
                    'speed': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'pitch': {'type': 'number_int', 'min': -500, 'max': 500, 'default': 0},
                    'volume': {'type': 'number_int', 'min': 0, 'max': 100, 'default': 50},
                    'audio_format': {'type': 'list', 'values': ['pcm', 'wav', 'mp3'], 'default': 'pcm'}
                },
                service=cloudlanguagetools.constants.Service.Alibaba,
                gender=cloudlanguagetools.constants.Gender.Female,
                audio_languages=[cloudlanguagetools.languages.AudioLanguage.zh_HK],
                service_fee=cloudlanguagetools.constants.ServiceFee.paid
            )
        ])
        
        return result
