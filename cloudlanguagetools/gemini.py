import tempfile
import logging
import pprint
from typing import List

from google.api_core.client_options import ClientOptions
import google.cloud.texttospeech
import google.api_core.exceptions

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.errors
from cloudlanguagetools.languages import AudioLanguage

logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gemini-2.5-flash-tts'

VOICE_OPTIONS = {
    'model': {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': [
            'gemini-2.5-flash-tts',
            'gemini-2.5-pro-tts',
            'gemini-2.5-flash-lite-preview-tts',
            'gemini-3.1-flash-tts-preview',
        ],
        'default': DEFAULT_MODEL
    },
    cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER: {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': [
            cloudlanguagetools.options.AudioFormat.mp3.name,
            cloudlanguagetools.options.AudioFormat.wav.name,
            cloudlanguagetools.options.AudioFormat.ogg_opus.name
        ],
        'default': cloudlanguagetools.options.AudioFormat.mp3.name
    }
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

    def configure(self, config):
        # we rely on os.environ['GOOGLE_APPLICATION_CREDENTIALS'] from the Google service
        pass

    def get_client(self):
        return google.cloud.texttospeech.TextToSpeechClient(
            client_options=ClientOptions(api_endpoint='texttospeech.googleapis.com')
        )

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
        """Generate TTS audio using Cloud Text-to-Speech API with Gemini models"""

        voice_name = voice_key['name']
        model = options.get('model', DEFAULT_MODEL)

        audio_format_str = options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, cloudlanguagetools.options.AudioFormat.mp3.name)
        audio_format = cloudlanguagetools.options.AudioFormat[audio_format_str]

        audio_format_map = {
            cloudlanguagetools.options.AudioFormat.mp3: google.cloud.texttospeech.AudioEncoding.MP3,
            cloudlanguagetools.options.AudioFormat.ogg_opus: google.cloud.texttospeech.AudioEncoding.OGG_OPUS,
            cloudlanguagetools.options.AudioFormat.wav: google.cloud.texttospeech.AudioEncoding.LINEAR16,
        }

        try:
            client = self.get_client()

            voice = google.cloud.texttospeech.VoiceSelectionParams(
                language_code='en-US',
                name=voice_name,
                model_name=model,
            )

            audio_config = google.cloud.texttospeech.AudioConfig(
                audio_encoding=audio_format_map[audio_format],
            )

            input_text = google.cloud.texttospeech.SynthesisInput(text=text)

            logger.debug(f'Making Gemini TTS request with voice: {voice_name}, model: {model}, format: {audio_format_str}')

            response = client.synthesize_speech(
                request={"input": input_text, "voice": voice, "audio_config": audio_config}
            )

            output_temp_file = tempfile.NamedTemporaryFile()
            with open(output_temp_file.name, "wb") as out:
                out.write(response.audio_content)

            return output_temp_file

        except google.api_core.exceptions.ResourceExhausted as e:
            retry_after = None
            for detail in e.details:
                if hasattr(detail, 'retry_delay'):
                    retry_after = detail.retry_delay.seconds
                    break
            if retry_after is None:
                retry_after = 60
            logger.warning(f'Gemini TTS rate limit hit (retry_after={retry_after}s): {e}')
            raise cloudlanguagetools.errors.RateLimitRetryAfterError(str(e), retry_after=retry_after)
        except google.api_core.exceptions.GoogleAPICallError as e:
            logger.warning(f'Gemini TTS error: {e}, code: {e.code}')
            raise cloudlanguagetools.errors.RequestError(f'Gemini TTS error: {str(e)}') from e
