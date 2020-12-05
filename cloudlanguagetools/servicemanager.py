import cloudlanguagetools.constants
import cloudlanguagetools.azure

class ServiceManager():
    def  __init__(self):
        self.services = {}
        self.services[cloudlanguagetools.constants.Service.Azure.name] = cloudlanguagetools.azure.AzureService()

    def configure_azure(self, region, key):
        self.services[cloudlanguagetools.constants.Service.Azure.name].configure({'key': key, 'region': region})

    def get_tts_voice_list(self):
        result = []
        for key, service in self.services.items():
            result.extend(service.get_tts_voice_list())
        return result

    def get_tts_voice_list_json(self):
        tts_voice_list = self.get_tts_voice_list()
        return [voice.json_obj() for voice in tts_voice_list]