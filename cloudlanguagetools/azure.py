import json
import requests
import tempfile
import uuid
import operator
import pydub
import logging
import pprint
import time
import cachetools
from typing import List

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.dictionarylookup
import cloudlanguagetools.errors
from cloudlanguagetools.options import AudioFormat


import azure.cognitiveservices.speech
import azure.cognitiveservices.speech.audio

logger = logging.getLogger(__name__)

AUDIO_LOCALE_OVERRIDE_MAP = {
    'sr-Latn-RS': 'sr_RS'
}

GENDER_MAP = {
    'Female': cloudlanguagetools.constants.Gender.Female,
    'Male': cloudlanguagetools.constants.Gender.Male,
    'Neutral': cloudlanguagetools.constants.Gender.Any,
}

VOICE_OPTIONS = {
            'rate' : {
                'type': cloudlanguagetools.options.ParameterType.number.name,
                'min': 0.5,
                'max': 3.0,
                'default': 1.0
            },
            'pitch': {
                'type': cloudlanguagetools.options.ParameterType.number.name,
                'min': -100,
                'max': 100,
                'default': 0
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
                'type': cloudlanguagetools.options.ParameterType.list.name,
                'values': [
                    cloudlanguagetools.options.AudioFormat.mp3.name,
                    cloudlanguagetools.options.AudioFormat.ogg_opus.name,
                    cloudlanguagetools.options.AudioFormat.wav.name,
                ],
                'default': cloudlanguagetools.options.AudioFormat.mp3.name
            }
}

class AzureVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        # print(voice_data)
        self.service = cloudlanguagetools.constants.Service.Azure
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        locale = voice_data['Locale']
        locale = AUDIO_LOCALE_OVERRIDE_MAP.get(locale, locale)
        language_enum_name = locale.replace('-', '_')
        self.audio_language = cloudlanguagetools.languages.AudioLanguage[language_enum_name]
        self.name = voice_data['Name']
        self.display_name = voice_data['DisplayName']
        self.local_name = voice_data['LocalName']
        self.short_name = voice_data['ShortName']
        self.gender = GENDER_MAP[voice_data['Gender']]

        self.locale = locale
        self.voice_type = voice_data['VoiceType']


    def get_voice_key(self):
        return {
            'name': self.name
        }

    def get_voice_shortname(self):
        if self.local_name != self.display_name:
            return f'{self.display_name} {self.local_name} ({self.voice_type})'
        else:
            return f'{self.display_name} ({self.voice_type})'

    def get_options(self):
        return VOICE_OPTIONS

def locale_to_audio_language(locale: str) -> cloudlanguagetools.languages.AudioLanguage:

    locale_override_map = {
        'zh-CN-shanxi': 'zh-CN-shaanxi'
    }
    locale = locale_override_map.get(locale, locale)

    locale = AUDIO_LOCALE_OVERRIDE_MAP.get(locale, locale)
    language_enum_name = locale.replace('-', '_')
    audio_language = cloudlanguagetools.languages.AudioLanguage[language_enum_name]    
    return audio_language

def build_tts_voice_v3(voice_data) -> cloudlanguagetools.ttsvoice.TtsVoice_v3:
    local_name = voice_data['LocalName']
    display_name = voice_data['DisplayName']
    voice_type = voice_data['VoiceType']

    # build all attributes required for TtsVoice_v3
    # name
    if local_name != display_name:
        voice_name = f"{display_name} {local_name} ({voice_type})"
    else:
        voice_name = f'{display_name} ({voice_type})'    
    voice_key = {
        'name': voice_data['Name']
    }
    options = VOICE_OPTIONS
    service = cloudlanguagetools.constants.Service.Azure
    gender = GENDER_MAP[voice_data['Gender']]
    service_fee = cloudlanguagetools.constants.ServiceFee.paid

    azure_locale_list = [voice_data['Locale']]
    if 'SecondaryLocaleList' in voice_data:
        azure_locale_list = voice_data['SecondaryLocaleList']
        # ensure the main locale is present
        azure_locale_list.append(voice_data['Locale'])
        # unique array
        azure_locale_list = list(set(azure_locale_list))

    audio_languages = [locale_to_audio_language(locale) for locale in azure_locale_list]

    return cloudlanguagetools.ttsvoice.TtsVoice_v3(
        name=voice_name,
        voice_key=voice_key,
        options=options,
        service=service,
        gender=gender,
        audio_languages=audio_languages,
        service_fee=service_fee)


