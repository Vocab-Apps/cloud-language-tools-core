import base64
import logging
import pprint
import re
import tempfile

import requests

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.errors
import cloudlanguagetools.audio_processing
import cloudlanguagetools.google_tts_common
from cloudlanguagetools.languages import AudioLanguage

logger = logging.getLogger(__name__)

# Gemini API generateContent endpoint, authenticated with a Gemini API key.
# https://ai.google.dev/gemini-api/docs/speech-generation
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

# The Gemini 3.8 models take the style prompt in speechMetadata, the older models reject it.
SPEECH_METADATA_MODELS = {
    'gemini-3.8-flash-tts',
    'gemini-3.8-flash-lite-tts',
}

DEFAULT_MODEL = 'gemini-3.8-flash-tts'

# model name used by this library -> model name on the Gemini API. The library names of the
# 2.5 models are their Cloud Text-to-Speech names, kept so that saved voice options keep working.
GEMINI_API_MODEL_NAMES = {
    'gemini-3.8-flash-tts': 'gemini-3.8-flash-tts',
    'gemini-3.8-flash-lite-tts': 'gemini-3.8-flash-lite-tts',
    'gemini-3.1-flash-tts-preview': 'gemini-3.1-flash-tts-preview',
    'gemini-2.5-flash-tts': 'gemini-2.5-flash-preview-tts',
    'gemini-2.5-pro-tts': 'gemini-2.5-pro-preview-tts',
}
# generateContent returns 24 kHz, mono, 16-bit audio (WAV by default, or headerless audio/L16)
GENERATE_CONTENT_SAMPLE_RATE = 24000
DEFAULT_RATE_LIMIT_RETRY_AFTER = 60

VOICE_OPTIONS = {
    'model': {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': [
            'gemini-3.8-flash-tts',
            'gemini-3.8-flash-lite-tts',
            'gemini-3.1-flash-tts-preview',
            'gemini-2.5-flash-tts',
            'gemini-2.5-pro-tts',
        ],
        'default': DEFAULT_MODEL
    },
    'language_code': {
        'type': cloudlanguagetools.options.ParameterType.text.name,
        'default': 'en-US'
    },
    'prompt': {
        'type': cloudlanguagetools.options.ParameterType.text.name,
        'default': ''
    },
    cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: cloudlanguagetools.google_tts_common.AUDIO_FORMAT_OPTION
}

