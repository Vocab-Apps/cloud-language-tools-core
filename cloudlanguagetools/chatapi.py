import pydantic
import logging
import pprint
import pydub
import tempfile
from pydantic import Field
import cloudlanguagetools.servicemanager
import cloudlanguagetools.options
import cloudlanguagetools.languages

logger = logging.getLogger(__name__)

"""
This API is meant to interface with chatbots such as ChatGPT. 
it has a simplified interface meant to integrate well with OpenAI functions, and returns text only
(with the exception of audio)
it will try to find the ideal service and parameters for the given request, 
but sometimes parameters will be overriden to ensure an output is produced.
"""

class NoDataFoundException(Exception):
    pass


class TranslateQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to translate")
    source_language: cloudlanguagetools.languages.Language = Field(description="language to translate from")
    target_language: cloudlanguagetools.languages.Language = Field(description="language to translate to")
    service: cloudlanguagetools.constants.Service = Field(default=None, description='service to use for translation')

class TransliterateQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to transliterate")
    language: cloudlanguagetools.languages.Language = Field(description="language the text is in")
    service: cloudlanguagetools.constants.Service = Field(default=None, description='service to use for transliteration')

class DictionaryLookup(pydantic.BaseModel):
    input_text: str = Field(description="text lookup in the dictionary")
    language: cloudlanguagetools.languages.Language = Field(description="language the text is in")
    service: cloudlanguagetools.constants.Service = Field(default=None, description='service to use for dictionary lookup')

class AudioQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to pronounce")
    language: cloudlanguagetools.languages.Language = Field(description="language the text is in")
    service: cloudlanguagetools.constants.Service = Field(default=None, description='service to use audio pronunciation')
    gender: cloudlanguagetools.constants.Gender = Field(default=None, description='gender of the voice to pronounce the text in')