def get_translation_language_enum(language_id):
    # print(f'language_id: {language_id}')
    azure_language_id_map = {
        'as': 'as_',
        'fr-ca': 'fr_ca',
        'fr-CA': 'fr_ca',
        'id': 'id_',
        'is': 'is_',
        'or': 'or_',
        'pt': 'pt_br',
        'pt-pt': 'pt_pt',
        'pt-PT': 'pt_pt',
        'sr-Cyrl': 'sr_cyrl',
        'sr-Latn': 'sr_latn',
        'tlh-Latn': 'tlh_latn',
        'tlh-Piqd': 'tlh_piqd',
        'zh-Hans': 'zh_cn',
        'zh-Hant': 'zh_tw',
        'lzh': 'zh_lit',
        'mn-Cyrl': 'mn_cyrl',
        'mn-Mong': 'mn',
        'iu-Latn': 'iu_latn',
        'lug': 'lg',
        'nya': 'ny',
        'run': 'rn',
    }
    if language_id in azure_language_id_map:
        language_id = azure_language_id_map[language_id]
    return cloudlanguagetools.languages.Language[language_id]

class AzureTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.Azure
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id

class AzureTransliterationLanguage(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, language_id, from_script, to_script, from_script_name, to_script_name, from_native_name, to_native_name):
        self.service = cloudlanguagetools.constants.Service.Azure
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)
        self.from_script = from_script
        self.to_script = to_script
        self.from_script_name = from_script_name
        self.to_script_name = to_script_name
        self.from_native_name = from_native_name
        self.to_native_name = to_native_name

    def get_transliteration_name(self):
        result = f'{self.language.lang_name} ({self.from_script_name}/{self.from_native_name} to {self.to_script_name}/{self.to_native_name}), {self.service.name}'
        return result

    def get_transliteration_shortname(self):
        result = f'{self.from_script_name}/{self.from_native_name} to {self.to_script_name}/{self.to_native_name}, {self.service.name}'
        return result        

    def get_transliteration_key(self):
        return {
            'language_id': self.language_id,
            'from_script': self.from_script,
            'to_script': self.to_script
        }

class AzureDictionaryLookup(cloudlanguagetools.dictionarylookup.DictionaryLookup):
    def __init__(self, source_language_code, target_language_code, lookup_type):
        self.service = cloudlanguagetools.constants.Service.Azure
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language = get_translation_language_enum(source_language_code)
        self.target_language = get_translation_language_enum(target_language_code)
        self.source_language_code = source_language_code
        self.target_language_code = target_language_code
        self.lookup_type = lookup_type

    def get_lookup_key(self):
        return {
            'source_language_code': self.source_language_code,
            'target_language_code': self.target_language_code,
            'language': self.language.name,
            'lookup_type': self.lookup_type.name
        }        

    def get_lookup_name(self):
        return f'{self.service.name} ({self.language.lang_name} to {self.target_language.lang_name}), {self.lookup_type.name}'

    def get_lookup_shortname(self):
        return f'{self.service.name}, {self.language.lang_name}, {self.lookup_type.name}'

