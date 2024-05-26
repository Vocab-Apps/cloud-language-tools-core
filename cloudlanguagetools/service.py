import requests
import tempfile
import logging
from typing import List

import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice

logger = logging.getLogger(__name__)

class Service():
    def __init__(self):
        pass

    def get_service_name(self):
        return self.service.name

    def post_request(self, url, **kwargs):
        kwargs['timeout'] = cloudlanguagetools.constants.RequestTimeout
        return requests.post(url, **kwargs)

    def get_tts_audio_base_post_request(self, url, **kwargs):
        try:
            response = self.post_request(url, **kwargs)
            response.raise_for_status()
            output_temp_file = tempfile.NamedTemporaryFile()
            output_temp_filename = output_temp_file.name            
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file            
        except requests.exceptions.ReadTimeout as exception:
            raise cloudlanguagetools.errors.TimeoutError(f'timeout while retrieving {self.get_service_name()} audio')
        except Exception as exception:
            error_message = f'could not retrieve audio from {self.get_service_name()}'
            logger.exception(error_message)
            raise cloudlanguagetools.errors.RequestError(error_message)

    # used for pre-loading models
    def load_data(self):
        pass

    def get_tts_voice_list(self):
        return []

    def get_tts_voice_list_v3(self) -> List[cloudlanguagetools.ttsvoice.TtsVoice_v3]:
        # the default implementation will convert list of voices to list of TtsVoice_v3
        voices = self.get_tts_voice_list()
        voices_v3 = [cloudlanguagetools.ttsvoice.TtsVoice_v3(
            name=voice.get_voice_shortname(),
            voice_key=voice.get_voice_key(),
            options=voice.get_options(),
            service=voice.service,
            gender=voice.get_gender(),
            audio_languages=[voice.audio_language],
            service_fee=voice.service_fee
        ) for voice in voices]
        return voices_v3

    def get_translation_language_list(self):
        return []

    def get_transliteration_language_list(self):
        return []

    def get_tokenization_options(self):
        return []

    def get_dictionary_lookup_list(self):
        return []