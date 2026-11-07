import html
import logging
import pprint
import requests
import google.cloud.texttospeech
import google.api_core.exceptions
from google.api_core.client_options import ClientOptions
import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.errors
import cloudlanguagetools.google_tts_common

logger = logging.getLogger(__name__)

# Cloud Translation Basic (v2) REST API, authenticated with the API key
TRANSLATION_URL = 'https://translation.googleapis.com/language/translate/v2'

# updates on google text to speech:
# https://cloud.google.com/text-to-speech/docs/release-notes

def language_code_to_enum(language_code):
    override_map = {
        'cmn-TW': cloudlanguagetools.languages.AudioLanguage.zh_TW,
        'cmn-CN': cloudlanguagetools.languages.AudioLanguage.zh_CN,
        'yue-HK': cloudlanguagetools.languages.AudioLanguage.zh_HK
    }
    if language_code in override_map:
        return override_map[language_code]
    language_enum_name = language_code.replace('-', '_')
    return cloudlanguagetools.languages.AudioLanguage[language_enum_name]

GENDER_MAP = {
    google.cloud.texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED: cloudlanguagetools.constants.Gender.Any,
    google.cloud.texttospeech.SsmlVoiceGender.NEUTRAL: cloudlanguagetools.constants.Gender.Any,
    google.cloud.texttospeech.SsmlVoiceGender.MALE: cloudlanguagetools.constants.Gender.Male,
    google.cloud.texttospeech.SsmlVoiceGender.FEMALE: cloudlanguagetools.constants.Gender.Female,
}

VOICES_WITHOUT_PITCH_SUPPORT = ['Studio', 'Chirp', 'Journey']

# Determines whether a given voice name supports SSML input.
# Chirp3-HD voices support SSML, but regular Chirp and Journey voices do not.
voice_supports_ssml = lambda voice_name: not (
    any(v in voice_name for v in ['Chirp', 'Journey']) and 'Chirp3-HD' not in voice_name
)

class GoogleVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, voice_data):
        logger.debug(f'processing voice {voice_data}')
        logger.debug(pprint.pformat(voice_data))
        self.service = cloudlanguagetools.constants.Service.Google
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.name = voice_data.name
        self.google_ssml_gender = google.cloud.texttospeech.SsmlVoiceGender(voice_data.ssml_gender)
        self.gender = GENDER_MAP[self.google_ssml_gender]
        if len(voice_data.language_codes) != 1:
            logger.error(f'expected exactly one language code for voice {voice_data.name}, got {voice_data.language_codes}')
        self.google_language_code = voice_data.language_codes[0]
        self.audio_language = language_code_to_enum(self.google_language_code)

    def supports_pitch(self):
        return not any(voice_type in self.name for voice_type in VOICES_WITHOUT_PITCH_SUPPORT)

    def get_voice_shortname(self):
        return self.name

    def get_voice_key(self):
        return {
            'name': self.name,
            'language_code': self.google_language_code,
            'ssml_gender': self.google_ssml_gender.name
        }

    def get_options(self):
        options = {
            'speaking_rate': {
                'type': 'number',
                'min': 0.25,
                'max': 4.0,
                'default': 1.0
            },
            cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: cloudlanguagetools.google_tts_common.AUDIO_FORMAT_OPTION
        }
        if self.supports_pitch():
            options['pitch'] = {
                'type': 'number',
                'min': -20.0,
                'max': 20.0,
                'default': 0.0
            }
        return options        


def get_translation_language_enum(language_id):
    google_language_id_map = {
        'as': 'as_',
        'fr-ca': 'fr_ca',
        'id': 'id_',
        'is': 'is_',
        'or': 'or_',
        'ms-Arab': 'ms_arab',
        'pa-Arab': 'pa_arab',
        'pt': 'pt_br',
        'pt-pt': 'pt_pt',
        'pt-PT': 'pt_pt',
        'sr': 'sr_cyrl',
        'sr-Cyrl': 'sr_cyrl',
        'sr-Latn': 'sr_latn',
        'tlh-Latn': 'tlh_latn',
        'tlh-Piqd': 'tlh_piqd',
        'zh-CN': 'zh_cn',
        'zh-TW': 'zh_tw',
        'zh': 'zh_cn',
        'mni-Mtei': 'mni',
        'jv': 'jw'
    }
    if language_id in google_language_id_map:
        language_id = google_language_id_map[language_id]
    return cloudlanguagetools.languages.Language[language_id]