class AzureService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.url_translator_base = 'https://api.cognitive.microsofttranslator.com'

    def configure(self, config):
        self.key = config['key']
        self.region = config['region']

    def get_token(self):
        fetch_token_url = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.key
        }
        response = requests.post(fetch_token_url, headers=headers, timeout=cloudlanguagetools.constants.RequestTimeout)
        access_token = str(response.text)
        return access_token

    def get_translator_headers(self):
        headers = {
            'Ocp-Apim-Subscription-Key': self.key,
            'Ocp-Apim-Subscription-Region': self.region,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        return headers        

    def get_tts_audio(self, text, voice_key, options):
        # https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech?tabs=streaming#audio-outputs
        # https://learn.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.speechsynthesisoutputformat?view=azure-python
        response_format_parameter, audio_format = self.get_request_audio_format({
            AudioFormat.mp3: 'Audio24Khz96KBitRateMonoMp3',
            AudioFormat.ogg_opus: 'Ogg48Khz16BitMonoOpus',
            AudioFormat.wav: 'Riff48Khz16BitMonoPcm'
        }, options, AudioFormat.mp3)

        output_temp_file = tempfile.NamedTemporaryFile(prefix=f'cloudlanguage_tools_{self.__class__.__name__}_audio', suffix=f'.{audio_format.name}')
        output_temp_filename = output_temp_file.name
        speech_config = azure.cognitiveservices.speech.SpeechConfig(subscription=self.key, region=self.region)
        speech_config.set_speech_synthesis_output_format(azure.cognitiveservices.speech.SpeechSynthesisOutputFormat[response_format_parameter])
        synthesizer = azure.cognitiveservices.speech.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        default_pitch = 0
        default_rate = 1.0

        pitch = options.get('pitch', default_pitch)
        pitch_str = f'{pitch:+.0f}Hz'
        rate = options.get('rate', default_rate)
        rate_str = f'{rate:0.1f}'


        prosody_start_str = ''
        prosody_end_str = ''

        if pitch != default_pitch or rate != default_rate:
            prosody_start_str = f"""<prosody pitch="{pitch_str}" rate="{rate_str}" >"""
            prosody_end_str = """</prosody>"""

        # do some cleaning on the text
        text = text.replace(' & ', ' &amp; ')

        # the ssml str must be super optimized to have no whitespace, no extra characters
        ssml_str = f"""<speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
<voice name="{voice_key['name']}">
{prosody_start_str}""".replace('\n', '') + text + f"""
{prosody_end_str}
</voice>
</speak>""".replace('\n', '')

        # print(f'[{ssml_str}] len: {len(ssml_str)}')

        result = synthesizer.speak_ssml(ssml_str)
        if result.reason != azure.cognitiveservices.speech.ResultReason.SynthesizingAudioCompleted:
            # special case errors:
            if 'standard voices will no longer be supported' in result.cancellation_details.error_details:
                error_message = 'Azure Standard voices are not supported anymore, please switch to Neural voices.'
            else:
                error_message = f'Could not generate audio: {result.cancellation_details.reason} {result.cancellation_details.error_details}'
            raise cloudlanguagetools.errors.RequestError(error_message)

        stream = azure.cognitiveservices.speech.AudioDataStream(result)
        stream.save_to_wav_file(output_temp_filename)

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
        response = requests.get(constructed_url, headers=headers, 
            timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()
        voice_list = json.loads(response.content)
        result = []
        for voice_data in voice_list:
            # print(voice_data['Status'])
            try:
                result.append(AzureVoice(voice_data))
            except KeyError:
                logging.error(f'could not process voice for {voice_data}', exc_info=True)
        return result

    def get_tts_voice_list_v3(self) -> List[cloudlanguagetools.ttsvoice.TtsVoice_v3]:
        # returns list of TtsVoice_v3

        token = self.get_token()

        base_url = f'https://{self.region}.tts.speech.microsoft.com/'
        path = 'cognitiveservices/voices/list'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + token,
        }        
        response = requests.get(constructed_url, headers=headers, 
            timeout=cloudlanguagetools.constants.RequestTimeout)
        response.raise_for_status()
        voice_list = json.loads(response.content)
        result = []
        for voice_data in voice_list:
            # print(voice_data['Status'])
            try:
                result.append(build_tts_voice_v3(voice_data))
            except:
                logger.exception(f'could not process voice for {voice_data}')
        return result            

    def get_translation(self, text, from_language_key, to_language_key):
        base_url = f'{self.url_translator_base}/translate?api-version=3.0'
        params = f'&to={to_language_key}&from={from_language_key}'
        url = base_url + params

        # You can pass more than one object in body.
        body = [{
            'text': text
        }]
        request = requests.post(url, headers=self.get_translator_headers(), json=body, timeout=cloudlanguagetools.constants.RequestTimeout)
        response = request.json()

        if 'error' in response:
            error_message = f'Azure: could not translate text [{text}] from {from_language_key} to {to_language_key} ({response})'
            raise cloudlanguagetools.errors.RequestError(error_message)

        return response[0]['translations'][0]['text']

    def get_transliteration(self, text, transliteration_key):
        return self.transliteration(text, transliteration_key['language_id'], transliteration_key['from_script'], transliteration_key['to_script'])

    def get_translation_language_list(self):
        azure_data = self.get_supported_languages()
        result = []
        for language_id, data in azure_data['translation'].items():
            try:
                result.append(AzureTranslationLanguage(language_id))
            except KeyError:
                logging.warning(f'could not process translation language for {language_id}, {data}', exc_info=True)
        return result

    def get_transliteration_language_list(self):
        result = []
        azure_data = self.get_supported_languages()
        for language_id, data in azure_data['transliteration'].items():
            try:
                # get the first script
                for from_script_data in data['scripts']:
                    from_script =  from_script_data['code']
                    from_native_name = from_script_data['nativeName']
                    for to_script_data in from_script_data['toScripts']:
                        to_script = to_script_data['code']
                        from_script_name = from_script_data['name']
                        to_script_name = to_script_data['name']
                        to_native_name = to_script_data['nativeName']
                    result.append(AzureTransliterationLanguage(
                        language_id, 
                        from_script, 
                        to_script, 
                        from_script_name, 
                        to_script_name,
                        from_native_name,
                        to_native_name))
            except KeyError:
                logging.error(f'could not process transliteration language for {language_id}, {data}', exc_info=True)
        return result


    @cachetools.cached(cache=cachetools.TTLCache(maxsize=1024, ttl=cloudlanguagetools.constants.TTLCacheTimeout))
    def get_supported_languages(self):
        max_retries = 3
        retry_delay = 5  # seconds
        url = 'https://api.cognitive.microsofttranslator.com/languages?api-version=3.0'

        # If you encounter any issues with the base_url or path, make sure
        # that you are using the latest endpoint: https://docs.microsoft.com/azure/cognitive-services/translator/reference/v3-0-languages
        path = '/languages?api-version=3.0'

        headers = {
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        for attempt in range(max_retries):
            try:
                request = requests.get(url, headers=headers, 
                    timeout=cloudlanguagetools.constants.RequestTimeoutLong)
                request.raise_for_status()
                response = request.json()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:  # If not the last attempt
                    logger.warning(f"Request failed. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Max retries reached. Unable to get supported languages.")
                    raise  # Re-raise the last exception if all retries failed

        # print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))        


    def detect_language(self, text_list):
        url = f'{self.url_translator_base}/detect?api-version=3.0'
        body = [{'text': text} for text in text_list]

        request = requests.post(url, headers=self.get_translator_headers(), json=body, timeout=cloudlanguagetools.constants.RequestTimeout)
        response = request.json()

        language_score = {}
        for entry in response:
            score = entry['score']
            language = entry['language']
            if language not in language_score:
                language_score[language] = 0
            language_score[language] += score

        highest_language = max(language_score.items(), key=operator.itemgetter(1))[0]
        return get_translation_language_enum(highest_language)

    def transliteration(self, text, language_key, from_script, to_script):
        url = f'{self.url_translator_base}/transliterate?api-version=3.0'
        params = f'&language={language_key}&fromScript={from_script}&toScript={to_script}'
        constructed_url = url + params

        body = [{
            'text': text
        }]
        request = requests.post(constructed_url, headers=self.get_translator_headers(), json=body, timeout=cloudlanguagetools.constants.RequestTimeout)
        response = request.json()

        assert(len(response) == 1)
        return response[0]['text']

    # supported languages: https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#speech-to-text
    def speech_to_text(self, mp3_filepath, audio_format, language=None):
        speech_config = azure.cognitiveservices.speech.SpeechConfig(subscription=self.key, region=self.region)

        if audio_format == cloudlanguagetools.options.AudioFormat.mp3:
            sound = pydub.AudioSegment.from_mp3(mp3_filepath)
        elif audio_format in [cloudlanguagetools.options.AudioFormat.ogg_opus, cloudlanguagetools.options.AudioFormat.ogg_vorbis]:
            sound = pydub.AudioSegment.from_ogg(mp3_filepath)
        elif audio_format == cloudlanguagetools.options.AudioFormat.wav:
            sound = pydub.AudioSegment.from_wav(mp3_filepath)
        wav_filepath = tempfile.NamedTemporaryFile(suffix='.wav').name
        sound.export(wav_filepath, format="wav")

        audio_input = azure.cognitiveservices.speech.audio.AudioConfig(filename=wav_filepath)

        # Creates a recognizer with the given settings
        if language != None:
            # we know which language
            logger.info(f'configuration speech recognition for language {language}')
            speech_recognizer = azure.cognitiveservices.speech.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input, language=language)
        else:
            # language unknown
            logger.info(f'configuration speech recognition for any language')
            speech_recognizer = azure.cognitiveservices.speech.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

        # Starts speech recognition, and returns after a single utterance is recognized. The end of a
        # single utterance is determined by listening for silence at the end or until a maximum of 15
        # seconds of audio is processed.  The task returns the recognition text as result. 
        # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
        # shot recognition like command or query. 
        # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
        result = speech_recognizer.recognize_once()

        # Checks result.
        if result.reason == azure.cognitiveservices.speech.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == azure.cognitiveservices.speech.ResultReason.NoMatch:
            error_message = "No speech could be recognized: {}".format(result.no_match_details)
            raise Exception(error_message)
        elif result.reason == azure.cognitiveservices.speech.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_message = "Speech Recognition canceled: {}".format(cancellation_details)
            raise Exception(error_message)

        raise "unknown error"

    def get_dictionary_lookup_list(self):
        result = []

        azure_data = self.get_supported_languages()
        for source_language_id, data in azure_data['dictionary'].items():
            for translation in data['translations']:
                target_language_id = translation['code']
                result.append(AzureDictionaryLookup(source_language_id, 
                                target_language_id, 
                                cloudlanguagetools.constants.DictionaryLookupType.Definitions))
                result.append(AzureDictionaryLookup(source_language_id, 
                                target_language_id, 
                                cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeech))
                result.append(AzureDictionaryLookup(source_language_id, 
                                target_language_id, 
                                cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeechDefinitions))

        return result

    def iterate_dictionary_results(self, text, lookup_key):
        from_language_code = lookup_key['source_language_code']
        to_language_code = lookup_key['target_language_code']
        base_url = f'{self.url_translator_base}/dictionary/lookup?api-version=3.0'
        params = f'&to={to_language_code}&from={from_language_code}'
        url = base_url + params

        logger.info(f'querying url for dictionary lookup: {url}')

        # You can pass more than one object in body.
        body = [{
            'text': text
        }]
        request = requests.post(url, headers=self.get_translator_headers(), json=body, timeout=cloudlanguagetools.constants.RequestTimeout)
        response = request.json()
        if len(response) > 1:
            raise Exception(f'more than one response entries, {url}, {text}')

        translation_entries = response[0]['translations']
        for translation_entry in translation_entries:
            yield translation_entry

    def collect_definitions(self, generator):
        result = []
        for entry in generator:
            result.append(entry['displayTarget'])
        return result

    def collect_partofspeech(self, generator):
        result = []
        for entry in generator:
            result.append(entry['posTag'].lower())
        result = list(set(result))
        result.sort()
        return result

    def collect_partofspeech_definitions(self, generator):
        result = {}
        for entry in generator:
            part_of_speech = entry['posTag'].lower()
            if part_of_speech not in result:
                result[part_of_speech] = []
            result[part_of_speech].append(entry['displayTarget'])
        return result        

    def collect_result_check_empty(self, generator, collect_result_fn, text):
        result = collect_result_fn(generator)

        not_found_error_msg = f'Azure: no results found for {text}'

        if type(result) is list:
            if len(result) == 0:
                raise cloudlanguagetools.errors.NotFoundError(not_found_error_msg)
        if type(result) is dict:
            if len(result.keys()) == 0:
                raise cloudlanguagetools.errors.NotFoundError(not_found_error_msg)

        return result

    def get_dictionary_lookup(self, text, lookup_key):
        lookup_type = cloudlanguagetools.constants.DictionaryLookupType[lookup_key['lookup_type']]
        lookup_type_fn_map = {
            cloudlanguagetools.constants.DictionaryLookupType.Definitions: self.collect_definitions,
            cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeech: self.collect_partofspeech,
            cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeechDefinitions: self.collect_partofspeech_definitions,
        }
        lookup_fn = lookup_type_fn_map[lookup_type]
        generator = self.iterate_dictionary_results(text, lookup_key)

        return self.collect_result_check_empty(generator, lookup_fn, text)


    def custom_dictionary_lookup(self, input_text, from_language_key, to_language_key):
        base_url = f'{self.url_translator_base}/dictionary/lookup?api-version=3.0'
        params = f'&to={to_language_key}&from={from_language_key}'
        url = base_url + params

        logging.info(f'querying url for dictionary lookup: {url}')

        # You can pass more than one object in body.
        body = [{
            'text': input_text
        }]
        request = requests.post(url, headers=self.get_translator_headers(), json=body, timeout=cloudlanguagetools.constants.RequestTimeout)
        response = request.json()

        pprint.pprint(response)

        translation_entries = response[0]['translations']
        translations = [entry['displayTarget'] for entry in translation_entries]

        return translations
        
        # print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))

        # return response[0]['translations'][0]['text']

    
    def dictionary_examples(self, input_text, translation, from_language_key, to_language_key):
        base_url = f'{self.url_translator_base}/dictionary/examples?api-version=3.0'
        params = f'&to={to_language_key}&from={from_language_key}'
        url = base_url + params

        print(url)

        # You can pass more than one object in body.
        body = [{
            'text': input_text,
            'translation': translation
        }]
        request = requests.post(url, headers=self.get_translator_headers(), json=body, timeout=cloudlanguagetools.constants.RequestTimeout)
        response = request.json()

        print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))

        # return response[0]['translations'][0]['text']    

    
