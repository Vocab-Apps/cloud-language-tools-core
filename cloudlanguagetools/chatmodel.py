import pydantic
import logging
import json
import pprint
import openai
import time
import cloudlanguagetools.chatapi

logger = logging.getLogger(__name__)

class FinishQuery(pydantic.BaseModel):
    pass

"""
holds an instance of a conversation
"""
class ChatModel():
    FUNCTION_NAME_TRANSLATE = 'translate'
    FUNCTION_NAME_TRANSLITERATE = 'transliterate'
    FUNCTION_NAME_FINISH = 'finish'

    def __init__(self, manager):
        self.manager = manager
        self.chatapi = cloudlanguagetools.chatapi.ChatAPI(self.manager)
        self.instruction = None
        self.message_history = []
    
    def set_instruction(self, instruction):
        self.instruction = instruction

    def set_send_message_callback(self, send_message_fn):
        self.send_message_fn = send_message_fn

    def send_message(self, message):
        self.send_message_fn(message)

    def call_openai(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant specialized in translation and language learning."},
            {"role": "system", "content": self.instruction},
            {"role": "system", "content": "When all tasks are done, call the finish function."}
        ]
        messages.extend(self.message_history)


        logger.debug(f"sending messages to openai: {pprint.pformat(messages)}")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            functions=self.get_openai_functions(),
            function_call= "auto",
            temperature=0.0
        )
        return response

    def process_message(self, message):
    
        max_calls = 10
        continue_processing = True

        # message_history contains the most recent request
        self.message_history.append({"role": "user", "content": message})

        while continue_processing and max_calls > 0:
            max_calls -= 1
            response = self.call_openai()
            logger.debug(pprint.pformat(response))
            message = response['choices'][0]['message']
            if 'function_call' in message:
                function_name = message['function_call']['name']
                logger.info(f'function_call: function_name: {function_name}')
                arguments = json.loads(message["function_call"]["arguments"])
                if function_name == self.FUNCTION_NAME_FINISH:
                    continue_processing = False
                    break
                else:
                    self.process_function_call(function_name, arguments)
            else:
                continue_processing = False

    def process_function_call(self, function_name, arguments):
        try:
            if function_name == self.FUNCTION_NAME_TRANSLATE:
                translate_query = cloudlanguagetools.chatapi.TranslateQuery(**arguments)
                result = self.chatapi.translate(translate_query)
            elif function_name == self.FUNCTION_NAME_TRANSLITERATE:
                query = cloudlanguagetools.chatapi.TransliterateQuery(**arguments)
                result = self.chatapi.transliterate(query)
        except cloudlanguagetools.chatapi.NoDataFoundException as e:
            result = str(e)
        logger.info(f'function: {function_name} result: {result}')
        self.message_history.append({"role": "function", "name": function_name, "content": result})
        self.send_message(result)

    def get_openai_functions(self):
        return [
            {
                'name': self.FUNCTION_NAME_TRANSLATE,
                'description': "Translate input text from source language to target language",
                'parameters': cloudlanguagetools.chatapi.TranslateQuery.model_json_schema(),
            },
            {
                'name': self.FUNCTION_NAME_TRANSLITERATE,
                'description': "Transliterate the input text in the given language",
                'parameters': cloudlanguagetools.chatapi.TransliterateQuery.model_json_schema(),
            },            
            # {
            #     'name': "pronounce",
            #     'description': "Pronounce input text in the given language",
            #     'parameters': PronounceQuery.model_json_schema(),
            # },
            {
                'name': self.FUNCTION_NAME_FINISH,
                'description': "Finish the conversation",
                'parameters': FinishQuery.model_json_schema(),
            },
        ]