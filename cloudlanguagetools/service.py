import requests
import tempfile
import logging
import pprint
from typing import List, Dict

import cloudlanguagetools.constants
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.options

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
            kwargs['timeout'] = cloudlanguagetools.constants.RequestTimeout
            logger.debug(f'{self.get_service_name()} TTS request - URL: {url}, kwargs: {pprint.pformat(kwargs)}')
            response = self.post_request(url, **kwargs)
            if response.status_code >= 400:
                logger.error(f'{self.get_service_name()} audio request failed with status code {response.status_code}: {response.content}')
            response.raise_for_status()
            output_temp_file = tempfile.NamedTemporaryFile(prefix='clt_audio_')
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

    def get_request_audio_format(self, format_map: Dict, options: Dict, default_format: cloudlanguagetools.options.AudioFormat):
        response_format_str = options.get(cloudlanguagetools.options.AUDIO_FORMAT_PARAMETER, 
            default_format.name)
        response_format = cloudlanguagetools.options.AudioFormat[response_format_str]
        response_format_parameter = format_map[response_format]
        return response_format_parameter, response_format

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