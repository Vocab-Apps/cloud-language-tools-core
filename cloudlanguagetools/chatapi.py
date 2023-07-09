import pydantic
from pydantic import Field
import cloudlanguagetools.servicemanager

"""
This API is meant to interface with chatbots such as ChatGPT. 
it has a simplified interface meant to integrate well with OpenAI functions, and returns text only
(with the exception of audio)
it will try to find the ideal service and parameters for the given request, 
but sometimes parameters will be overriden to ensure an output is produced.
"""


class TranslateQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to translate")
    source_language: cloudlanguagetools.languages.Language = Field(description="language to translate from")
    target_language: cloudlanguagetools.languages.Language = Field(description="language to translate to")
    service: cloudlanguagetools.constants.Service = cloudlanguagetools.constants.Service.DeepL

class ChatAPI():
    def __init__(self):
        self.manager = cloudlanguagetools.servicemanager.ServiceManager()
        self.manager.configure_default()

    def translate(self, query: TranslateQuery):
        service_preference = [
            query.service,
            cloudlanguagetools.constants.Service.DeepL,
            cloudlanguagetools.constants.Service.Azure,
            cloudlanguagetools.constants.Service.Google,
            cloudlanguagetools.constants.Service.Amazon,
            cloudlanguagetools.constants.Service.Watson
        ]

        # get list of translation options
        translation_language_list = self.manager.get_translation_language_list()
        source_translation_language_list = [x for x in translation_language_list if x.language == query.source_language]
        target_translation_language_list = [x for x in translation_language_list if x.language == query.target_language]
        # get the list of services in common between source_translation_language_list and target_translation_language_list
        source_service_list = set([x.service for x in source_translation_language_list])
        target_service_list = set([x.service for x in target_translation_language_list])
        common_service_list = source_service_list.intersection(target_service_list)

        while service_preference[0] not in common_service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise RuntimeError(f'no service found for translation from {query.source_language} to {query.target_language}')

        service = service_preference[0]
        source_language_key = [x for x in source_translation_language_list if x.service == service][0].get_language_id()
        target_language_key = [x for x in target_translation_language_list if x.service == service][0].get_language_id()

        # get the translation
        translated_text = self.manager.get_translation(
            query.input_text,
            service,
            source_language_key,
            target_language_key,
        )
        return translated_text


        