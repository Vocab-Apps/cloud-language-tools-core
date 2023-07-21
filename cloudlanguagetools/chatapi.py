import pydantic
import logging
import pprint
import pydub
import tempfile
from pydantic import Field
from typing import Optional
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

class TranslateLookupQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to translate or lookup in the dictionary")
    source_language: cloudlanguagetools.languages.CommonLanguage = Field(description="language of the text to translate or lookup in dictionary")
    target_language: cloudlanguagetools.languages.CommonLanguage = Field(description="language to translate to, or language of dictionary definition")
    service: Optional[cloudlanguagetools.constants.Service] = Field(default=None, description='service to use for translation')

class TransliterateQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to transliterate")
    language: cloudlanguagetools.languages.CommonLanguage = Field(description="language the text is in")
    service: Optional[cloudlanguagetools.constants.Service] = Field(default=None, description='service to use for transliteration')

class AudioQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to pronounce / generate audio")
    language: cloudlanguagetools.languages.CommonLanguage = Field(description="language the text is in")
    service: Optional[cloudlanguagetools.constants.Service] = Field(default=None, description='service to use audio pronunciation')
    gender: Optional[cloudlanguagetools.constants.Gender] = Field(default=None, description='gender of the voice to pronounce the text in')

class BreakdownQuery(pydantic.BaseModel):
    input_text: str = Field(description="text to breakdown into words")
    language: cloudlanguagetools.languages.CommonLanguage = Field(description="language the text is in")
    translation_language: cloudlanguagetools.languages.CommonLanguage = Field(default=cloudlanguagetools.languages.CommonLanguage.en, description="language to translate into")
    translation_service: Optional[cloudlanguagetools.constants.Service] = Field(default=None, description='service to use for translation')
    transliteration_service: Optional[cloudlanguagetools.constants.Service] = Field(default=None, description='service to use for transliteration')