# Gemini TTS supported languages
# GA languages
TTS_SUPPORTED_LANGUAGES = [
    AudioLanguage.ar_EG,
    AudioLanguage.bn_BD,
    AudioLanguage.nl_NL,
    AudioLanguage.en_IN,
    AudioLanguage.en_US,
    AudioLanguage.fr_FR,
    AudioLanguage.de_DE,
    AudioLanguage.hi_IN,
    AudioLanguage.id_ID,
    AudioLanguage.it_IT,
    AudioLanguage.ja_JP,
    AudioLanguage.ko_KR,
    AudioLanguage.mr_IN,
    AudioLanguage.pl_PL,
    AudioLanguage.pt_BR,
    AudioLanguage.ro_RO,
    AudioLanguage.ru_RU,
    AudioLanguage.es_ES,
    AudioLanguage.ta_IN,
    AudioLanguage.te_IN,
    AudioLanguage.th_TH,
    AudioLanguage.tr_TR,
    AudioLanguage.uk_UA,
    AudioLanguage.vi_VN,
    # Preview languages
    AudioLanguage.af_ZA,
    AudioLanguage.sq_AL,
    AudioLanguage.am_ET,
    AudioLanguage.ar_XA,
    AudioLanguage.hy_AM,
    AudioLanguage.az_AZ,
    AudioLanguage.eu_ES,
    AudioLanguage.be_BY,
    AudioLanguage.bg_BG,
    AudioLanguage.my_MM,
    AudioLanguage.ca_ES,
    AudioLanguage.ceb_PH,
    AudioLanguage.zh_CN,
    AudioLanguage.zh_TW,
    AudioLanguage.hr_HR,
    AudioLanguage.cs_CZ,
    AudioLanguage.da_DK,
    AudioLanguage.en_AU,
    AudioLanguage.en_GB,
    AudioLanguage.et_EE,
    AudioLanguage.fil_PH,
    AudioLanguage.fi_FI,
    AudioLanguage.fr_CA,
    AudioLanguage.gl_ES,
    AudioLanguage.ka_GE,
    AudioLanguage.el_GR,
    AudioLanguage.gu_IN,
    AudioLanguage.ht_HT,
    AudioLanguage.he_IL,
    AudioLanguage.hu_HU,
    AudioLanguage.is_IS,
    AudioLanguage.jv_ID,
    AudioLanguage.kn_IN,
    AudioLanguage.kok_IN,
    AudioLanguage.lo_LA,
    AudioLanguage.la,
    AudioLanguage.lv_LV,
    AudioLanguage.lt_LT,
    AudioLanguage.lb_LU,
    AudioLanguage.mk_MK,
    AudioLanguage.mai_IN,
    AudioLanguage.mg_MG,
    AudioLanguage.ms_MY,
    AudioLanguage.ml_IN,
    AudioLanguage.mn_MN,
    AudioLanguage.ne_NP,
    AudioLanguage.nb_NO,
    AudioLanguage.nn_NO,
    AudioLanguage.or_IN,
    AudioLanguage.ps_AF,
    AudioLanguage.fa_IR,
    AudioLanguage.pt_PT,
    AudioLanguage.pa_IN,
    AudioLanguage.sr_RS,
    AudioLanguage.sd_IN,
    AudioLanguage.si_LK,
    AudioLanguage.sk_SK,
    AudioLanguage.sl_SI,
    AudioLanguage.es_LA,
    AudioLanguage.es_MX,
    AudioLanguage.sw_KE,
    AudioLanguage.sv_SE,
    AudioLanguage.ur_PK,
    # Additional languages supported by the Gemini 3.8 models
    # https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts
    AudioLanguage.ace_ID,
    AudioLanguage.ak_GH,
    AudioLanguage.as_IN,
    AudioLanguage.awa_IN,
    AudioLanguage.ba_RU,
    AudioLanguage.ban_ID,
    AudioLanguage.bem_ZM,
    AudioLanguage.bho_IN,
    AudioLanguage.bs_BA,
    AudioLanguage.ckb_IQ,
    AudioLanguage.crh_UA,
    AudioLanguage.dz_BT,
    AudioLanguage.ff_NG,
    AudioLanguage.gn_PY,
    AudioLanguage.ha_NG,
    AudioLanguage.hne_IN,
    AudioLanguage.ig_NG,
    AudioLanguage.ilo_PH,
    AudioLanguage.kk_KZ,
    AudioLanguage.km_KH,
    AudioLanguage.ks_IN,
    AudioLanguage.ky_KG,
    AudioLanguage.lg_UG,
    AudioLanguage.ln_CD,
    AudioLanguage.ltg_LV,
    AudioLanguage.lus_IN,
    AudioLanguage.min_ID,
    AudioLanguage.mni_IN,
    AudioLanguage.mt_MT,
    AudioLanguage.nso_ZA,
    AudioLanguage.ny_MW,
    AudioLanguage.oc_FR,
    AudioLanguage.pag_PH,
    AudioLanguage.prs_AF,
    AudioLanguage.rw_RW,
    AudioLanguage.so_SO,
    AudioLanguage.ss_SZ,
    AudioLanguage.st_ZA,
    AudioLanguage.tg_TJ,
    AudioLanguage.ti_ET,
    AudioLanguage.ug_CN,
    AudioLanguage.uz_UZ,
    AudioLanguage.zh_HK,
]

GEMINI_VOICES = [
    ('Zephyr', 'Bright', cloudlanguagetools.constants.Gender.Female),
    ('Puck', 'Upbeat', cloudlanguagetools.constants.Gender.Male),
    ('Charon', 'Informative', cloudlanguagetools.constants.Gender.Male),
    ('Kore', 'Firm', cloudlanguagetools.constants.Gender.Female),
    ('Fenrir', 'Excitable', cloudlanguagetools.constants.Gender.Male),
    ('Leda', 'Youthful', cloudlanguagetools.constants.Gender.Female),
    ('Orus', 'Firm', cloudlanguagetools.constants.Gender.Male),
    ('Aoede', 'Breezy', cloudlanguagetools.constants.Gender.Female),
    ('Callirrhoe', 'Easy-going', cloudlanguagetools.constants.Gender.Female),
    ('Autonoe', 'Bright', cloudlanguagetools.constants.Gender.Female),
    ('Enceladus', 'Breathy', cloudlanguagetools.constants.Gender.Male),
    ('Iapetus', 'Clear', cloudlanguagetools.constants.Gender.Male),
    ('Umbriel', 'Easy-going', cloudlanguagetools.constants.Gender.Male),
    ('Algieba', 'Smooth', cloudlanguagetools.constants.Gender.Male),
    ('Despina', 'Smooth', cloudlanguagetools.constants.Gender.Female),
    ('Erinome', 'Clear', cloudlanguagetools.constants.Gender.Female),
    ('Algenib', 'Gravelly', cloudlanguagetools.constants.Gender.Male),
    ('Rasalgethi', 'Informative', cloudlanguagetools.constants.Gender.Male),
    ('Laomedeia', 'Upbeat', cloudlanguagetools.constants.Gender.Female),
    ('Achernar', 'Soft', cloudlanguagetools.constants.Gender.Female),
    ('Alnilam', 'Firm', cloudlanguagetools.constants.Gender.Male),
    ('Schedar', 'Even', cloudlanguagetools.constants.Gender.Male),
    ('Gacrux', 'Mature', cloudlanguagetools.constants.Gender.Female),
    ('Pulcherrima', 'Forward', cloudlanguagetools.constants.Gender.Female),
    ('Achird', 'Friendly', cloudlanguagetools.constants.Gender.Male),
    ('Zubenelgenubi', 'Casual', cloudlanguagetools.constants.Gender.Male),
    ('Vindemiatrix', 'Gentle', cloudlanguagetools.constants.Gender.Female),
    ('Sadachbia', 'Lively', cloudlanguagetools.constants.Gender.Male),
    ('Sadaltager', 'Knowledgeable', cloudlanguagetools.constants.Gender.Male),
    ('Sulafat', 'Warm', cloudlanguagetools.constants.Gender.Female),
]

