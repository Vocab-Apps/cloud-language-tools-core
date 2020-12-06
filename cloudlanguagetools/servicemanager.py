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

    def configure_azure(self, region, key):
        self.services[cloudlanguagetools.constants.Service.Azure.name].configure({'key': key, 'region': region})

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

    def get_tts_audio(self, text, service, voice_id, options):
        service = self.services[service]
        return service.get_tts_audio(text, voice_id, options)