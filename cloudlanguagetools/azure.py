import json
import requests
import tempfile
import uuid

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage


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


    def get_voice_key(self):
        return {
            'name': self.name
        }

def get_translation_language_enum(language_id):
    print(f'language_id: {language_id}')
    azure_language_id_map = {
        'as': 'as_',
        'fr-ca': 'fr_ca',
        'id': 'id_',
        'is': 'is_',
        'or': 'or_',
        'pt': 'pt_br',
        'pt-pt': 'pt_pt',
        'sr-Cyrl': 'sr_cyrl',
        'sr-Latn': 'sr_latn',
        'tlh-Latn': 'tlh_latn',
        'tlh-Piqd': 'tlh_piqd',
        'zh-Hans': 'zh_cn',
        'zh-Hant': 'zh_tw'
    }
    if language_id in azure_language_id_map:
        language_id = azure_language_id_map[language_id]
    return cloudlanguagetools.constants.Language[language_id]

class AzureTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.Azure
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id

    

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

    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name
        speech_config = azure.cognitiveservices.speech.SpeechConfig(subscription=self.key, region=self.region)
        speech_config.set_speech_synthesis_output_format(azure.cognitiveservices.speech.SpeechSynthesisOutputFormat["Audio24Khz96KBitRateMonoMp3"])
        audio_config = azure.cognitiveservices.speech.audio.AudioOutputConfig(filename=output_temp_filename)
        synthesizer = azure.cognitiveservices.speech.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        ssml_str = f"""<speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="{voice_key['name']}">
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

    def get_translation_language_list(self):
        azure_data = self.get_supported_languages()
        result = []
        for language_id, data in azure_data['translation'].items():
            result.append(AzureTranslationLanguage(language_id))
        return result

    def get_supported_languages(self):
        url = 'https://api.cognitive.microsofttranslator.com/languages?api-version=3.0'

        # If you encounter any issues with the base_url or path, make sure
        # that you are using the latest endpoint: https://docs.microsoft.com/azure/cognitive-services/translator/reference/v3-0-languages
        path = '/languages?api-version=3.0'

        headers = {
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        request = requests.get(url, headers=headers)
        response = request.json()

        return response

        # print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))        


