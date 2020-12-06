import json
import requests
import tempfile

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice


import azure.cognitiveservices.speech
import azure.cognitiveservices.speech.audio

class AzureVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        self.service = cloudlanguagetools.constants.Service.Azure
        locale = voice_data['Locale']
        language_enum_name = locale.replace('-', '_')
        self.language = cloudlanguagetools.constants.Language[language_enum_name]
        self.name = voice_data['Name']
        self.display_name = voice_data['DisplayName']
        self.local_name = voice_data['LocalName']
        self.short_name = voice_data['ShortName']
        self.gender = cloudlanguagetools.constants.Gender[voice_data['Gender']]

        self.locale = locale
        self.voice_type = voice_data['VoiceType']

    def get_voice_id(self):
        return self.name

class AzureService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, data):
        self.key = data['key']
        self.region = data['region']

    def get_token(self):
        fetch_token_url = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.key
        }
        response = requests.post(fetch_token_url, headers=headers)
        access_token = str(response.text)
        return access_token

    def get_tts_audio(self, text, voice_id, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name
        speech_config = azure.cognitiveservices.speech.SpeechConfig(subscription=self.key, region=self.region)
        speech_config.set_speech_synthesis_output_format(azure.cognitiveservices.speech.SpeechSynthesisOutputFormat["Audio24Khz96KBitRateMonoMp3"])
        audio_config = azure.cognitiveservices.speech.audio.AudioOutputConfig(filename=output_temp_filename)
        synthesizer = azure.cognitiveservices.speech.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        ssml_str = f"""<speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="{voice_id}">
    {text}
  </voice>
</speak>"""

        result = synthesizer.start_speaking_ssml(ssml_str)

        return output_temp_file

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



