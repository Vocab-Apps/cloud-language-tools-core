import json
import requests
import tempfile
import logging
import time

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors


FPTAI_VOICE_SPEED_DEFAULT = 0


class FptAiVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, voice_id, name, gender, region):
        self.service = cloudlanguagetools.constants.Service.FptAi
        self.audio_language = audio_language
        self.voice_id = voice_id
        self.name = name
        self.gender = gender
        self.region = region

    def get_voice_key(self):
        return {
            'voice_id': self.voice_id
        }

    def get_voice_shortname(self):
        return f'{self.name} ({self.region})'

    def get_options(self):
        return {
            'speed' : {
                'type': 'number',
                'min': -3,
                'max': 3,
                'default': FPTAI_VOICE_SPEED_DEFAULT
            },            
        }


class FptAiService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        self.api_key = config['key']

    def get_translation(self, text, from_language_key, to_language_key):
        raise cloudlanguagetools.errors.RequestError('not supported')


    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        api_url = "https://api.fpt.ai/hmi/tts/v5"
        body = text
        headers = {
            'api_key': self.api_key,
            'voice': voice_key['voice_id'],
            'Cache-Control': 'no-cache',
            'format': 'mp3',
            #'speed': str(options['speed'])
        }
        speed = options.get('speed', FPTAI_VOICE_SPEED_DEFAULT)
        if speed != FPTAI_VOICE_SPEED_DEFAULT:
            headers['speed'] = str(speed)
        response = requests.post(api_url, headers=headers, data=body.encode('utf-8'), 
            timeout=cloudlanguagetools.constants.RequestTimeout)

        if response.status_code == 200:
            response_data = response.json()
            async_url = response_data['async']
            logging.debug(f'received async_url: {async_url}')

            # wait until the audio is available
            audio_available = False
            total_tries = 7
            max_tries = total_tries
            wait_time = 0.2
            while audio_available == False and max_tries > 0:
                time.sleep(wait_time)
                logging.debug(f'checking whether audio is available on {async_url}')
                response = requests.get(async_url, allow_redirects=True, timeout=cloudlanguagetools.constants.RequestTimeout)
                if response.status_code == 200 and len(response.content) > 0:
                    with open(output_temp_filename, 'wb') as audio:
                        audio.write(response.content)                    
                    audio_available = True
                wait_time = wait_time * 2
                max_tries -= 1            
            
            if not audio_available:
                error_message = f'could not retrieve audio after {total_tries} tries (url {async_url})'
                raise cloudlanguagetools.errors.RequestError(error_message)

            return output_temp_file

        error_message = f'could not retrieve FPT.AI audio: {response.content}'
        raise cloudlanguagetools.errors.RequestError(error_message)


    def get_tts_voice_list(self):
        # returns list of TtSVoice
        return [
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'leminh', 'Lê Minh', cloudlanguagetools.constants.Gender.Male, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'banmai', 'Ban Mai', cloudlanguagetools.constants.Gender.Female, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'thuminh', 'Thu Minh', cloudlanguagetools.constants.Gender.Female, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'giahuy', 'Gia Huy', cloudlanguagetools.constants.Gender.Male, 'miền Trung'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'ngoclam', 'Ngọc Lam', cloudlanguagetools.constants.Gender.Female, 'miền Trung'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'myan', 'Mỹ An', cloudlanguagetools.constants.Gender.Female, 'miền Trung'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'lannhi', 'Lan Nhi', cloudlanguagetools.constants.Gender.Female, 'miền Nam'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'linhsan', 'Linh San', cloudlanguagetools.constants.Gender.Female, 'miền Nam'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'minhquang', 'Minh Quang', cloudlanguagetools.constants.Gender.Male, 'miền Nam'),
            # acesound voices
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'banmaiace', 'Ban Mai (AceSound)', cloudlanguagetools.constants.Gender.Female, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'thuminhace', 'Thu Minh (AceSound)', cloudlanguagetools.constants.Gender.Female, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'ngoclamace', 'Ngọc Lam (AceSound)', cloudlanguagetools.constants.Gender.Female, 'miền Trung'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'linhsanace', 'Linh San (AceSound)', cloudlanguagetools.constants.Gender.Female, 'miền Nam'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'minhquangace', 'Minh Quang (AceSound)', cloudlanguagetools.constants.Gender.Male, 'miền Nam'),


        ]

    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   