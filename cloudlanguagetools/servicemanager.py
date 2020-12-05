import os
import cloudlanguagetools.constants
import cloudlanguagetools.azure
import cloudlanguagetools.google

class ServiceManager():
    def  __init__(self):
        self.services = {}
        self.services[cloudlanguagetools.constants.Service.Azure.name] = cloudlanguagetools.azure.AzureService()
        self.services[cloudlanguagetools.constants.Service.Google.name] = cloudlanguagetools.google.GoogleService()

    def configure_azure(self, region, key):
        self.services[cloudlanguagetools.constants.Service.Azure.name].configure({'key': key, 'region': region})

    def configure_google(self, credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

    def get_tts_voice_list(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_tts_voice_list())
        return result

    def get_tts_voice_list_json(self):
        tts_voice_list = self.get_tts_voice_list()
        return [voice.json_obj() for voice in tts_voice_list]

    def get_tts_audio(self, service, voice_id, options):
        pass