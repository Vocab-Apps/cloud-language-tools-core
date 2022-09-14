import os
import base64
import tempfile
import logging
import timeit
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
import cloudlanguagetools.encryption

LOAD_NLP_MODELS = os.environ.get('CLOUDLANGUAGETOOLS_CORE_LOAD_NLP', 'yes') == 'yes'

if LOAD_NLP_MODELS:
    import cloudlanguagetools.deepl
    import cloudlanguagetools.epitran
    import cloudlanguagetools.mandarincantonese
    import cloudlanguagetools.easypronunciation
    import cloudlanguagetools.pythainlp
    import cloudlanguagetools.spacy
    import cloudlanguagetools.wenlin
    import cloudlanguagetools.libretranslate    

class ServiceManager():
    def  __init__(self):
        self.services = {}
        self.services[cloudlanguagetools.constants.Service.Azure.name] = cloudlanguagetools.azure.AzureService()
        self.services[cloudlanguagetools.constants.Service.Google.name] = cloudlanguagetools.google.GoogleService()
        self.services[cloudlanguagetools.constants.Service.Watson.name] = cloudlanguagetools.watson.WatsonService()
        self.services[cloudlanguagetools.constants.Service.Naver.name] = cloudlanguagetools.naver.NaverService()
        self.services[cloudlanguagetools.constants.Service.Amazon.name] = cloudlanguagetools.amazon.AmazonService()
        self.services[cloudlanguagetools.constants.Service.Forvo.name] = cloudlanguagetools.forvo.ForvoService()
        self.services[cloudlanguagetools.constants.Service.CereProc.name] = cloudlanguagetools.cereproc.CereProcService()
        self.services[cloudlanguagetools.constants.Service.VocalWare.name] = cloudlanguagetools.vocalware.VocalWareService()
        self.services[cloudlanguagetools.constants.Service.FptAi.name] = cloudlanguagetools.fptai.FptAiService()
        self.services[cloudlanguagetools.constants.Service.Voicen.name] = cloudlanguagetools.voicen.VoicenService()

        if LOAD_NLP_MODELS:
            self.services[cloudlanguagetools.constants.Service.EasyPronunciation.name] = cloudlanguagetools.easypronunciation.EasyPronunciationService()
            self.services[cloudlanguagetools.constants.Service.Epitran.name] = cloudlanguagetools.epitran.EpitranService()
            self.services[cloudlanguagetools.constants.Service.DeepL.name] = cloudlanguagetools.deepl.DeepLService()
            self.services[cloudlanguagetools.constants.Service.PyThaiNLP.name] = cloudlanguagetools.pythainlp.PyThaiNLPService()
            self.services[cloudlanguagetools.constants.Service.Spacy.name] = cloudlanguagetools.spacy.SpacyService()
            self.services[cloudlanguagetools.constants.Service.MandarinCantonese.name] = cloudlanguagetools.mandarincantonese.MandarinCantoneseService()            
            self.services[cloudlanguagetools.constants.Service.Wenlin.name] = cloudlanguagetools.wenlin.WenlinService()
            self.services[cloudlanguagetools.constants.Service.LibreTranslate.name] = cloudlanguagetools.libretranslate.LibreTranslateService()

    def configure_default(self):
        # use the stored keys to configure services
        self.configure_services(cloudlanguagetools.encryption.decrypt())

    def configure_services(self, config):
        for service_name, value in config.items():
            if service_name in self.services:
                self.services[service_name].configure(value)

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
        

    def get_language_list(self):
        result_dict = {}
        for language in cloudlanguagetools.languages.Language:
            result_dict[language.name] = language.lang_name
        return result_dict

    def get_tts_voice_list(self):
        result = []
        for key, service in self.services.items():
            logging.info(f'retrieving voice list from {key}')
            result.extend(service.get_tts_voice_list())
        return result

    def get_tts_voice_list_json(self):
        tts_voice_list = self.get_tts_voice_list()
        return [voice.json_obj() for voice in tts_voice_list]

    def get_translation_language_list(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_translation_language_list())
        return result        

    def get_translation_language_list_json(self):
        """return list of languages supported for translation, using plain objects/strings"""
        language_list = self.get_translation_language_list()
        return [language.json_obj() for language in language_list]

    def get_transliteration_language_list(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_transliteration_language_list())
        return result

    def get_transliteration_language_list_json(self):
        """return list of languages supported for transliteration, using plain objects/strings"""
        language_list = self.get_transliteration_language_list()
        return [language.json_obj() for language in language_list]

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

    def get_dictionary_lookup_options(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_dictionary_lookup_list())
        return result

    def get_dictionary_lookup_options_json(self):
        dictionary_lookup_list = self.get_dictionary_lookup_options()
        return [dict_lookup_option.json_obj() for dict_lookup_option in dictionary_lookup_list]

    def get_tts_audio(self, text, service, voice_id, options):
        service = self.services[service]
        return service.get_tts_audio(text, voice_id, options)

    def get_translation(self, text, service, from_language_key, to_language_key):
        """return text"""
        service = self.services[service]
        return service.get_translation(text, from_language_key, to_language_key)

    def get_all_translations(self, text, from_language, to_language):
        global_starttime = timeit.default_timer()

        translation_language_list = self.get_translation_language_list()

        result = {}
        for service_name, service in self.services.items():
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

    def get_transliteration(self, text, service, transliteration_key):
        service = self.services[service]
        return service.get_transliteration(text, transliteration_key)

    def get_tokenization(self, text, service, tokenization_key):
        service = self.services[service]
        return service.get_tokenization(text, tokenization_key)

    def get_dictionary_lookup(self, text, service, lookup_key):
        service = self.services[service]
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



    def detect_language(self, text_list):
        """returns an enum from languages.Language"""
        service = self.services[cloudlanguagetools.constants.Service.Azure.name]
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
        ]

        if service in FREE_SERVICES:
            return 0

        if service == cloudlanguagetools.constants.Service.Naver and request_type == cloudlanguagetools.constants.RequestType.audio:
            return 6 * character_length

        return character_length