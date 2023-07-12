import sys
import os
import logging
import tempfile
import pydub
import pasimple
import wave
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cloudlanguagetools.servicemanager
import cloudlanguagetools.chatmodel


class InteractiveChatbot():
    def __init__(self):
        self.manager = cloudlanguagetools.servicemanager.ServiceManager()
        self.manager.configure_default()
        self.chat_model = cloudlanguagetools.chatmodel.ChatModel(self.manager)
        self.chat_model.set_send_message_callback(self.received_message, self.received_audio)

    def received_message(self, message: str):
        print(message)

    def received_audio(self, audio_tempfile: tempfile.NamedTemporaryFile):
        print(f'received audio')
        sound = pydub.AudioSegment.from_mp3(audio_tempfile.name)
        wav_tempfile = tempfile.NamedTemporaryFile(prefix='clt_interactivechatbot', suffix='.wav')
        sound.export(wav_tempfile.name, format="wav")
        
        # Read a .wav file with its attributes
        with wave.open(wav_tempfile.name, 'rb') as wave_file:
            format = pasimple.width2format(wave_file.getsampwidth())
            channels = wave_file.getnchannels()
            sample_rate = wave_file.getframerate()
            audio_data = wave_file.readframes(wave_file.getnframes())

        # Play the file via PulseAudio
        with pasimple.PaSimple(pasimple.PA_STREAM_PLAYBACK, format, channels, sample_rate) as pa:
            pa.write(audio_data)
            pa.drain()        

    def run(self):
        while True:
            user_input = input("Enter a message:")
            self.chat_model.process_message(user_input)
            print(self.chat_model.status())


if __name__ == '__main__':
    logger = logging.getLogger()
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])        
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.INFO)    

    chatbot = InteractiveChatbot()
    chatbot.run()