def get_tts_voice_list():
    """Legacy method for backwards compatibility"""
    return []

def build_tts_voice_v3(voice_name, description, gender):
    """Build a TtsVoice_v3 instance for a Gemini voice"""
    return cloudlanguagetools.ttsvoice.TtsVoice_v3(
        name=f'{voice_name} ({description})',
        voice_key={
            'name': voice_name
        },
        options=VOICE_OPTIONS,
        service=cloudlanguagetools.constants.Service.Gemini,
        gender=gender,
        audio_languages=TTS_SUPPORTED_LANGUAGES,
        service_fee=cloudlanguagetools.constants.ServiceFee.paid
    )

class GeminiService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.service = cloudlanguagetools.constants.Service.Gemini
        self.api_key = None

    def configure(self, config):
        # Gemini has its own API key, independent from the Google service
        self.api_key = config.api_key.get_secret_value()

    def get_tts_voice_list(self):
        return get_tts_voice_list()

    def get_tts_voice_list_v3(self):
        """Return list of TtsVoice_v3 instances for all Gemini voices"""
        result = []
        for voice_name, description, gender in GEMINI_VOICES:
            voice = build_tts_voice_v3(voice_name, description, gender)
            result.append(voice)
        return result

    def get_tts_audio(self, text, voice_key, options):
        """Generate TTS audio with a Gemini model, through the Gemini API generateContent endpoint."""
        voice_name = voice_key['name']
        model = options.get('model', DEFAULT_MODEL)
        audio_format = cloudlanguagetools.google_tts_common.get_audio_format(options)

        if model not in GEMINI_API_MODEL_NAMES:
            raise cloudlanguagetools.errors.InputError(
                f'Gemini TTS: unsupported model {model}, use one of {", ".join(GEMINI_API_MODEL_NAMES)}')
        if self.api_key is None:
            raise cloudlanguagetools.errors.AuthenticationError('Gemini TTS: service is not configured')

        request_body = self.build_generate_content_request(text, voice_name, options, model)
        url = GEMINI_API_URL.format(model=GEMINI_API_MODEL_NAMES[model])
        headers = cloudlanguagetools.google_tts_common.get_api_key_headers(self.api_key)

        logger.debug(f'Making Gemini generateContent TTS request: model: {model}, voice: {voice_name}, format: {audio_format.name}, body: {pprint.pformat(request_body)}')

        try:
            response = requests.post(url, headers=headers, json=request_body,
                timeout=cloudlanguagetools.constants.RequestTimeoutLong)
        except requests.exceptions.Timeout as e:
            logger.warning(f'Gemini generateContent TTS request timed out: {e}')
            raise cloudlanguagetools.errors.TimeoutError(f'Gemini TTS timed out: {str(e)}') from e
        self.raise_for_generate_content_error(response)

        audio_bytes, mime_type = self.extract_generate_content_audio(response.json())
        return self.write_generate_content_audio(audio_bytes, mime_type, audio_format)

    def build_generate_content_request(self, text, voice_name, options, model=DEFAULT_MODEL):
        prompt = options.get('prompt', '')
        # the models detect the input language automatically, only pass a
        # language code when the caller explicitly set one
        language_code = options.get('language_code')

        if model in SPEECH_METADATA_MODELS:
            # gemini 3.8: the style prompt goes in speechMetadata
            part = {'text': text}
            if prompt:
                part['speechMetadata'] = {'style': prompt}
            speech_config = {'voiceConfig': {'voice': voice_name}}
        else:
            # older models reject speechMetadata, the style is given as a natural
            # language prefix, e.g. "Say cheerfully: <text>"
            part = {'text': f'{prompt}: {text}' if prompt else text}
            speech_config = {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice_name}}}
        if language_code:
            speech_config['languageCode'] = language_code

        return {
            'contents': [{'role': 'user', 'parts': [part]}],
            'generationConfig': {
                'responseModalities': ['AUDIO'],
                'speechConfig': speech_config,
            }
        }

    def raise_for_generate_content_error(self, response):
        """Map an error HTTP response from generateContent to a cloudlanguagetools error."""
        status_code = response.status_code
        if status_code < 400:
            return

        try:
            error_data = response.json().get('error', {})
        except (ValueError, TypeError, AttributeError):
            error_data = {}
        if not isinstance(error_data, dict):
            error_data = {}
        message = error_data.get('message', response.text)

        logger.warning(f'Gemini generateContent TTS request failed with status code {status_code}: {message} | full response: {response.text}')

        if status_code == 429:
            retry_after = self.get_retry_after(error_data)
            raise cloudlanguagetools.errors.RateLimitRetryAfterError(
                f'Gemini TTS rate limit exceeded: {message}', retry_after=retry_after)
        if status_code == 400:
            raise cloudlanguagetools.errors.InputError(f'Gemini TTS error: {message}')
        if status_code in (401, 403):
            raise cloudlanguagetools.errors.AuthenticationError(
                f'Gemini TTS authentication error (is the API key a Gemini API key, allowed to call the Generative Language API?): {message}')
        if status_code in (408, 504):
            raise cloudlanguagetools.errors.TimeoutError(f'Gemini TTS timed out: {message}')
        raise cloudlanguagetools.errors.RequestError(f'Gemini TTS error (status code {status_code}): {message}')

    @staticmethod
    def get_retry_after(error_data):
        """Extract the retry delay in seconds from a google.rpc.RetryInfo error detail."""
        for detail in error_data.get('details', []):
            if detail.get('@type') == 'type.googleapis.com/google.rpc.RetryInfo':
                match = re.match(r'^(\d+)(?:\.\d+)?s$', str(detail.get('retryDelay', '')))
                if match:
                    return int(match.group(1))
        return DEFAULT_RATE_LIMIT_RETRY_AFTER

    @staticmethod
    def extract_generate_content_audio(response_data):
        """Return (audio bytes, mime type) from a generateContent response."""
        candidates = response_data.get('candidates') or []
        if len(candidates) == 0:
            logger.error(f'No candidates in Gemini generateContent response: {pprint.pformat(response_data)}')
            block_reason = (response_data.get('promptFeedback') or {}).get('blockReason')
            if block_reason:
                raise cloudlanguagetools.errors.RequestError(f'Gemini TTS request blocked: {block_reason}')
            raise cloudlanguagetools.errors.RequestError('Gemini TTS: no audio candidates in response')

        candidate = candidates[0]
        parts = (candidate.get('content') or {}).get('parts') or []
        for part in parts:
            inline_data = part.get('inlineData')
            if inline_data and inline_data.get('data'):
                return base64.b64decode(inline_data['data']), inline_data.get('mimeType', '')

        finish_reason = candidate.get('finishReason')
        logger.error(f'No audio data in Gemini generateContent response (finish reason: {finish_reason}): {pprint.pformat(response_data)}')
        raise cloudlanguagetools.errors.RequestError(f'Gemini TTS: no audio data in response (finish reason: {finish_reason})')

    @staticmethod
    def write_generate_content_audio(audio_bytes, mime_type, audio_format):
        """Write the generateContent audio to a temp file and transcode it to the requested format."""
        audio_temp_file = tempfile.NamedTemporaryFile(prefix='clt_gemini_audio_', suffix='.wav')
        with open(audio_temp_file.name, 'wb') as f:
            f.write(audio_bytes)

        if not audio_bytes.startswith(b'RIFF'):
            # headerless PCM (audio/L16;codec=pcm;rate=24000), wrap it in a WAV container
            sample_rate = GENERATE_CONTENT_SAMPLE_RATE
            rate_match = re.search(r'rate=(\d+)', mime_type)
            if rate_match:
                sample_rate = int(rate_match.group(1))
            logger.debug(f'wrapping headerless PCM response ({mime_type}) in a WAV container at {sample_rate} Hz')
            audio_temp_file = cloudlanguagetools.audio_processing.wrap_pcm_data_wave(
                audio_temp_file, num_channels=1, sample_width=2, framerate=sample_rate)

        return cloudlanguagetools.google_tts_common.convert_wav_to_format(audio_temp_file, audio_format)
