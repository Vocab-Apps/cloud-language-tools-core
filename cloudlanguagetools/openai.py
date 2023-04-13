import openai
import pprint
import logging

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
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