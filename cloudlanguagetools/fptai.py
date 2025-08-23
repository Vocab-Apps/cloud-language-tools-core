import json
import requests
import tempfile
import logging
import time
import os

from pydub import AudioSegment

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors
from cloudlanguagetools.options import AudioFormat


FPTAI_VOICE_SPEED_DEFAULT = 1.0


class FptAiVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, voice_id, name, gender, region):
        self.service = cloudlanguagetools.constants.Service.FptAi
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
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
                'min': 0.5,
                'max': 2.0,
                'default': FPTAI_VOICE_SPEED_DEFAULT
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.wav.name,
                    cloudlanguagetools.options.AudioFormat.ogg_opus.name
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }
        }


class FptAiService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        self.api_key = config['key']

    def get_translation(self, text, from_language_key, to_language_key):
        raise cloudlanguagetools.errors.RequestError('not supported')


    def get_tts_audio(self, text, voice_key, options):
        # Get the requested audio format from options
        audio_format = options.get('audio_format', 'mp3')
        
        # Create temporary WAV file to store the initial response
        wav_temp_file = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_fptai_', suffix='.wav', delete=False)
        wav_temp_filename = wav_temp_file.name

        api_url = "https://mkp-api.fptcloud.com/v1/audio/speech"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # documentation: https://marketplace.fptcloud.com/en/ai-product/FPT.AI/FPT.AI-VITs
        data = {
            'model': 'FPT.AI-VITs',
            'input': text,
            'voice': voice_key['voice_id']
        }
        
        speed = options.get('speed', FPTAI_VOICE_SPEED_DEFAULT)
        if speed != FPTAI_VOICE_SPEED_DEFAULT:
            data['speed'] = speed
            
        response = requests.post(api_url, headers=headers, json=data, 
            timeout=cloudlanguagetools.constants.RequestTimeout)

        if response.status_code == 200:
            # The API returns WAV audio directly
            with open(wav_temp_filename, 'wb') as audio:
                audio.write(response.content)
            
            # If WAV format is requested, return as-is
            if audio_format == 'wav':
                output_temp_file = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_fptai_', suffix='.wav')
                with open(wav_temp_filename, 'rb') as src:
                    output_temp_file.write(src.read())
                output_temp_file.seek(0)
                os.unlink(wav_temp_filename)
                return output_temp_file
            
            # For other formats, convert using pydub
            audio_segment = AudioSegment.from_wav(wav_temp_filename)
            
            if audio_format == 'ogg_opus':
                # Convert to OGG Opus
                output_temp_file = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_fptai_', suffix='.ogg', delete=False)
                audio_segment.export(output_temp_file.name, format="ogg", codec="libopus")
                suffix = '.ogg'
            else:  # Default to MP3
                # Convert to MP3
                output_temp_file = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_fptai_', suffix='.mp3', delete=False)
                audio_segment.export(output_temp_file.name, format="mp3")
                suffix = '.mp3'
            
            # Clean up the intermediate WAV file
            os.unlink(wav_temp_filename)
            
            # Reopen as NamedTemporaryFile for compatibility with existing code
            final_temp_file = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_fptai_', suffix=suffix)
            with open(output_temp_file.name, 'rb') as src:
                final_temp_file.write(src.read())
            final_temp_file.seek(0)
            
            # Clean up the intermediate output file
            os.unlink(output_temp_file.name)
            
            return final_temp_file

        error_message = f'could not retrieve FPT.AI audio: {response.content}'
        raise cloudlanguagetools.errors.RequestError(error_message)


    def get_tts_voice_list(self):
        # returns list of TtSVoice
        return [
            # North voices
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_leminh', 'Le Minh', cloudlanguagetools.constants.Gender.Male, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_banmai', 'Ban Mai', cloudlanguagetools.constants.Gender.Female, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_thuminh', 'Thu Minh', cloudlanguagetools.constants.Gender.Female, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_huyphong', 'Huy Phong', cloudlanguagetools.constants.Gender.Male, 'miền Bắc'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_minhquan', 'Minh Quan', cloudlanguagetools.constants.Gender.Male, 'miền Bắc'),
            # South voices
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_kimngan', 'Kim Ngan', cloudlanguagetools.constants.Gender.Female, 'miền Nam'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_hatieumai', 'Ha Tieu Mai', cloudlanguagetools.constants.Gender.Female, 'miền Nam'),
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_giahuy', 'Gia Huy', cloudlanguagetools.constants.Gender.Male, 'miền Nam'),
            # Center voice
            FptAiVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'std_ngoclam', 'Ngoc Lam', cloudlanguagetools.constants.Gender.Female, 'miền Trung'),
        ]

    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   