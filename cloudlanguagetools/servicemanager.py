import logging
import timeit
import functools
import cachetools
from typing import List, Optional
import requests.exceptions
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.errors
import cloudlanguagetools.azure
import cloudlanguagetools.google
import cloudlanguagetools.watson
import cloudlanguagetools.naver
import cloudlanguagetools.amazon
import cloudlanguagetools.forvo
import cloudlanguagetools.cereproc
import cloudlanguagetools.vocalware
import cloudlanguagetools.fptai
import cloudlanguagetools.voicen
import cloudlanguagetools.elevenlabs
import cloudlanguagetools.deepl
import cloudlanguagetools.epitran
import cloudlanguagetools.mandarincantonese
import cloudlanguagetools.easypronunciation
import cloudlanguagetools.pythainlp
import cloudlanguagetools.spacy
import cloudlanguagetools.wenlin
import cloudlanguagetools.libretranslate
import cloudlanguagetools.openai
import cloudlanguagetools.alibaba
import cloudlanguagetools.gemini
import cloudlanguagetools.configuration
import cloudlanguagetools.test_services
import cloudlanguagetools.translationlanguage
from cloudlanguagetools.constants import Service

# service enum -> class implementing it
SERVICE_CLASSES = {
    Service.Azure: cloudlanguagetools.azure.AzureService,
    Service.Google: cloudlanguagetools.google.GoogleService,
    Service.Watson: cloudlanguagetools.watson.WatsonService,
    Service.Naver: cloudlanguagetools.naver.NaverService,
    Service.Amazon: cloudlanguagetools.amazon.AmazonService,
    Service.Forvo: cloudlanguagetools.forvo.ForvoService,
    Service.CereProc: cloudlanguagetools.cereproc.CereProcService,
    Service.VocalWare: cloudlanguagetools.vocalware.VocalWareService,
    Service.FptAi: cloudlanguagetools.fptai.FptAiService,
    Service.ElevenLabs: cloudlanguagetools.elevenlabs.ElevenLabsService,
    Service.EasyPronunciation: cloudlanguagetools.easypronunciation.EasyPronunciationService,
    Service.Epitran: cloudlanguagetools.epitran.EpitranService,
    Service.DeepL: cloudlanguagetools.deepl.DeepLService,
    Service.PyThaiNLP: cloudlanguagetools.pythainlp.PyThaiNLPService,
    Service.Spacy: cloudlanguagetools.spacy.SpacyService,
    Service.MandarinCantonese: cloudlanguagetools.mandarincantonese.MandarinCantoneseService,
    Service.Wenlin: cloudlanguagetools.wenlin.WenlinService,
    Service.OpenAI: cloudlanguagetools.openai.OpenAIService,
    Service.Alibaba: cloudlanguagetools.alibaba.AlibabaService,
    Service.Gemini: cloudlanguagetools.gemini.GeminiService,
    Service.TestServiceA: cloudlanguagetools.test_services.TestServiceA,
    Service.TestServiceB: cloudlanguagetools.test_services.TestServiceB,
}


def cached_list(method):
    """Cache the result of an argument-less list-retrieving method in the ServiceManager instance's
    TTL cache, which configure() clears."""
    @functools.wraps(method)
    def wrapper(self):
        key = method.__name__
        if key in self.cache:
            return self.cache[key]
        result = method(self)
        self.cache[key] = result
        return result
    return wrapper


