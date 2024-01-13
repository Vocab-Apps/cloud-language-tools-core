import openai
import logging
import tempfile
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.options

logger = logging.getLogger(__name__)

DEFAULT_TTS_SPEED = 1.0

class OpenAIVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, name: str, 
                audio_language: cloudlanguagetools.languages.AudioLanguage,
                gender: cloudlanguagetools.constants.Gender):
        self.name = name
        self.gender = gender
        self.audio_language = audio_language
        self.service = cloudlanguagetools.constants.Service.OpenAI
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid

    def get_voice_key(self):
        return {
            'name': self.name,
            'language': self.audio_language.name            
        }

    def get_voice_shortname(self):
        return self.name

    def get_options(self):
        return {
            'speed' : {
                'type': cloudlanguagetools.options.ParameterType.number.name,
                'min': 0.25,
                'max': 4.0,
                'default': DEFAULT_TTS_SPEED
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.ogg_opus.name,
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }
        }

class OpenAIService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.chatbot_model = "gpt-3.5-turbo"

    def configure(self, config):
        self.api_key = config['api_key']
        openai.api_key = self.api_key

    def single_prompt(self, prompt, max_tokens):
        messages = [
            {'role': 'user', 'content': prompt}
        ]        

        if max_tokens != None:
            response = openai.ChatCompletion.create(
                model=self.chatbot_model,
                messages=messages,
                max_tokens=max_tokens
            )    
        else:
            response = openai.ChatCompletion.create(
                model=self.chatbot_model,
                messages=messages
            )    
        logger.debug(pprint.pformat(response))
        tokens_used = response['usage']['total_tokens']
        response_text = response['choices'][0]['message']['content']
        return response_text, tokens_used

    def full_query(self, messages, max_tokens):
        if max_tokens != None:
            response = openai.ChatCompletion.create(
                model=self.chatbot_model,
                messages=messages,
                max_tokens=max_tokens
            )    
        else:
            response = openai.ChatCompletion.create(
                model=self.chatbot_model,
                messages=messages
            )    
        logger.debug(pprint.pformat(response))
        return response

    def speech_to_text(self, filepath, audio_format: cloudlanguagetools.options.AudioFormat):

        if audio_format in [cloudlanguagetools.options.AudioFormat.ogg_opus, cloudlanguagetools.options.AudioFormat.ogg_vorbis]:
            # need to convert to wav first
            sound = pydub.AudioSegment.from_ogg(filepath)
            wav_tempfile = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_OpenAI_speech_to_text', suffix='.wav')
            sound.export(wav_tempfile.name, format="wav")
            filepath = wav_tempfile.name

        logger.debug(f'opening file {filepath}')
        audio_file= open(filepath, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript['text']
    
    
    def get_tts_voice_list(self) -> List[OpenAIVoice]:
        result = []

        supported_languages = [
            cloudlanguagetools.languages.AudioLanguage.en_US,
            cloudlanguagetools.languages.AudioLanguage.en_US,
        ]

        for audio_language in supported_languages:
            result.extend([
                OpenAIVoice('alloy', audio_language, cloudlanguagetools.constants.Gender.Female),
                OpenAIVoice('echo', audio_language, cloudlanguagetools.constants.Gender.Male),
                OpenAIVoice('fable', audio_language, cloudlanguagetools.constants.Gender.Female),
                OpenAIVoice('onyx', audio_language, cloudlanguagetools.constants.Gender.Male),
                OpenAIVoice('nova', audio_language, cloudlanguagetools.constants.Gender.Female),
                OpenAIVoice('shimmer', audio_language, cloudlanguagetools.constants.Gender.Female),
            ])
        return result

    def get_tts_audio(self, text, voice_key, options):
        # https://platform.openai.com/docs/guides/text-to-speech
        # https://platform.openai.com/docs/api-reference/audio/createSpeech?lang=python
        
        output_temp_file = tempfile.NamedTemporaryFile()

        speed = options.get('speed', DEFAULT_TTS_SPEED)
        response_format = options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, 
            cloudlanguagetools.options.AudioFormat.mp3.name)
        if response_format == cloudlanguagetools.options.AudioFormat.ogg_opus.name:
            response_format = 'opus'

        response = openai.audio.speech.create(
            model='tts-1-hd',
            voice=voice_key['name'],
            input=text,
            response_format=response_format,
            speed=speed
        )
        response.stream_to_file(output_temp_file.name)

        return output_temp_file
