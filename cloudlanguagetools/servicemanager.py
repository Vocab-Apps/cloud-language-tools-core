import os
import base64
import tempfile
import cloudlanguagetools.constants
import cloudlanguagetools.errors
import cloudlanguagetools.azure
import cloudlanguagetools.google
import cloudlanguagetools.mandarincantonese
import cloudlanguagetools.easypronunciation
import cloudlanguagetools.watson
import cloudlanguagetools.naver
import cloudlanguagetools.amazon

class ServiceManager():
    def  __init__(self):
        self.services = {}
        self.services[cloudlanguagetools.constants.Service.Azure.name] = cloudlanguagetools.azure.AzureService()
        self.services[cloudlanguagetools.constants.Service.Google.name] = cloudlanguagetools.google.GoogleService()
        self.services[cloudlanguagetools.constants.Service.MandarinCantonese.name] = cloudlanguagetools.mandarincantonese.MandarinCantoneseService()
        self.services[cloudlanguagetools.constants.Service.EasyPronunciation.name] = cloudlanguagetools.easypronunciation.EasyPronunciationService()
        self.services[cloudlanguagetools.constants.Service.Watson.name] = cloudlanguagetools.watson.WatsonService()
        self.services[cloudlanguagetools.constants.Service.Naver.name] = cloudlanguagetools.naver.NaverService()
        self.services[cloudlanguagetools.constants.Service.Amazon.name] = cloudlanguagetools.amazon.AmazonService()

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
        easypronunciation_key = os.environ['EASYPRONUNCIATION_KEY']
        self.configure_easypronunciation(easypronunciation_key)

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

        # for AWS, the boto3 library will read environment variables itself

        self.translation_language_list = self.get_translation_language_list()

    def configure_azure(self, region, key):
        self.services[cloudlanguagetools.constants.Service.Azure.name].configure(key, region)

    def configure_google(self, credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.services[cloudlanguagetools.constants.Service.Google.name].configure()

    def configure_easypronunciation(self, access_token):
        self.services[cloudlanguagetools.constants.Service.EasyPronunciation.name].configure(access_token)

    def configure_watson(self, translator_api_key, translator_url, speech_api_key, speech_url):
        self.services[cloudlanguagetools.constants.Service.Watson.name].configure(translator_api_key, translator_url, speech_api_key, speech_url)

    def configure_naver(self, naver_client_id, naver_client_secret):
        self.services[cloudlanguagetools.constants.Service.Naver.name].configure(naver_client_id, naver_client_secret)

    def get_language_list(self):
        result_dict = {}
        for language in cloudlanguagetools.constants.Language:
            result_dict[language.name] = language.lang_name
        return result_dict

    def get_tts_voice_list(self):
        result = []
        for key, service in self.services.items():
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

    def get_tts_audio(self, text, service, voice_id, options):
        service = self.services[service]
        return service.get_tts_audio(text, voice_id, options)

    def get_translation(self, text, service, from_language_key, to_language_key):
        """return text"""
        service = self.services[service]
        return service.get_translation(text, from_language_key, to_language_key)

    def get_all_translations(self, text, from_language, to_language):
        result = {}
        for service_name, service in self.services.items():
            # locate from language key
            from_language_entries = [x for x in self.translation_language_list if x.service.name == service_name and x.get_language_code() == from_language]
            if len(from_language_entries) == 1:
                # this service provides the "from" language in translation list
                from_language_id = from_language_entries[0].get_language_id()
                # locate to language key
                to_language_entries = [x for x in self.translation_language_list if x.service.name == service_name and x.get_language_code() == to_language]
                assert(len(to_language_entries) == 1)
                to_language_id = to_language_entries[0].get_language_id()
                try:
                    result[service_name] = self.get_translation(text, service_name, from_language_id, to_language_id)
                except cloudlanguagetools.errors.RequestError:
                    pass # don't do anything
        return result

    def get_transliteration(self, text, service, transliteration_key):
        service = self.services[service]
        return service.get_transliteration(text, transliteration_key)

    def detect_language(self, text_list):
        """returns an enum from constants.Language"""
        service = self.services[cloudlanguagetools.constants.Service.Azure.name]
        result = service.detect_language(text_list)
        return result