import json
import requests

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice


import azure.cognitiveservices.speech
import azure.cognitiveservices.speech.audio

class AzureVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        self.name = voice_data['Name']
        self.display_name = voice_data['DisplayName']
        self.local_name = voice_data['LocalName']
        self.short_name = voice_data['ShortName']
        self.gender = cloudlanguagetools.constants.Gender[voice_data['Gender']]
        self.locale = voice_data['Locale']
        self.voice_type = voice_data['VoiceType']

class AzureService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, data):
        self.key = data['key']
        self.region = data['region']

    def get_token(self):
        fetch_token_url = "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.key
        }
        response = requests.post(fetch_token_url, headers=headers)
        access_token = str(response.text)
        return access_token

    def get_tts_voice_list(self):
        # returns list of TtSVoice

        token = self.get_token()

        base_url = f'https://{self.region}.tts.speech.microsoft.com/'
        path = 'cognitiveservices/voices/list'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + token,
        }        
        response = requests.get(constructed_url, headers=headers)
        if response.status_code == 200:
            voice_list = json.loads(response.content)
            result = []
            for voice_data in voice_list:
                result.append(AzureVoice(voice_data))
            return result



