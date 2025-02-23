import json
import requests
import time
import datetime
import uuid
import urllib
import hmac
import base64
import logging
import tempfile
import pprint
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.options
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.errors
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)

ALIBABA_VOICE_SPEED_DEFAULT = 0
ALIBABA_VOICE_PITCH_DEFAULT = 0

VOICE_OPTIONS = {
    'speed': {'type': 'number_int', 'min': -500, 'max': 500, 'default': ALIBABA_VOICE_SPEED_DEFAULT},
    'pitch': {'type': 'number_int', 'min': -500, 'max': 500, 'default': ALIBABA_VOICE_PITCH_DEFAULT},
    'volume': {'type': 'number_int', 'min': 0, 'max': 100, 'default': 50},
    cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': ['pcm', 'wav', 'mp3'],
        'default': 'mp3'
    }
}


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
        logger.debug(f'get_tts_audio, text: {text} voice_key: {voice_key}')
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

        logger.debug(f'response status code: {response.status_code} headers: {pprint.pformat(response.headers)} length of response: {len(response.content)}')

        if response.status_code != 200:
            data = response.json()
            error_message = f'could not retrieve audio using Alibaba: {response.content}'
            logger.error(error_message)
            raise cloudlanguagetools.errors.RequestError(text, voice, error_message)

        if response.headers['Content-Type'] != 'audio/mpeg':
            logger.error(f'Unexpected response type. Response as text: {response.text}')
            raise cloudlanguagetools.errors.RequestError(
                text, voice,
                f'Got bad content type in response: {response.headers["Content-Type"]}'
            )
        
        # Create a temporary file and write the audio content to it
        output_temp_file = tempfile.NamedTemporaryFile(prefix=f'cloudlanguage_tools_{self.__class__.__name__}_audio', suffix='.mp3')
        output_temp_filename = output_temp_file.name
        with open(output_temp_filename, 'wb') as audio:
            audio.write(response.content)        
        logger.debug(f'result temporary file name: {output_temp_file.name}')
        return output_temp_file

    def get_tts_voice_list(self):
        # returns list of TtsVoice
        return []

    def build_tts_voice_v3(self, name: str, voice_id: str, gender: cloudlanguagetools.constants.Gender, audio_languages: List[cloudlanguagetools.languages.AudioLanguage]):
        return cloudlanguagetools.ttsvoice.TtsVoice_v3(
            name=name,
            voice_key={'name': voice_id},
            options=VOICE_OPTIONS,
            service=cloudlanguagetools.constants.Service.Alibaba,
            gender=gender,
            audio_languages=audio_languages,
            service_fee=cloudlanguagetools.constants.ServiceFee.paid
        )

    def get_tts_voice_list_v3(self) -> List[cloudlanguagetools.ttsvoice.TtsVoice_v3]:
        result = []

        # Standard voices for all scenarios
        result.extend([
            # Standard Chinese voices
            self.build_tts_voice_v3('Xiaoyun (Standard)', 'Xiaoyun', 
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Xiaogang (Standard)', 'Xiaogang',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Ruoxi (Gentle)', 'Ruoxi',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Siqi (Gentle)', 'Siqi',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Sijia (Standard)', 'Sijia',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Sicheng (Standard)', 'Sicheng',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aiqi (Gentle)', 'Aiqi',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aijia (Standard)', 'Aijia',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aicheng (Standard)', 'Aicheng',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aida (Standard)', 'Aida',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3("Ning'er", 'Ninger',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Ruilin', 'Ruilin',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),

            # Customer service voices
            self.build_tts_voice_v3('Siyue (Gentle)', 'Siyue',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aiya (Harsh)', 'Aiya',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aixia (Amiable)', 'Aixia',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aimei (Sweet)', 'Aimei',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aiyu (Natural)', 'Aiyu',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aiyue (Gentle)', 'Aiyue',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aijing (Harsh)', 'Aijing',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Xiaomei (Sweet)', 'Xiaomei',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),

            # Regional accent voices
            self.build_tts_voice_v3('Aina (Zhejiang)', 'Aina',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Yina (Zhejiang)', 'Yina',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Sijing (Harsh)', 'Sijing',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),

            # Child voices
            self.build_tts_voice_v3('Sitong (Child)', 'Sitong',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Xiaobei (Little Girl)', 'Xiaobei',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Aitong (Child)', 'Aitong',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Aiwei (Little Girl)', 'Aiwei',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Aibao (Little Girl)', 'Aibao',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),

            # English voices
            self.build_tts_voice_v3('Harry (British)', 'Harry',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.en_GB]),
            self.build_tts_voice_v3('Abby (American)', 'Abby',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Andy (American)', 'Andy',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Eric (British)', 'Eric',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.en_GB]),
            self.build_tts_voice_v3('Emily (British)', 'Emily',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.en_GB]),
            self.build_tts_voice_v3('Luna (British)', 'Luna',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.en_GB]),
            self.build_tts_voice_v3('Luca (British)', 'Luca',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.en_GB]),
            self.build_tts_voice_v3('Wendy (British)', 'Wendy',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.en_GB]),
            self.build_tts_voice_v3('William (British)', 'William',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.en_GB]),
            self.build_tts_voice_v3('Olivia (British)', 'Olivia',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.en_GB]),

            # Special dialect voices
            self.build_tts_voice_v3('Shanshan (Cantonese)', 'Shanshan',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_HK]),
            self.build_tts_voice_v3('Xiaoyue (Sichuan)', 'Xiaoyue',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Lydia (Bilingual)', 'Lydia',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Aishuo (Natural)', 'Aishuo',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.zh_CN, cloudlanguagetools.languages.AudioLanguage.en_US]),
            self.build_tts_voice_v3('Qingqing (Taiwanese)', 'Qingqing',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Cuijie (Northeastern)', 'Cuijie',
                cloudlanguagetools.constants.Gender.Female, [cloudlanguagetools.languages.AudioLanguage.zh_CN]),
            self.build_tts_voice_v3('Xiaoze (Hunan)', 'Xiaoze',
                cloudlanguagetools.constants.Gender.Male, [cloudlanguagetools.languages.AudioLanguage.zh_CN])
        ])
        
        return result
