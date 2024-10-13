import wave
import tempfile

# audio utilities


# take PCM audio and wrap it in a WAV container
def wrap_pcm_data_wave(audio_temp_file: tempfile.NamedTemporaryFile,
        num_channels,
        sample_width,
        framerate) -> tempfile.NamedTemporaryFile:
    # read the audio data
    f = open(audio_temp_file.name, 'rb')
    data = f.read()
    f.close()

    wav_frames = []
    wav_frames.append(data)

    wav_audio_temp_file = tempfile.NamedTemporaryFile(prefix='clt_wav_audio_', suffix='.wav')

    WAVEFORMAT = wave.open(wav_audio_temp_file.name,'wb')
    WAVEFORMAT.setnchannels(num_channels) # one channel, mono
    WAVEFORMAT.setsampwidth(sample_width) # Polly's output is a stream of 16-bits (2 bytes) samples
    WAVEFORMAT.setframerate(framerate)
    WAVEFORMAT.writeframes(b''.join(wav_frames))
    WAVEFORMAT.close()    
    
    return wav_audio_temp_file