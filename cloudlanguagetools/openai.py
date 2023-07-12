import openai
import pprint
import logging
import tempfile
import pydub

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.options
import cloudlanguagetools.transliterationlanguage

logger = logging.getLogger(__name__)

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