class ServiceManager():
    def __init__(self, configuration: Optional[cloudlanguagetools.configuration.ServicesConfiguration] = None):
        """Create a service manager. Without a configuration no service is enabled, call configure()."""
        self.services = {}
        self.configuration = cloudlanguagetools.configuration.ServicesConfiguration()
        self.cache = cachetools.TTLCache(maxsize=1024, ttl=cloudlanguagetools.constants.TTLCacheTimeout)
        if configuration is not None:
            self.configure(configuration)

    def configure(self, configuration: cloudlanguagetools.configuration.ServicesConfiguration):
        """Enable and configure the services present in the configuration, replacing any previous
        configuration. Services left out of the configuration are disabled."""
        if not isinstance(configuration, cloudlanguagetools.configuration.ServicesConfiguration):
            raise TypeError(f'expected a ServicesConfiguration, got {type(configuration).__name__}')
        services = {}
        for service_enum, service_config in configuration.enabled_services().items():
            service = SERVICE_CLASSES[service_enum]()
            service.configure(service_config)
            services[service_enum] = service
        self.services = services
        self.configuration = configuration
        self.cache.clear()

    def is_enabled(self, service_name) -> bool:
        return Service[service_name] in self.services

    def get_enabled_services(self) -> List[Service]:
        return list(self.services.keys())

    def get_service(self, service_name):
        """Return the service instance, raise errors.ServiceNotEnabledError if it is not enabled."""
        service_enum = Service[service_name]
        if service_enum not in self.services:
            raise cloudlanguagetools.errors.ServiceNotEnabledError(f'service {service_enum.name} is not enabled')
        return self.services[service_enum]

    def get_language_data_json(self):
        # retrieve all language data (tts, translation, transliteration, etc)
        logging.info('retrieving language data')
        
        logging.info('retrieving language list')
        language_list = self.get_language_list()
        logging.info('retrieving translation list')
        translation_language_list = self.get_translation_language_list()
        logging.info('retrieving transliteration language list')
        transliteration_language_list = self.get_transliteration_language_list()
        logging.info('retrieving tts voice list')
        tts_voice_list = self.get_tts_voice_list()
        logging.info('retrieving tokenization options')
        tokenization_options = self.get_tokenization_options()
        logging.info('retrieving dictionary lookup options')
        dictionary_lookup_options = self.get_dictionary_lookup_options()        

        return {
            'language_list': language_list,
            'translation_options': [option.json_obj() for option in translation_language_list],
            'transliteration_options': [option.json_obj() for option in transliteration_language_list],
            'voice_list': [voice.json_obj() for voice in tts_voice_list],
            'tokenization_options': [option.json_obj() for option in tokenization_options],
            'dictionary_lookup_options': [option.json_obj() for option in dictionary_lookup_options],
        }
        

    def get_language_data_json_v2(self):
        # retrieve all language data (tts, translation, transliteration, etc), sort by free/free+paid
        logging.info('retrieving language data')
        
        logging.info('retrieving translation list')
        translation_language_list = self.get_translation_language_list()
        logging.info('retrieving transliteration language list')
        transliteration_language_list = self.get_transliteration_language_list()
        logging.info('retrieving tts voice list')
        tts_voice_list = self.get_tts_voice_list()
        logging.info('retrieving tokenization options')
        tokenization_options = self.get_tokenization_options()
        logging.info('retrieving dictionary lookup options')
        dictionary_lookup_options = self.get_dictionary_lookup_options()        

        return {
            'premium': {
                'translation_options': [option.json_obj() for option in translation_language_list],
                'transliteration_options': [option.json_obj() for option in transliteration_language_list],
                'voice_list': [voice.json_obj() for voice in tts_voice_list],
                'tokenization_options': [option.json_obj() for option in tokenization_options],
                'dictionary_lookup_options': [option.json_obj() for option in dictionary_lookup_options],
            },
            'free': {
                'translation_options': [option.json_obj() for option in translation_language_list if option.service_fee == cloudlanguagetools.constants.ServiceFee.free],
                'transliteration_options': [option.json_obj() for option in transliteration_language_list if option.service_fee == cloudlanguagetools.constants.ServiceFee.free],
                'voice_list': [voice.json_obj() for voice in tts_voice_list if voice.service_fee == cloudlanguagetools.constants.ServiceFee.free],
                'tokenization_options': [option.json_obj() for option in tokenization_options if option.service_fee == cloudlanguagetools.constants.ServiceFee.free],
                'dictionary_lookup_options': [option.json_obj() for option in dictionary_lookup_options if option.service_fee == cloudlanguagetools.constants.ServiceFee.free],
            }
        }
                

    def get_language_list(self):
        result_dict = {}
        for language in cloudlanguagetools.languages.Language:
            result_dict[language.name] = language.lang_name
        return result_dict

    @cached_list
    def get_tts_voice_list(self):
        result = []
        for key, service in self.services.items():
            logging.info(f'retrieving voice list from {key}')
            result.extend(service.get_tts_voice_list())
        return result

    def get_tts_voice_list_json(self):
        tts_voice_list = self.get_tts_voice_list()
        return [voice.json_obj() for voice in tts_voice_list]

    @cached_list
    def get_tts_voice_list_v3(self):
        result = []
        for key, service in self.services.items():
            logging.info(f'retrieving voice list from {key}')
            result.extend(service.get_tts_voice_list_v3())
        return result

    @cached_list
    def get_translation_language_list(self) -> List[cloudlanguagetools.translationlanguage.TranslationLanguage]:
        result = []
        for key, service in self.services.items():
            result.extend(service.get_translation_language_list())
        return result        

    def get_translation_language_list_json(self):
        """return list of languages supported for translation, using plain objects/strings"""
        language_list = self.get_translation_language_list()
        return [language.json_obj() for language in language_list]

    @cached_list
    def get_transliteration_language_list(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_transliteration_language_list())
        return result

    def get_transliteration_language_list_json(self):
        """return list of languages supported for transliteration, using plain objects/strings"""
        language_list = self.get_transliteration_language_list()
        return [language.json_obj() for language in language_list]

    @cached_list
    def get_tokenization_options(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_tokenization_options())
        return result

    def get_tokenization_options_json(self):
        """return list of languages supported for tokenization, using plain objects/strings"""
        tokenization_list = self.get_tokenization_options()
        return [tokenization_option.json_obj() for tokenization_option in tokenization_list]

    # dictionary lookups

    @cached_list
    def get_dictionary_lookup_options(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_dictionary_lookup_list())
        return result

    def get_dictionary_lookup_options_json(self):
        dictionary_lookup_list = self.get_dictionary_lookup_options()
        return [dict_lookup_option.json_obj() for dict_lookup_option in dictionary_lookup_list]

    def get_tts_audio(self, text, service_name, voice_id, options):
        service = self.get_service(service_name)
        return service.get_tts_audio(text, voice_id, options)

    def get_tts_audio_v5(self, text, service_name, voice_id, options):
        """Generate TTS audio, normalizing all exceptions to TransientError or PermanentError.

        This method wraps get_tts_audio and ensures only exceptions derived from
        errors.TransientError or errors.PermanentError are raised. This allows
        callers to determine whether a failure can be retried (TransientError)
        or not (PermanentError).

        Raises:
            errors.TimeoutError: On HTTP request timeouts (subclass of TransientError).
            errors.TransientError: On failures that may succeed on retry.
            errors.PermanentError: On failures that will not succeed on retry.
        """
        try:
            service = self.get_service(service_name)
            return service.get_tts_audio(text, voice_id, options)
        except (cloudlanguagetools.errors.TransientError, cloudlanguagetools.errors.PermanentError):
            # these exceptions are already properly categorized, so just re-throw them
            raise
        except requests.exceptions.Timeout as e:
            # transient error, use errors.TimeoutError
            raise cloudlanguagetools.errors.TimeoutError(f'timeout generating TTS audio for {service_name}: {e}') from e
        except Exception as e:
            # assume this is a transient error for now, and the error may later be categorized as permanent
            raise cloudlanguagetools.errors.TransientError(f'unexpected error generating TTS audio for {service_name}: {e}') from e

    def get_translation(self, text, service_name: str, from_language_key, to_language_key):
        """return text"""
        service = self.get_service(service_name)
        return service.get_translation(text, from_language_key, to_language_key)

    def get_all_translations(self, text, from_language, to_language):
        global_starttime = timeit.default_timer()

        translation_language_list = self.get_translation_language_list()

        result = {}
        for service_enum, service in self.services.items():
            service_name = service_enum.name
            # locate from language key
            from_language_entries = [x for x in translation_language_list if x.service.name == service_name and x.get_language_code() == from_language]
            if len(from_language_entries) == 1:
                starttime = timeit.default_timer()
                # this service provides the "from" language in translation list
                from_language_id = from_language_entries[0].get_language_id()
                # locate to language key
                to_language_entries = [x for x in translation_language_list if x.service.name == service_name and x.get_language_code() == to_language]
                if len(to_language_entries) == 1:
                    to_language_id = to_language_entries[0].get_language_id()
                    try:
                        result[service_name] = self.get_translation(text, service_name, from_language_id, to_language_id)
                    except cloudlanguagetools.errors.RequestError:
                        pass # don't do anything
                    except Exception as e:
                        # default exception handler
                        logging.exception(f'could not retrieve translation for service {service_name}, text: {text}')
                    time_diff = timeit.default_timer() - starttime
                    logging.info(f'get_all_translation processing time for {service_name}: {time_diff:.1f}')
        global_time_diff = timeit.default_timer() - global_starttime
        logging.info(f'get_all_translation total processing time: {global_time_diff:.1f}')
        return result

    def get_transliteration(self, text, service_name: str, transliteration_key):
        service = self.get_service(service_name)
        return service.get_transliteration(text, transliteration_key)

    def get_tokenization(self, text, service_name: str, tokenization_key):
        service = self.get_service(service_name)
        return service.get_tokenization(text, tokenization_key)

    def get_dictionary_lookup(self, text, service_name, lookup_key):
        service = self.get_service(service_name)
        return service.get_dictionary_lookup(text, lookup_key)

    def get_breakdown(self, text, tokenization_option, translation_option, transliteration_option):
        
        # first, tokenize
        tokenization_service = tokenization_option['service']
        tokenization_key = tokenization_option['tokenization_key']
        tokenization_result = self.get_tokenization(text, tokenization_service, tokenization_key)

        if translation_option != None:
            translation_service = translation_option['service']
            translation_source_language_id = translation_option['source_language_id']
            translation_target_language_id = translation_option['target_language_id']

        if transliteration_option != None:
            transliteration_service = transliteration_option['service']
            transliteration_key = transliteration_option['transliteration_key']

        # then, enrich tokens with translation and transliteration
        result = []
        for token in tokenization_result:
            entry = {
                'token': token['token'],
                'lemma': token['lemma']
            }

            if token['can_translate'] and translation_option != None:
                # translate this token (lemma)
                entry['translation'] = self.get_translation(token['lemma'], translation_service, translation_source_language_id, translation_target_language_id)

            if token['can_transliterate'] and transliteration_option != None:
                # transliterate the token
                entry['transliteration'] = self.get_transliteration(token['token'], transliteration_service, transliteration_key)

            if 'pos_description' in token:
                entry['pos_description'] = token['pos_description']

            result.append(entry)
        
        return result

    # special handling for pinyin and jyutping
    # ========================================
    
    def get_pinyin_supported_languages(self):
        return [
            cloudlanguagetools.languages.Language.zh_cn,
            cloudlanguagetools.languages.Language.zh_tw,
        ]

    def get_jyutping_supported_languages(self):
        return [
            cloudlanguagetools.languages.Language.yue
        ]        

    def get_pinyin(self, text, tone_numbers, spaces, corrections=[]):
        return self.get_service(Service.MandarinCantonese).get_pinyin(text, tone_numbers, spaces, corrections)

    def get_jyutping(self, text, tone_numbers, spaces, corrections=[]):
        return self.get_service(Service.MandarinCantonese).get_jyutping(text, tone_numbers, spaces, corrections)

    # LLM APIs
    # ========

    def openai_single_prompt(self, text, max_tokens=None):
        return self.get_service(Service.OpenAI).single_prompt(text, max_tokens)

    def openai_full_query(self, messages, max_tokens=None):
        return self.get_service(Service.OpenAI).full_query(messages, max_tokens)

    # transcription (speech to text) and llm, used by the CLT-AI API
    # ===============================================================

    def get_transcription_services(self) -> List[cloudlanguagetools.constants.Service]:
        return [service_enum for service_enum, service in self.services.items() if service.get_transcription_options_model() is not None]

    def get_transcription(self, audio_path, service_name: str, audio_format, language, options):
        """convert audio into text. language is a languages.Language, or None"""
        service = self.get_service(service_name)
        return service.get_transcription(audio_path, audio_format, language, options)

    def get_llm_services(self) -> List[cloudlanguagetools.constants.Service]:
        return [service_enum for service_enum, service in self.services.items() if service.get_llm_options_model() is not None]

    def get_llm_response(self, prompt, service_name: str, instructions, options):
        service = self.get_service(service_name)
        return service.get_llm_response(prompt, instructions, options)

    def detect_language(self, text_list):
        """returns an enum from languages.Language"""
        service = self.get_service(Service.Azure)
        result = service.detect_language(text_list)
        return result

    def service_cost(self, text, service_name, request_type: cloudlanguagetools.constants.RequestType):
        """return the cost of using a service, in characters"""
        service = cloudlanguagetools.constants.Service[service_name]
        character_length = len(text)
        
        FREE_SERVICES = [
            cloudlanguagetools.constants.Service.MandarinCantonese,
            cloudlanguagetools.constants.Service.LibreTranslate,
            cloudlanguagetools.constants.Service.Epitran,
            cloudlanguagetools.constants.Service.Wenlin,
            cloudlanguagetools.constants.Service.PyThaiNLP,
            cloudlanguagetools.constants.Service.TestServiceA,
        ]

        if service in FREE_SERVICES:
            return 0

        if service == cloudlanguagetools.constants.Service.Naver and request_type == cloudlanguagetools.constants.RequestType.audio:
            return 6 * character_length

        return character_length