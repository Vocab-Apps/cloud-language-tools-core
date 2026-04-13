import requests
import tempfile
import logging
import pprint
import json
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

    def _extract_error_message(self, data):
        """Try common error keys, fall back to full dump."""
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            for key in ('message', 'error', 'detail', 'error_message'):
                if key in data:
                    return self._extract_error_message(data[key])
        return json.dumps(data)

    def _get_response_error_message(self, response):
        """Extract error message from an HTTP error response. Never raises."""
        try:
            error_data = response.json()
            return self._extract_error_message(error_data)
        except (ValueError, TypeError):
            return response.text

    def get_tts_audio_base_post_request(self, url, **kwargs):
        try:
            kwargs['timeout'] = cloudlanguagetools.constants.RequestTimeout
            logger.debug(f'{self.get_service_name()} TTS request - URL: {url}, kwargs: {pprint.pformat(kwargs)}')
            response = self.post_request(url, **kwargs)
            if response.status_code == 429:
                msg = self._get_response_error_message(response)
                logger.warning(f'{self.get_service_name()} rate limited (429): {msg}')
                raise cloudlanguagetools.errors.RateLimitError(f'{self.get_service_name()}: {msg}')
            if response.status_code >= 400:
                msg = self._get_response_error_message(response)
                logger.warning(f'{self.get_service_name()} audio request failed with status code {response.status_code}: {msg}')
                raise cloudlanguagetools.errors.RequestError(f'{self.get_service_name()}: {msg}')
            response.raise_for_status()
            output_temp_file = tempfile.NamedTemporaryFile(prefix='clt_audio_')
            output_temp_filename = output_temp_file.name            
            with open(output_temp_filename, 'wb') as audio:
                audio.write(response.content)
            return output_temp_file            
        except requests.exceptions.ReadTimeout as exception:
            raise cloudlanguagetools.errors.TimeoutError(f'timeout while retrieving {self.get_service_name()} audio') from exception
        except cloudlanguagetools.errors.TransientError:
            raise
        except cloudlanguagetools.errors.PermanentError:
            raise
        except Exception as exception:
            error_message = f'could not retrieve audio from {self.get_service_name()}: {str(exception)}'
            raise cloudlanguagetools.errors.RequestError(error_message) from exception

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