"""Audio format handling shared by the Google and Gemini services.

Both services accept the same set of output formats. Cloud Text-to-Speech
responses (Google voices, Gemini 2.5/3.1 models) are post-processed with
write_audio_response(). Gemini 3.8 models go through the Gemini Enterprise
generateContent endpoint, which only returns WAV, so their output is transcoded
locally with convert_wav_to_format().
"""
import tempfile
import logging

import google.cloud.texttospeech

import cloudlanguagetools.options
import cloudlanguagetools.audio_processing
from cloudlanguagetools.options import AudioFormat

logger = logging.getLogger(__name__)

DEFAULT_AUDIO_FORMAT = AudioFormat.mp3

# the native mp3 encoding is a fixed 32 kbps on Chirp 3 HD and Gemini voices
# (64 kbps on older voice families), which is noticeably lossy. for mp3_hq we
# request lossless LINEAR16 and re-encode locally at a higher bitrate instead.
AUDIO_ENCODING_MAP = {
    AudioFormat.mp3: google.cloud.texttospeech.AudioEncoding.MP3,
    AudioFormat.mp3_hq: google.cloud.texttospeech.AudioEncoding.LINEAR16,
    AudioFormat.ogg_opus: google.cloud.texttospeech.AudioEncoding.OGG_OPUS,
    AudioFormat.wav: google.cloud.texttospeech.AudioEncoding.LINEAR16,
}

# the 'format' entry to include in a voice's options
AUDIO_FORMAT_OPTION = {
    'type': cloudlanguagetools.options.ParameterType.list.name,
    'values': [audio_format.name for audio_format in AUDIO_ENCODING_MAP.keys()],
    'default': DEFAULT_AUDIO_FORMAT.name
}

def get_audio_format(options) -> AudioFormat:
    audio_format_str = options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, DEFAULT_AUDIO_FORMAT.name)
    return AudioFormat[audio_format_str]

def get_audio_encoding(audio_format: AudioFormat) -> google.cloud.texttospeech.AudioEncoding:
    return AUDIO_ENCODING_MAP[audio_format]

def write_audio_response(audio_content: bytes, audio_format: AudioFormat) -> tempfile.NamedTemporaryFile:
    """Write the synthesis response to a temp file, re-encoding it when needed."""
    output_temp_file = tempfile.NamedTemporaryFile(prefix='clt_audio_')
    with open(output_temp_file.name, 'wb') as out:
        out.write(audio_content)

    if audio_format == AudioFormat.mp3_hq:
        # we requested lossless LINEAR16, re-encode it to mp3 at our target bitrate
        logger.debug('re-encoding LINEAR16 response to high quality mp3')
        output_temp_file = cloudlanguagetools.audio_processing.encode_wav_to_mp3(output_temp_file)

    return output_temp_file


def convert_wav_to_format(wav_temp_file: tempfile.NamedTemporaryFile, audio_format: AudioFormat) -> tempfile.NamedTemporaryFile:
    """Transcode a WAV temp file to the requested format.

    Used for endpoints that only return WAV (Gemini generateContent). There is no
    native mp3 there, so both mp3 and mp3_hq are encoded locally at the mp3_hq bitrate.
    """
    if audio_format == AudioFormat.wav:
        return wav_temp_file
    if audio_format in (AudioFormat.mp3, AudioFormat.mp3_hq):
        logger.debug('encoding WAV response to mp3')
        return cloudlanguagetools.audio_processing.encode_wav_to_mp3(wav_temp_file)
    if audio_format == AudioFormat.ogg_opus:
        logger.debug('encoding WAV response to ogg opus')
        return cloudlanguagetools.audio_processing.encode_wav_to_ogg_opus(wav_temp_file)
    raise ValueError(f'unsupported audio format: {audio_format}')