class ChatAPI():
    def __init__(self):
        self.manager = cloudlanguagetools.servicemanager.ServiceManager()
        self.manager.configure_default()

    def get_service_preference(self, preferred_service_list, default_service):
        if default_service != None:
            return [default_service] + preferred_service_list
        else:
            return preferred_service_list

    def translate(self, query: TranslateQuery):
        service_preference = self.get_service_preference([
            cloudlanguagetools.constants.Service.DeepL,
            cloudlanguagetools.constants.Service.Azure,
            cloudlanguagetools.constants.Service.Google,
            cloudlanguagetools.constants.Service.Amazon,
            cloudlanguagetools.constants.Service.Watson            
        ], query.service)

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
                raise NoDataFoundException(f'No service found for translation from {query.source_language} to {query.target_language}')

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
            raise NoDataFoundException(f'No transliteration service found for language {query.language.lang_name}')

        service_list = set([x.service for x in candidates])

        service_preference = self.get_service_preference([
            cloudlanguagetools.constants.Service.MandarinCantonese, # in case input text is chinese
            cloudlanguagetools.constants.Service.EasyPronunciation,
            cloudlanguagetools.constants.Service.Azure,
            cloudlanguagetools.constants.Service.PyThaiNLP,
        ], query.service)

        while service_preference[0] not in service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise NoDataFoundException(f'No service found for transliteration of {query.language.lang_name}')
            
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

    def dictionary_lookup(self, query: DictionaryLookup):
        dictionary_option_list = self.manager.get_dictionary_lookup_options()
        candidates = [x for x in dictionary_option_list if x.language == query.language]
        if len(candidates) == 0:
            raise NoDataFoundException(f'No dictionary service found for language {query.language.lang_name}')

        service_list = set([x.service for x in candidates])

        service_preference = self.get_service_preference([
            cloudlanguagetools.constants.Service.Wenlin,
            cloudlanguagetools.constants.Service.Azure,
        ], query.service)

        while service_preference[0] not in service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise NoDataFoundException(f'No service found for dictionary lookup of {query.language.lang_name}')
            
        service = service_preference[0]
        final_candidates = [x for x in candidates if x.service == service]

        dictionary_option = final_candidates[0]
        logger.debug(f'Using dictionary option {pprint.pformat(dictionary_option.json_obj())}')

        dictionary_result = self.manager.get_dictionary_lookup(
            query.input_text,
            service,
            dictionary_option.get_lookup_key()
        )
        result = ' / '.join(dictionary_result)
        return result
        

    def audio(self, query: AudioQuery, format: cloudlanguagetools.options.AudioFormat):
        logger.debug(f'processing audio query: {query}')
        # get full voice list, filter down to correct language
        # ====================================================
        voice_list = self.manager.get_tts_voice_list()
        default_audio_language = cloudlanguagetools.languages.AudioLanguageDefaults[query.language]
        candidates = [x for x in voice_list if x.audio_language == default_audio_language]

        # select service
        # ==============

        service_list = set([x.service for x in candidates])
        service_preference = self.get_service_preference([
            cloudlanguagetools.constants.Service.Azure,
            cloudlanguagetools.constants.Service.Amazon,
            cloudlanguagetools.constants.Service.Google,
            cloudlanguagetools.constants.Service.Watson,
            cloudlanguagetools.constants.Service.Naver,
            cloudlanguagetools.constants.Service.CereProc,
            cloudlanguagetools.constants.Service.VocalWare,
            cloudlanguagetools.constants.Service.FptAi,
        ], query.service)

        while service_preference[0] not in service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise NoDataFoundException(f'No service found for audio pronouncation of {query.language.lang_name}')

        # restrict to candidates for that service
        service = service_preference[0]
        candidates = [x for x in candidates if x.service == service]

        # select gender
        # =============
        gender_list = set([x.gender for x in candidates])
        gender_preference = [
            cloudlanguagetools.constants.Gender.Female,
            cloudlanguagetools.constants.Gender.Male,
            cloudlanguagetools.constants.Gender.Any
        ]
        if query.gender != None:
            gender_preference = [query.gender] + gender_preference

        while gender_preference[0] not in gender_list:
            gender_preference.pop(0)
        gender = gender_preference[0]
        logger.debug(f'selected gender: {gender}')

        candidates = [x for x in candidates if x.gender == gender]

        # pick the first candidate and generate audio
        # ===========================================

        voice = candidates[0]
        logger.debug(f'picked voice: {voice.get_voice_description()}')

        options = {}
        convert_mp3_to_ogg = False
        # by default, the format is mp3. if the request format is ogg, then we need to convert
        if format == cloudlanguagetools.options.AudioFormat.ogg_opus:
            logger.debug(f'requested ogg_opus format')
            convert_mp3_to_ogg = True
            if cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER in voice.get_options():
                logger.debug(f'voice supports audio format parameter')
                voice_available_formats = voice.get_options()[cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER]['values']
                logger.debug(f'voice available formats: {voice_available_formats}')
                if format.name in voice_available_formats:
                    # native ogg opus supported
                    logger.debug(f'ogg opus natively supported')
                    options[cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER] = format.name
                    convert_mp3_to_ogg = False

        # generate audio
        logger.debug(f'generating audio with voice {pprint.pformat(voice.json_obj())} options {pprint.pformat(options)}')
        audio_temp_file = self.manager.get_tts_audio(
            query.input_text,
            service,
            voice.get_voice_key(),
            options
        )

        if convert_mp3_to_ogg:
            logger.debug(f'need to convert from mp3 to ogg_opus')
            audio = pydub.AudioSegment.from_mp3(audio_temp_file.name)
            ogg_audio_temp_file = tempfile.NamedTemporaryFile(prefix='cloudlanguagetools_chatapi', suffix='.ogg')
            audio.export(ogg_audio_temp_file.name, format="ogg", codec="libopus")
            audio_temp_file = ogg_audio_temp_file

        return audio_temp_file

    def recognize_audio(self, sound_temp_file: tempfile.NamedTemporaryFile, audio_format: cloudlanguagetools.options.AudioFormat):
        # logger.debug(f'processing audio query: {query}')
        # result = self.manager.services[cloudlanguagetools.constants.Service.Azure].speech_to_text(sound_temp_file.name, audio_format)
        result = self.manager.services[cloudlanguagetools.constants.Service.OpenAI].speech_to_text(sound_temp_file.name, audio_format)
        return result