class GoogleTranslationLanguage(cloudlanguagetools.translationlanguage.TranslationLanguage):
    def __init__(self, language_id):
        self.service = cloudlanguagetools.constants.Service.Google
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language_id = language_id
        self.language = get_translation_language_enum(language_id)

    def get_language_id(self):
        return self.language_id


class GoogleService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.service = cloudlanguagetools.constants.Service.Google
        self.api_key = None

    def configure(self, config):
        self.api_key = config.api_key.get_secret_value()

    def get_client(self):
        if self.api_key is None:
            raise cloudlanguagetools.errors.AuthenticationError('Google: service is not configured')
        return google.cloud.texttospeech.TextToSpeechClient(client_options=ClientOptions(api_key=self.api_key))

    def translation_request(self, method, path, **kwargs):
        """Call the Cloud Translation v2 REST API, return the 'data' field of the response."""
        if self.api_key is None:
            raise cloudlanguagetools.errors.AuthenticationError('Google: service is not configured')
        headers = cloudlanguagetools.google_tts_common.get_api_key_headers(self.api_key)
        response = requests.request(method, TRANSLATION_URL + path, headers=headers,
            timeout=cloudlanguagetools.constants.RequestTimeout, **kwargs)
        if response.status_code >= 400:
            message = self._get_response_error_message(response)
            logger.warning(f'Google translation request {path} failed with status code {response.status_code}: {message}')
            if response.status_code in (401, 403):
                raise cloudlanguagetools.errors.AuthenticationError(f'Google translation authentication error: {message}')
            raise cloudlanguagetools.errors.RequestError(f'Google translation error: {message}')
        return response.json()['data']

    def get_tts_audio(self, text, voice_key, options):
        audio_format = cloudlanguagetools.google_tts_common.get_audio_format(options)

        try:
            client = self.get_client()

            # Note: the voice can also be specified by name.
            # Names of voices can be retrieved with client.list_voices().
            voice = google.cloud.texttospeech.VoiceSelectionParams(
                name=voice_key['name'],
                language_code=voice_key['language_code'],
                ssml_gender=google.cloud.texttospeech.SsmlVoiceGender[voice_key['ssml_gender']]
            )

            audio_config_params = {
                'audio_encoding': cloudlanguagetools.google_tts_common.get_audio_encoding(audio_format),
                'speaking_rate': options.get('speaking_rate', 1.0),
            }
            # Studio, Chirp, and Journey voices don't support pitch
            # https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types
            voice_supports_pitch = not any(voice_type in voice_key['name'] for voice_type in VOICES_WITHOUT_PITCH_SUPPORT)
            if voice_supports_pitch:
                audio_config_params['pitch'] = options.get('pitch', 0.0)
            audio_config = google.cloud.texttospeech.AudioConfig(**audio_config_params)

            # some voices don't support SSML and it's weirdly not documented
            # see voice_supports_ssml for details
            if voice_supports_ssml(voice_key['name']):
                ssml_text = '<speak>' + text + '</speak>'
                input_text = google.cloud.texttospeech.SynthesisInput(ssml=ssml_text)
            else:
                logger.info(f'with voice {voice_key}, use non-ssml input')
                input_text = google.cloud.texttospeech.SynthesisInput(text=text)

            speech_request = {"input": input_text, "voice": voice, "audio_config": audio_config}
            response = client.synthesize_speech(
                request=speech_request,
                timeout=cloudlanguagetools.constants.RequestTimeout
            )

            return cloudlanguagetools.google_tts_common.write_audio_response(response.audio_content, audio_format)
        except google.api_core.exceptions.DeadlineExceeded as deadline_exceeded_exception:
            logger.warning(f'Google Cloud TTS deadline exceeded: {deadline_exceeded_exception}')
            error_message = f'Google Cloud TTS timed out: {str(deadline_exceeded_exception)}'
            raise cloudlanguagetools.errors.TimeoutError(error_message) from deadline_exceeded_exception
        except google.api_core.exceptions.ResourceExhausted as resource_exhausted_exception:
            retry_after = None
            for detail in resource_exhausted_exception.details:
                if hasattr(detail, 'retry_delay'):
                    retry_after = detail.retry_delay.seconds
                    break
            # default to 60 second retry: Google rate limits are often minute-based so this makes sense
            if retry_after is None:
                retry_after = 60
            logger.warning(f'Google TTS rate limit hit (retry_after={retry_after}s): {resource_exhausted_exception}')
            rate_limit_message = f'Google TTS rate limit hit. Please retry after {retry_after} seconds.'
            raise cloudlanguagetools.errors.RateLimitRetryAfterError(rate_limit_message, retry_after=retry_after) from resource_exhausted_exception
        except google.api_core.exceptions.InvalidArgument as invalid_argument_error:
            logger.warning(f'Google Cloud TTS invalid argument: {invalid_argument_error}, code: {invalid_argument_error.code}, details: {invalid_argument_error.details}, errors: {invalid_argument_error.errors}')
            error_message = f'Google Cloud TTS error: {str(invalid_argument_error)}'
            raise cloudlanguagetools.errors.InputError(error_message) from invalid_argument_error
        except google.api_core.exceptions.GoogleAPICallError as api_error:
            logger.warning(f'Google Cloud TTS error: {api_error}, code: {api_error.code}, details: {api_error.details}, errors: {api_error.errors}')
            error_message = f'Google Cloud TTS error: {str(api_error)}'
            raise cloudlanguagetools.errors.RequestError(error_message) from api_error


    def get_tts_voice_list(self):
        client = self.get_client()

        # Performs the list voices request
        voices = client.list_voices()

        result = []

        for voice in voices.voices:
            # in 2025/08, voices with no dashes such as "Leda" started appearing in this list
            # they are not queryable directly, we get the error message
            # {"error":"Could not generate audio: 400 This voice requires a model name to be specified."}, 
            # data: {'text': 'success', 'service': 'Google', 'request_mode': 'batch', 'language_code': 'en', 
            # 'voice_key': {'name': 'Leda', 'language_code': 'en-US', 'ssml_gender': 'FEMALE'}, 'options': {}}
            # 
            # these are most likely Gemini voices, it's annoying that the `list_voices()` API call doesn't allow
            # us to distinguish them, so we exclude them for now.
            #
            # regular voices look like this: "name": "ar-XA-Chirp3-HD-Leda"
            if '-' not in voice.name:
                logger.warning(f'skipping voice with unexpected name format, is probably a Gemini voice: {voice.name}')
                continue
            try:
                result.append(GoogleVoice(voice))
            except KeyError:
                logging.error(f'could not process voice for {voice}', exc_info=True)

        return result

    def get_translation_language_list(self):
        data = self.get_translation_languages()
        result_dict = {}
        for entry in data:
            try:
                translation_language = GoogleTranslationLanguage(entry['language'])
                result_dict[translation_language.get_language_code()] = translation_language
            except KeyError:
                logging.warning(f'could not process translation language for {entry}', exc_info=True)
        return result_dict.values()

    def get_transliteration_language_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):
        data = self.translation_request('POST', '', json={'q': text, 'source': from_language_key, 'target': to_language_key})
        # the default (html) format escapes entities in the result
        return html.unescape(data['translations'][0]['translatedText'])

    def get_translation_languages(self):
        """List of {'language': code} entries."""
        return self.translation_request('GET', '/languages')['languages']

    def detect_language(self, input_text):
        """Return the detection ({'language', 'confidence', 'isReliable'}) for a string."""
        data = self.translation_request('POST', '/detect', json={'q': input_text})
        return data['detections'][0][0]
