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
    service: cloudlanguagetools.constants.Service = Field(default=cloudlanguagetools.constants.Service.DeepL, description='service to use for translation')

class TransliterateQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to transliterate")
    language: cloudlanguagetools.languages.Language = Field(description="language the text is in")
    service: cloudlanguagetools.constants.Service = Field(default=cloudlanguagetools.constants.Service.EasyPronunciation, description='service to use for transliteration')

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
                return f'No service found for translation from {query.source_language} to {query.target_language}'

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


    def transliterate(self, query: TranslateQuery):
        transliteration_option_list = self.manager.get_transliteration_language_list()
        candidates = [x for x in transliteration_option_list if x.language == query.language]
        if len(candidates) == 0:
            return f'No transliteration service found for language {query.language.lang_name}'

        service_list = set([x.service for x in candidates])

        service_preference = [
            query.service,
            cloudlanguagetools.constants.Service.MandarinCantonese, # in case input text is chinese
            cloudlanguagetools.constants.Service.EasyPronunciation,
            cloudlanguagetools.constants.Service.Azure,
            cloudlanguagetools.constants.Service.PyThaiNLP,
        ]

        while service_preference[0] not in service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise RuntimeError(f'No service found for transliteration of {query.language.lang_name}')
            
        service = service_preference[0]
        final_candidates = [x for x in candidates if x.service == service]

        if service == cloudlanguagetools.constants.Service.MandarinCantonese:
            final_candidates = [x for x in candidates if 
                                x.service == service and x.get_transliteration_key()['tone_numbers'] == False and
                                x.service == service and x.get_transliteration_key()['spaces'] == False]
        transliteration_option = final_candidates[0]

        transliterated_text = self.manager.get_transliteration(
            query.input_text,
            service,
            transliteration_option.get_transliteration_key()
        )
        return transliterated_text
        