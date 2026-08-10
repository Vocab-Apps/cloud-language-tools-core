import os
import sys
import math
import wave
import struct
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.audio_processing
import cloudlanguagetools.constants
import audio_utils


def build_wav_temp_file(sample_rate=24000, duration_seconds=1) -> tempfile.NamedTemporaryFile:
    # a real 16-bit mono WAV, matching what Google/Gemini LINEAR16 returns
    wav_temp_file = tempfile.NamedTemporaryFile(prefix='clt_test_wav_', suffix='.wav')
    w = wave.open(wav_temp_file.name, 'wb')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sample_rate)
    num_frames = sample_rate * duration_seconds
    w.writeframes(b''.join(
        struct.pack('<h', int(30000 * math.sin(2 * math.pi * 440 * n / sample_rate)))
        for n in range(num_frames)))
    w.close()
    return wav_temp_file


class TestEncodeWavToMp3(unittest.TestCase):
    """Exercises the WAV->mp3 re-encode used by the Google/Gemini services.

    Runnable without API keys: it only needs pydub/ffmpeg and libmagic, which the
    audio test suite already depends on.
    """

    def test_reencodes_to_default_bitrate(self):
        wav_temp_file = build_wav_temp_file()
        mp3_temp_file = cloudlanguagetools.audio_processing.encode_wav_to_mp3(wav_temp_file)

        self.assertTrue(audio_utils.is_mp3_format(mp3_temp_file.name))
        # constants.AUDIO_MP3_ENCODE_BITRATE is '128k'
        self.assertEqual(audio_utils.get_mp3_bitrate_kbps(mp3_temp_file.name), 128)

    def test_respects_explicit_bitrate(self):
        # 192 kbps requires an MPEG-1 sample rate (44.1/48 kHz); at the 24 kHz
        # (MPEG-2) rate used above the encoder caps at 160 kbps.
        wav_temp_file = build_wav_temp_file(sample_rate=44100)
        mp3_temp_file = cloudlanguagetools.audio_processing.encode_wav_to_mp3(wav_temp_file, bitrate='192k')

        self.assertTrue(audio_utils.is_mp3_format(mp3_temp_file.name))
        self.assertEqual(audio_utils.get_mp3_bitrate_kbps(mp3_temp_file.name), 192)


if __name__ == '__main__':
    unittest.main()
