import requests
import tempfile
import logging

import cloudlanguagetools.constants

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

    def get_translation_language_list(self):
        return []

    def get_transliteration_language_list(self):
        return []

    def get_tokenization_options(self):
        return []

    def get_dictionary_lookup_list(self):
        return []