class ChatAPI():
    def __init__(self, manager):
        self.manager = manager

    def get_service_preference(self, preferred_service_list, default_service):
        if default_service != None:
            return [default_service] + preferred_service_list
        else:
            return preferred_service_list

    def select_translation_option(self, preferred_service: cloudlanguagetools.constants.Service,
            source_language: cloudlanguagetools.languages.Language,
            target_language: cloudlanguagetools.languages.Language):   
        """pick appropriate translation service"""

        service_preference = self.get_service_preference([
            cloudlanguagetools.constants.Service.DeepL,
            cloudlanguagetools.constants.Service.Azure,
            cloudlanguagetools.constants.Service.Google,
            cloudlanguagetools.constants.Service.Amazon,
            cloudlanguagetools.constants.Service.Watson            
        ], preferred_service)

        # get list of translation options
        translation_language_list = self.manager.get_translation_language_list()
        source_translation_language_list = [x for x in translation_language_list if x.language == source_language]
        target_translation_language_list = [x for x in translation_language_list if x.language == target_language]
        # get the list of services in common between source_translation_language_list and target_translation_language_list
        source_service_list = set([x.service for x in source_translation_language_list])
        target_service_list = set([x.service for x in target_translation_language_list])
        common_service_list = source_service_list.intersection(target_service_list)

        while service_preference[0] not in common_service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise NoDataFoundException(f'No service found for translation from {source_language} to {target_language}')

        service = service_preference[0]
        source_language_id = [x for x in source_translation_language_list if x.service == service][0].get_language_id()
        target_language_id = [x for x in target_translation_language_list if x.service == service][0].get_language_id()

        translation_option = {
            'service': service,
            'source_language_id': source_language_id,
            'target_language_id': target_language_id
        }
        return translation_option

    def select_transliteration_option(self, preferred_service: cloudlanguagetools.constants.Service,
            language: cloudlanguagetools.languages.Language):
        transliteration_option_list = self.manager.get_transliteration_language_list()
        candidates = [x for x in transliteration_option_list if x.language == language]
        if len(candidates) == 0:
            raise NoDataFoundException(f'No transliteration service found for language {language.lang_name}')

        service_list = set([x.service for x in candidates])

        service_preference = self.get_service_preference([
            cloudlanguagetools.constants.Service.MandarinCantonese, # in case input text is chinese
            cloudlanguagetools.constants.Service.EasyPronunciation,
            cloudlanguagetools.constants.Service.Azure,
            cloudlanguagetools.constants.Service.PyThaiNLP,
        ], preferred_service)

        while service_preference[0] not in service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise NoDataFoundException(f'No service found for transliteration of {language.lang_name}')
            
        service = service_preference[0]
        final_candidates = [x for x in candidates if x.service == service]

        if service == cloudlanguagetools.constants.Service.MandarinCantonese:
            final_candidates = [x for x in candidates if 
                                x.service == service and x.get_transliteration_key()['tone_numbers'] == False and
                                x.service == service and x.get_transliteration_key()['spaces'] == False]
        transliteration_option = final_candidates[0]

        return transliteration_option

    def translate(self, query: TranslateLookupQuery):
        logger.info(f'translating {query.input_text} from {query.source_language} to {query.target_language}')

        source_language = cloudlanguagetools.languages.Language[query.source_language.name]
        target_language = cloudlanguagetools.languages.Language[query.target_language.name]
        translation_option = self.select_translation_option(query.service, source_language, target_language)

        # get the translation
        translated_text = self.manager.get_translation(
            query.input_text,
            translation_option['service'],
            translation_option['source_language_id'],
            translation_option['target_language_id'],
        )
        return translated_text


    def transliterate(self, query: TransliterateQuery):
        language = cloudlanguagetools.languages.Language[query.language.name]
        transliteration_option = self.select_transliteration_option(query.service, language)
        transliterated_text = self.manager.get_transliteration(
            query.input_text,
            transliteration_option.service,
            transliteration_option.get_transliteration_key()
        )
        return transliterated_text

    def translate_or_lookup(self, query: TranslateLookupQuery):
        logger.info(f'translation or dictionary lookup: {query}')

        try:
            # try dictionary lookup as a first attempt
            result = self.dictionary_lookup(query)
            return result
        except cloudlanguagetools.errors.NotFoundError as e:
            # if dictionary lookup fails, try translation
            result = self.translate(query)
            return result

    def dictionary_lookup(self, query: TranslateLookupQuery):
        logger.info(f'dictionary lookup {query}')
        source_language = cloudlanguagetools.languages.Language[query.source_language.name]
        target_language = cloudlanguagetools.languages.Language[query.target_language.name]
        dictionary_option_list = self.manager.get_dictionary_lookup_options()
        candidates = [x for x in dictionary_option_list if x.language == source_language and x.target_language == target_language]
        if len(candidates) == 0:
            raise NoDataFoundException(f'No dictionary service found for source language {query.source_language.lang_name} / target language: {query.target_language.lang_name}')

        service_list = set([x.service for x in candidates])

        preferred_service = query.service
        # for Chinese, always enforce Wenlin
        if source_language in [
            cloudlanguagetools.languages.Language.yue,
            cloudlanguagetools.languages.Language.zh_cn,
            cloudlanguagetools.languages.Language.zh_tw,
            cloudlanguagetools.languages.Language.zh_lit
        ]:
            preferred_service = cloudlanguagetools.constants.Service.Wenlin

        service_preference = self.get_service_preference([
            cloudlanguagetools.constants.Service.Wenlin,
            cloudlanguagetools.constants.Service.Azure,
        ], preferred_service)

        while service_preference[0] not in service_list:
            service_preference.pop(0)
            if len(service_preference) == 0:
                raise NoDataFoundException(f'No service found for dictionary lookup of {query.source_language.lang_name}')
            
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
        

    def audio(self, query: AudioQuery, format: cloudlanguagetools.options.AudioFormat) -> tempfile.NamedTemporaryFile:
        logger.info(f'processing audio query: {query}')
        language = cloudlanguagetools.languages.Language[query.language.name]
        # get full voice list, filter down to correct language
        # ====================================================
        voice_list = self.manager.get_tts_voice_list()
        default_audio_language = cloudlanguagetools.languages.AudioLanguageDefaults[language]
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
                raise NoDataFoundException(f'No service found for audio pronouncation of {language.lang_name}')

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

    def breakdown(self, query: BreakdownQuery):
        logger.debug(f'processing breakdown query: {query}')

        language = cloudlanguagetools.languages.Language[query.language.name]
        translation_language = cloudlanguagetools.languages.Language[query.translation_language.name]

        # locate tokenization option
        # ==========================
        tokenization_options = self.manager.get_tokenization_options()
        tokenization_candidates = [x for x in tokenization_options if x.language == language]
        if len(tokenization_candidates) == 0:
            raise NoDataFoundException(f'No tokenization options found for language {language.lang_name}')
        tokenization_option = tokenization_candidates[0]

        # locate translation option
        # =========================
        translation_option = self.select_translation_option(query.translation_service, language, translation_language)

        # locate transliteration option
        # =============================
        transliteration_option = self.select_transliteration_option(query.transliteration_service, language)

        breakdown_result = self.manager.get_breakdown(query.input_text, 
            tokenization_option.json_obj(), 
            translation_option, 
            transliteration_option.json_obj())

        # process breakdown result
        # ========================

        lines = []
        for entry in breakdown_result:
            line_components = []
            line_components.append(entry['token'] + ':')
            if 'lemma' in entry and entry['lemma'] != entry['token']:
                line_components.append('/' + entry['lemma'])
            
            if 'transliteration' in entry:
                line_components.append(entry['transliteration'] + ',')

            if 'translation' in entry:
                line_components.append(entry['translation'])

            if 'pos_description' in entry:
                line_components.append('(' + entry['pos_description'] + ')')
            
            lines.append(' '.join(line_components))

        return '\n'.join(lines)