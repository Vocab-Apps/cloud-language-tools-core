import os
import base64
import tempfile
import logging
import timeit
import cloudlanguagetools.constants
import cloudlanguagetools.errors
import cloudlanguagetools.azure
import cloudlanguagetools.google
import cloudlanguagetools.mandarincantonese
import cloudlanguagetools.easypronunciation
import cloudlanguagetools.watson
import cloudlanguagetools.naver
import cloudlanguagetools.amazon
import cloudlanguagetools.forvo
import cloudlanguagetools.cereproc
import cloudlanguagetools.epitran
import cloudlanguagetools.deepl
import cloudlanguagetools.vocalware
import cloudlanguagetools.fptai
import cloudlanguagetools.pythainlp
import cloudlanguagetools.spacy

class ServiceManager():
    def  __init__(self, secrets_config):
        self.secrets_config = secrets_config
        self.services = {}
        self.services[cloudlanguagetools.constants.Service.Azure.name] = cloudlanguagetools.azure.AzureService()
        self.services[cloudlanguagetools.constants.Service.Google.name] = cloudlanguagetools.google.GoogleService()
        self.services[cloudlanguagetools.constants.Service.MandarinCantonese.name] = cloudlanguagetools.mandarincantonese.MandarinCantoneseService()
        self.services[cloudlanguagetools.constants.Service.EasyPronunciation.name] = cloudlanguagetools.easypronunciation.EasyPronunciationService()
        self.services[cloudlanguagetools.constants.Service.Watson.name] = cloudlanguagetools.watson.WatsonService()
        self.services[cloudlanguagetools.constants.Service.Naver.name] = cloudlanguagetools.naver.NaverService()
        self.services[cloudlanguagetools.constants.Service.Amazon.name] = cloudlanguagetools.amazon.AmazonService()
        self.services[cloudlanguagetools.constants.Service.Forvo.name] = cloudlanguagetools.forvo.ForvoService()
        self.services[cloudlanguagetools.constants.Service.CereProc.name] = cloudlanguagetools.cereproc.CereProcService()
        self.services[cloudlanguagetools.constants.Service.Epitran.name] = cloudlanguagetools.epitran.EpitranService()
        self.services[cloudlanguagetools.constants.Service.DeepL.name] = cloudlanguagetools.deepl.DeepLService()
        self.services[cloudlanguagetools.constants.Service.VocalWare.name] = cloudlanguagetools.vocalware.VocalWareService()
        self.services[cloudlanguagetools.constants.Service.FptAi.name] = cloudlanguagetools.fptai.FptAiService()
        if self.secrets_config['load_nlp_models']:
            logging.info('loading nlp models')
            self.services[cloudlanguagetools.constants.Service.PyThaiNLP.name] = cloudlanguagetools.pythainlp.PyThaiNLPService()
            self.services[cloudlanguagetools.constants.Service.Spacy.name] = cloudlanguagetools.spacy.SpacyService()

    def configure(self):
        # azure
        self.configure_azure(os.environ['AZURE_REGION'], os.environ['AZURE_KEY'])

        # google
        google_key = os.environ['GOOGLE_KEY']
        data_bytes = base64.b64decode(google_key)
        data_str = data_bytes.decode('utf-8')    
        # write to file
        # note: temp file needs to be a member so it doesn't get collected
        self.google_key_temp_file = tempfile.NamedTemporaryFile()  
        google_key_filename = self.google_key_temp_file.name
        with open(google_key_filename, 'w') as f:
            f.write(data_str)    
            f.close()
        self.configure_google(google_key_filename)

        # easypronunciation
        self.configure_easypronunciation()

        # watson
        watson_translator_api_key = os.environ['WATSON_TRANSLATOR_API_KEY']
        watson_translator_url = os.environ['WATSON_TRANSLATOR_URL']
        watson_speech_api_key = os.environ['WATSON_SPEECH_API_KEY']
        watson_speech_url = os.environ['WATSON_SPEECH_URL']
        self.configure_watson(watson_translator_api_key, watson_translator_url, watson_speech_api_key, watson_speech_url)

        # naver
        naver_client_id = os.environ['NAVER_CLIENT_ID']
        naver_client_secret = os.environ['NAVER_CLIENT_SECRET']
        self.configure_naver(naver_client_id, naver_client_secret)

        # forvo
        self.configure_forvo()

        # cereproc
        self.services[cloudlanguagetools.constants.Service.CereProc.name].configure()

        self.services[cloudlanguagetools.constants.Service.DeepL.name].configure()

        # vocalware
        self.services[cloudlanguagetools.constants.Service.VocalWare.name].configure(
            self.secrets_config['services']['vocalware']['secret_phrase'],
            self.secrets_config['services']['vocalware']['account_id'],
            self.secrets_config['services']['vocalware']['api_id']
        )

        # fpt.ai
        self.services[cloudlanguagetools.constants.Service.FptAi.name].configure(
            self.secrets_config['services']['fptai']['api_key']
        )

        # for AWS, the boto3 library will read environment variables itself

        self.translation_language_list = self.get_translation_language_list()

    def configure_azure(self, region, key):
        self.services[cloudlanguagetools.constants.Service.Azure.name].configure(key, region)

    def configure_google(self, credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.services[cloudlanguagetools.constants.Service.Google.name].configure()

    def configure_easypronunciation(self):
        self.services[cloudlanguagetools.constants.Service.EasyPronunciation.name].configure()

    def configure_watson(self, translator_api_key, translator_url, speech_api_key, speech_url):
        self.services[cloudlanguagetools.constants.Service.Watson.name].configure(translator_api_key, translator_url, speech_api_key, speech_url)

    def configure_naver(self, naver_client_id, naver_client_secret):
        self.services[cloudlanguagetools.constants.Service.Naver.name].configure(naver_client_id, naver_client_secret)

    def configure_forvo(self):
        self.services[cloudlanguagetools.constants.Service.Forvo.name].configure()

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

        return {
            'language_list': language_list,
            'translation_options': [option.json_obj() for option in translation_language_list],
            'transliteration_options': [option.json_obj() for option in transliteration_language_list],
            'voice_list': [voice.json_obj() for voice in tts_voice_list],
            'tokenization_options': [option.json_obj() for option in tokenization_options],
        }
        

    def get_language_list(self):
        result_dict = {}
        for language in cloudlanguagetools.constants.Language:
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

    def get_tts_audio(self, text, service, voice_id, options):
        service = self.services[service]
        return service.get_tts_audio(text, voice_id, options)

    def get_translation(self, text, service, from_language_key, to_language_key):
        """return text"""
        service = self.services[service]
        return service.get_translation(text, from_language_key, to_language_key)

    def get_all_translations(self, text, from_language, to_language):
        global_starttime = timeit.default_timer()
        result = {}
        for service_name, service in self.services.items():
            # locate from language key
            from_language_entries = [x for x in self.translation_language_list if x.service.name == service_name and x.get_language_code() == from_language]
            if len(from_language_entries) == 1:
                starttime = timeit.default_timer()
                # this service provides the "from" language in translation list
                from_language_id = from_language_entries[0].get_language_id()
                # locate to language key
                to_language_entries = [x for x in self.translation_language_list if x.service.name == service_name and x.get_language_code() == to_language]
                if len(to_language_entries) == 1:
                    to_language_id = to_language_entries[0].get_language_id()
                    try:
                        result[service_name] = self.get_translation(text, service_name, from_language_id, to_language_id)
                    except cloudlanguagetools.errors.RequestError:
                        pass # don't do anything
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
        """returns an enum from constants.Language"""
        service = self.services[cloudlanguagetools.constants.Service.Azure.name]
        result = service.detect_language(text_list)
        return result