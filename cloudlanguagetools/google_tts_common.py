"""Audio format handling shared by the Google and Gemini services.

Both services synthesize through the Google Cloud Text-to-Speech API, so they
accept the same set of output formats and post-process the response the same way.
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
