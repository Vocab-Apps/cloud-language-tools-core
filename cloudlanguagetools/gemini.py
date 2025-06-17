import tempfile
import logging
import wave
import os
import pprint
from typing import List

from google import genai
from google.genai import types
from pydub import AudioSegment

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.options
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.errors
from cloudlanguagetools.languages import AudioLanguage
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gemini-2.5-flash-preview-tts'

# note the rate limits:
# https://ai.google.dev/gemini-api/docs/rate-limits#tier-1

VOICE_OPTIONS = {
    'model': {
        'type': cloudlanguagetools.options.ParameterType.list.name,
        'values': [
            'gemini-2.5-flash-preview-tts',
            'gemini-2.5-pro-preview-tts'
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

# Gemini TTS supports 24+ languages
TTS_SUPPORTED_LANGUAGES = [
    AudioLanguage.en_US,
    AudioLanguage.fr_FR,
    AudioLanguage.de_DE,
    AudioLanguage.es_ES,
    AudioLanguage.it_IT,
    AudioLanguage.pt_BR,
    AudioLanguage.ru_RU,
    AudioLanguage.ja_JP,
    AudioLanguage.ko_KR,
    AudioLanguage.zh_CN,
    AudioLanguage.hi_IN,
    AudioLanguage.ar_XA,
    AudioLanguage.nl_NL,
    AudioLanguage.pl_PL,
    AudioLanguage.sv_SE,
    AudioLanguage.da_DK,
    AudioLanguage.nb_NO,
    AudioLanguage.fi_FI,
    AudioLanguage.tr_TR,
    AudioLanguage.th_TH,
    AudioLanguage.vi_VN,
    AudioLanguage.uk_UA,
    AudioLanguage.cs_CZ,
    AudioLanguage.hu_HU
]

GEMINI_VOICES = [
    ('Zephyr', 'Bright', cloudlanguagetools.constants.Gender.Any),
    ('Puck', 'Upbeat', cloudlanguagetools.constants.Gender.Any),
    ('Charon', 'Informative', cloudlanguagetools.constants.Gender.Any),
    ('Kore', 'Firm', cloudlanguagetools.constants.Gender.Any),
    ('Fenrir', 'Excitable', cloudlanguagetools.constants.Gender.Any),
    ('Leda', 'Youthful', cloudlanguagetools.constants.Gender.Any),
    ('Orus', 'Firm', cloudlanguagetools.constants.Gender.Any),
    ('Aoede', 'Breezy', cloudlanguagetools.constants.Gender.Any),
    ('Callirrhoe', 'Easy-going', cloudlanguagetools.constants.Gender.Any),
    ('Autonoe', 'Bright', cloudlanguagetools.constants.Gender.Any),
    ('Enceladus', 'Breathy', cloudlanguagetools.constants.Gender.Any),
    ('Iapetus', 'Clear', cloudlanguagetools.constants.Gender.Any),
    ('Umbriel', 'Easy-going', cloudlanguagetools.constants.Gender.Any),
    ('Algieba', 'Smooth', cloudlanguagetools.constants.Gender.Any),
    ('Despina', 'Smooth', cloudlanguagetools.constants.Gender.Any),
    ('Erinome', 'Clear', cloudlanguagetools.constants.Gender.Any),
    ('Algenib', 'Gravelly', cloudlanguagetools.constants.Gender.Any),
    ('Rasalgethi', 'Informative', cloudlanguagetools.constants.Gender.Any),
    ('Laomedeia', 'Upbeat', cloudlanguagetools.constants.Gender.Any),
    ('Achernar', 'Soft', cloudlanguagetools.constants.Gender.Any),
    ('Alnilam', 'Firm', cloudlanguagetools.constants.Gender.Any),
    ('Schedar', 'Even', cloudlanguagetools.constants.Gender.Any),
    ('Gacrux', 'Mature', cloudlanguagetools.constants.Gender.Any),
    ('Pulcherrima', 'Forward', cloudlanguagetools.constants.Gender.Any),
    ('Achird', 'Friendly', cloudlanguagetools.constants.Gender.Any),
    ('Zubenelgenubi', 'Casual', cloudlanguagetools.constants.Gender.Any),
    ('Vindemiatrix', 'Gentle', cloudlanguagetools.constants.Gender.Any),
    ('Sadachbia', 'Lively', cloudlanguagetools.constants.Gender.Any),
    ('Sadaltager', 'Knowledgeable', cloudlanguagetools.constants.Gender.Any),
    ('Sulafat', 'Warm', cloudlanguagetools.constants.Gender.Any),
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

def convert_pcm_to_audio_file(audio_data, audio_format):
    """Convert PCM audio data to the requested format and return a NamedTemporaryFile.
    
    Args:
        audio_data: Raw PCM audio data from Gemini (24kHz, 16-bit, mono)
        audio_format: Target format ('wav', 'mp3', 'ogg_opus')
        
    Returns:
        tempfile.NamedTemporaryFile containing the converted audio
        
    Note:
        Gemini returns 24kHz, mono, 16-bit PCM audio data.
        Ref: https://ai.google.dev/gemini-api/docs/speech-generation
    """
    
    # First create a temporary WAV file from PCM data
    wav_temp_file = tempfile.NamedTemporaryFile(prefix='clt_gemini_wav_', suffix='.wav', delete=False)
    with wave.open(wav_temp_file.name, "wb") as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(24000)  # 24kHz
        wf.writeframes(audio_data)
    
    if audio_format == 'wav':
        # For WAV, just return the file we already created
        output_temp_file = tempfile.NamedTemporaryFile(prefix='clt_gemini_audio_', suffix='.wav')
        with open(wav_temp_file.name, 'rb') as src:
            output_temp_file.write(src.read())
        output_temp_file.seek(0)
        os.unlink(wav_temp_file.name)
        return output_temp_file
    
    # For other formats, convert using pydub
    audio_segment = AudioSegment.from_wav(wav_temp_file.name)
    
    if audio_format == 'ogg_opus':
        # Convert to OGG Opus
        output_temp_file = tempfile.NamedTemporaryFile(prefix='clt_gemini_audio_', suffix='.ogg', delete=False)
        audio_segment.export(output_temp_file.name, format="ogg", codec="libopus")
        suffix = '.ogg'
    else:  # Default to MP3
        # Convert to MP3
        output_temp_file = tempfile.NamedTemporaryFile(prefix='clt_gemini_audio_', suffix='.mp3', delete=False)
        audio_segment.export(output_temp_file.name, format="mp3")
        suffix = '.mp3'
    
    # Clean up the intermediate WAV file
    os.unlink(wav_temp_file.name)
    
    # Reopen as NamedTemporaryFile for compatibility with existing code
    final_temp_file = tempfile.NamedTemporaryFile(prefix='clt_gemini_audio_', suffix=suffix)
    with open(output_temp_file.name, 'rb') as src:
        final_temp_file.write(src.read())
    final_temp_file.seek(0)
    
    # Clean up the intermediate output file
    os.unlink(output_temp_file.name)
    
    return final_temp_file

class GeminiService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.service = cloudlanguagetools.constants.Service.Gemini
        self.api_key_required = True
        self.client = None

    def configure(self, config):
        self.config = config
        self.api_key = config.get('api_key', None)
        logger.debug(f'Configuring Gemini service with api_key: {self.api_key[:20] if self.api_key else None}...')
        if self.api_key is None:
            raise cloudlanguagetools.errors.AuthenticationError('api_key not set')
        
        # Initialize the genai client
        self.client = genai.Client(api_key=self.api_key)

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
        """Generate TTS audio using Google Gemini API via google-genai SDK"""
        
        # Extract voice name from voice_key dict
        if isinstance(voice_key, dict) and 'name' in voice_key:
            voice_name = voice_key['name']
        else:
            raise cloudlanguagetools.errors.RequestError(f'Invalid voice key format: {voice_key}')
        
        # Get model and format from options
        model = options.get('model', DEFAULT_MODEL)
        audio_format = options.get('audio_format', 'mp3')
        
        try:
            logger.debug(f'Making Gemini TTS request with voice: {voice_name}, model: {model}, format: {audio_format}')
            
            # Generate content with audio response using the SDK
            response = self.client.models.generate_content(
                model=model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                )
            )
            
            # Extract audio data from response
            if not response.candidates or len(response.candidates) == 0:
                # This can happen due to safety filters, rate limits, or API errors
                logger.error(f'No candidates in Gemini response. Full response: {response}')
                raise cloudlanguagetools.errors.RequestError('No audio candidates in response')
            
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                # This might occur if content was filtered or if there's an API issue
                # Check if there's a finish_reason that might explain why
                finish_reason = getattr(candidate, 'finish_reason', None)
                logger.error(f'No content parts in response. Finish reason: {finish_reason}, Candidate: {candidate} response: {pprint.pformat(response)}')
                
                # Provide more specific error messages based on finish_reason
                if finish_reason:
                    finish_reason_str = str(finish_reason)
                    if 'OTHER' in finish_reason_str:
                        error_msg = f'No content parts in response (finish_reason: {finish_reason}) - This is often a transient API issue, consider retrying'
                    elif 'SAFETY' in finish_reason_str:
                        error_msg = f'No content parts in response (finish_reason: {finish_reason}) - Content was blocked by safety filters'
                    elif 'RECITATION' in finish_reason_str:
                        error_msg = f'No content parts in response (finish_reason: {finish_reason}) - Content was blocked due to recitation/copyright detection'
                    elif 'BLOCKLIST' in finish_reason_str:
                        error_msg = f'No content parts in response (finish_reason: {finish_reason}) - Content was blocked by terminology blocklist'
                    else:
                        error_msg = f'No content parts in response (finish_reason: {finish_reason})'
                else:
                    error_msg = 'No content parts in response'
                
                raise cloudlanguagetools.errors.RequestError(error_msg)
            
            # Find the audio part
            audio_part = None
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    audio_part = part
                    break
            
            if audio_part is None or not audio_part.inline_data:
                raise cloudlanguagetools.errors.RequestError('No audio data found in response')
            
            # Get the raw audio data (PCM format from Gemini)
            audio_data = audio_part.inline_data.data
            
            # Convert audio format as requested using the helper function
            return convert_pcm_to_audio_file(audio_data, audio_format)
            
        except Exception as e:
            error_msg = f'Error while retrieving Gemini TTS audio: {str(e)}'
            logger.exception(error_msg)
            raise cloudlanguagetools.errors.RequestError(error_msg)