import os
import base64
import tempfile
import cloudlanguagetools.constants
import cloudlanguagetools.azure
import cloudlanguagetools.google

class ServiceManager():
    def  __init__(self):
        self.services = {}
        self.services[cloudlanguagetools.constants.Service.Azure.name] = cloudlanguagetools.azure.AzureService()
        self.services[cloudlanguagetools.constants.Service.Google.name] = cloudlanguagetools.google.GoogleService()

    def configure(self):
        # azure
        self.configure_azure(os.environ['AZURE_REGION'], os.environ['AZURE_KEY'], os.environ['AZURE_TRANSLATOR_KEY'])

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

    def configure_azure(self, region, key, translator_key):
        self.services[cloudlanguagetools.constants.Service.Azure.name].configure(key, region, translator_key)

    def configure_google(self, credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.services[cloudlanguagetools.constants.Service.Google.name].configure()

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
        language_list = self.get_translation_language_list()
        return [language.json_obj() for language in language_list]

    def get_tts_audio(self, text, service, voice_id, options):
        service = self.services[service]
        return service.get_tts_audio(text, voice_id, options)

    def get_translation(self, text, service, from_language_key, to_language_key):
        service = self.services[service]
        return service.get_translation(text, from_language_key, to_language_key)

    def detect_language(self, text_list):
        service = self.services[cloudlanguagetools.constants.Service.Azure.name]
        result = service.detect_language(text_list)
        return result