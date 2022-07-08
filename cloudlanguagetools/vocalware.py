import requests
import urllib
import hashlib
import tempfile
import time
import logging

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

logger = logging.getLogger(__name__)

class VocalWareVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, audio_language, name, gender, language_id, voice_id, engine_id):
        self.service = cloudlanguagetools.constants.Service.VocalWare
        self.audio_language = audio_language
        self.name = name
        self.gender = gender
        self.language_id = language_id
        self.voice_id = voice_id
        self.engine_id = engine_id

    def get_voice_key(self):
        return {
            'language_id': self.language_id,
            'voice_id': self.voice_id,
            'engine_id': self.engine_id
        }

    def get_voice_shortname(self):
        return f'{self.name}'

    def get_options(self):
        return {}


class VocalWareService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        self.secret_phrase = config['secret_phrase']
        self.account_id = config['account_id']
        self.api_id = config['api_id']

    def get_translation(self, text, from_language_key, to_language_key):
        raise cloudlanguagetools.errors.RequestError('not supported')

    def get_tts_audio(self, text, voice_key, options):
        output_temp_file = tempfile.NamedTemporaryFile()
        output_temp_filename = output_temp_file.name

        urlencoded_text = urllib.parse.unquote_plus(text)

        # checksum calculation
        # CS = md5 (EID + LID + VID + TXT + EXT + FX_TYPE + FX_LEVEL + ACC + API+ SESSION + HTTP_ERR + SECRET PHRASE)
        checksum_input = f"""{voice_key['engine_id']}{voice_key['language_id']}{voice_key['voice_id']}{text}{self.account_id}{self.api_id}{self.secret_phrase}"""
        checksum = hashlib.md5(checksum_input.encode('utf-8')).hexdigest()

        url_parameters = f"""EID={voice_key['engine_id']}&LID={voice_key['language_id']}&VID={voice_key['voice_id']}&TXT={urlencoded_text}&ACC={self.account_id}&API={self.api_id}&CS={checksum}"""
        url = f"""http://www.vocalware.com/tts/gen.php?{url_parameters}"""

        retry_count = 3
        while retry_count > 0:
            logger.debug(f'retrieving url {url}, retry_count: {retry_count}')
            try:
                response = requests.get(url, timeout=cloudlanguagetools.constants.RequestTimeout)
                logger.debug(f'response.status_code: {response.status_code}')
                has_timeout_response_header = False
                if '408 Request Timeout' in response.headers.get('X-Error', ''):
                    logger.warn(f"found timeout in response header: {response.headers['X-Error']}, {response.headers['X-ErrorLine']}")
                    has_timeout_response_header = True
                if response.status_code == 200 and has_timeout_response_header == False:
                    with open(output_temp_filename, 'wb') as audio:
                        audio.write(response.content)
                    return output_temp_file
            except requests.exceptions.ConnectionError as exception:
                pass # allow the retry logic to proceed
            retry_count -= 1
            time.sleep(1)

        response_data = response.content
        error_message = f'Status code: {response.status_code}: {response_data}'

        # reformat certain error messages
        if response.status_code == 503:
            error_message = f'VocalWare service temporarily unavailable (503)'

        raise cloudlanguagetools.errors.RequestError(error_message)

    def get_tts_voice_list(self):
        # returns list of TtSVoice
        return [
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Susan', cloudlanguagetools.constants.Gender.Female, 1, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Dave', cloudlanguagetools.constants.Gender.Male, 1, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Kenneth', cloudlanguagetools.constants.Gender.Male, 1, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_GB, 'Elizabeth', cloudlanguagetools.constants.Gender.Female, 1, 4, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_GB, 'Simon', cloudlanguagetools.constants.Gender.Male, 1, 5, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_GB, 'Catherine', cloudlanguagetools.constants.Gender.Female, 1, 6, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Allison', cloudlanguagetools.constants.Gender.Female, 1, 7, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Steven', cloudlanguagetools.constants.Gender.Male, 1, 8, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_AU, 'Alan', cloudlanguagetools.constants.Gender.Male, 1, 9, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_AU, 'Grace', cloudlanguagetools.constants.Gender.Female, 1, 10, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_IN, 'Veena', cloudlanguagetools.constants.Gender.Female, 1, 11, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_ES, 'Carmen', cloudlanguagetools.constants.Gender.Female, 2, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_ES, 'Juan', cloudlanguagetools.constants.Gender.Male, 2, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_LA, 'Francisca', cloudlanguagetools.constants.Gender.Female, 2, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_LA, 'Diego', cloudlanguagetools.constants.Gender.Male, 2, 4, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_MX, 'Esperanza', cloudlanguagetools.constants.Gender.Female, 2, 5, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_ES, 'Jorge', cloudlanguagetools.constants.Gender.Male, 2, 6, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_US, 'Carlos', cloudlanguagetools.constants.Gender.Male, 2, 7, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_US, 'Soledad', cloudlanguagetools.constants.Gender.Female, 2, 8, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_ES, 'Leonor', cloudlanguagetools.constants.Gender.Female, 2, 9, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_US, 'Ximena', cloudlanguagetools.constants.Gender.Female, 2, 10, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.de_DE, 'Ulrike', cloudlanguagetools.constants.Gender.Female, 3, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.de_DE, 'Stefan', cloudlanguagetools.constants.Gender.Male, 3, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.de_DE, 'Katrin', cloudlanguagetools.constants.Gender.Female, 3, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Sophie', cloudlanguagetools.constants.Gender.Female, 4, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Bernard', cloudlanguagetools.constants.Gender.Male, 4, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Jolie', cloudlanguagetools.constants.Gender.Female, 4, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Florence', cloudlanguagetools.constants.Gender.Female, 4, 4, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_CA, 'Charlotte', cloudlanguagetools.constants.Gender.Female, 4, 5, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_CA, 'Olivier', cloudlanguagetools.constants.Gender.Male, 4, 6, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ca_ES, 'Montserrat', cloudlanguagetools.constants.Gender.Female, 5, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ca_ES, 'Jordi', cloudlanguagetools.constants.Gender.Male, 5, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ca_ES, 'Empar', cloudlanguagetools.constants.Gender.Female, 5, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_BR, 'Gabriela', cloudlanguagetools.constants.Gender.Female, 6, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_PT, 'Amalia', cloudlanguagetools.constants.Gender.Female, 6, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_PT, 'Eusebio', cloudlanguagetools.constants.Gender.Male, 6, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_BR, 'Fernanda', cloudlanguagetools.constants.Gender.Female, 6, 4, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_BR, 'Felipe', cloudlanguagetools.constants.Gender.Male, 6, 5, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Paola', cloudlanguagetools.constants.Gender.Female, 7, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Silvana', cloudlanguagetools.constants.Gender.Female, 7, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Valentina', cloudlanguagetools.constants.Gender.Female, 7, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Fabio', cloudlanguagetools.constants.Gender.Male, 7, 4, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Luca', cloudlanguagetools.constants.Gender.Male, 7, 5, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Marcello', cloudlanguagetools.constants.Gender.Male, 7, 6, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Raffaele', cloudlanguagetools.constants.Gender.Male, 7, 7, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Matteo', cloudlanguagetools.constants.Gender.Male, 7, 8, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Giulia', cloudlanguagetools.constants.Gender.Female, 7, 9, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Federica', cloudlanguagetools.constants.Gender.Female, 7, 10, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.el_GR, 'Afroditi', cloudlanguagetools.constants.Gender.Female, 8, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.el_GR, 'Artemis', cloudlanguagetools.constants.Gender.Female, 8, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.el_GR, 'Nikos', cloudlanguagetools.constants.Gender.Male, 8, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.sv_SE, 'Annika', cloudlanguagetools.constants.Gender.Female, 9, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.sv_SE, 'Sven', cloudlanguagetools.constants.Gender.Male, 9, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_CN, 'Linlin', cloudlanguagetools.constants.Gender.Female, 10, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_CN, 'Lisheng', cloudlanguagetools.constants.Gender.Female, 10, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nl_NL, 'Willem', cloudlanguagetools.constants.Gender.Male, 11, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nl_NL, 'Saskia', cloudlanguagetools.constants.Gender.Female, 11, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pl_PL, 'Zosia', cloudlanguagetools.constants.Gender.Female, 14, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pl_PL, 'Krzysztof', cloudlanguagetools.constants.Gender.Male, 14, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.gl_ES, 'Carmela', cloudlanguagetools.constants.Gender.Female, 15, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.tr_TR, 'Kerem', cloudlanguagetools.constants.Gender.Male, 16, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.tr_TR, 'Zeynep', cloudlanguagetools.constants.Gender.Female, 16, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.tr_TR, 'Selin', cloudlanguagetools.constants.Gender.Female, 16, 3, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ca_ES, 'Empar', cloudlanguagetools.constants.Gender.Female, 17, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.da_DK, 'Frida', cloudlanguagetools.constants.Gender.Female, 19, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.da_DK, 'Magnus', cloudlanguagetools.constants.Gender.Male, 19, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nb_NO, 'Vilde', cloudlanguagetools.constants.Gender.Female, 20, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nb_NO, 'Henrik', cloudlanguagetools.constants.Gender.Male, 20, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ru_RU, 'Olga', cloudlanguagetools.constants.Gender.Female, 21, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ru_RU, 'Dmitri', cloudlanguagetools.constants.Gender.Male, 21, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fi_FI, 'Milla', cloudlanguagetools.constants.Gender.Female, 23, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fi_FI, 'Marko', cloudlanguagetools.constants.Gender.Male, 23, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ar_XA, 'Tarik', cloudlanguagetools.constants.Gender.Male, 27, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ar_XA, 'Laila', cloudlanguagetools.constants.Gender.Female, 27, 2, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ro_RO, 'Ioana', cloudlanguagetools.constants.Gender.Female, 30, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.eo_XX, 'Ludoviko', cloudlanguagetools.constants.Gender.Male, 31, 1, 2),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Kate', cloudlanguagetools.constants.Gender.Female, 1, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Paul', cloudlanguagetools.constants.Gender.Male, 1, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Julie', cloudlanguagetools.constants.Gender.Female, 1, 3, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_GB, 'Bridget', cloudlanguagetools.constants.Gender.Female, 1, 4, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_GB, 'Hugh', cloudlanguagetools.constants.Gender.Male, 1, 5, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Ashley', cloudlanguagetools.constants.Gender.Female, 1, 6, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'James', cloudlanguagetools.constants.Gender.Male, 1, 7, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Beth', cloudlanguagetools.constants.Gender.Female, 1, 8, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_MX, 'Violeta', cloudlanguagetools.constants.Gender.Female, 2, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_MX, 'Francisco', cloudlanguagetools.constants.Gender.Male, 2, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_MX, 'Gloria', cloudlanguagetools.constants.Gender.Female, 2, 3, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_ES, 'Lola', cloudlanguagetools.constants.Gender.Female, 2, 4, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.es_ES, 'Manuel', cloudlanguagetools.constants.Gender.Male, 2, 5, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.de_DE, 'Lena', cloudlanguagetools.constants.Gender.Female, 3, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.de_DE, 'Tim', cloudlanguagetools.constants.Gender.Male, 3, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_CA, 'Chloe', cloudlanguagetools.constants.Gender.Female, 4, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_CA, 'Leo', cloudlanguagetools.constants.Gender.Male, 4, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Roxane', cloudlanguagetools.constants.Gender.Female, 4, 3, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Louis', cloudlanguagetools.constants.Gender.Male, 4, 4, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_BR, 'Helena', cloudlanguagetools.constants.Gender.Female, 6, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_BR, 'Rafael', cloudlanguagetools.constants.Gender.Male, 6, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Elisa', cloudlanguagetools.constants.Gender.Female, 7, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Roberto', cloudlanguagetools.constants.Gender.Male, 7, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_CN, 'Lily', cloudlanguagetools.constants.Gender.Female, 10, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_CN, 'Wang', cloudlanguagetools.constants.Gender.Male, 10, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_CN, 'Hui', cloudlanguagetools.constants.Gender.Female, 10, 3, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_CN, 'Liang', cloudlanguagetools.constants.Gender.Male, 10, 4, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_CN, 'Kiang', cloudlanguagetools.constants.Gender.Male, 10, 5, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_HK, 'Kaho', cloudlanguagetools.constants.Gender.Male, 10, 6, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_HK, 'Kayan', cloudlanguagetools.constants.Gender.Female, 10, 7, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_TW, 'Yafang', cloudlanguagetools.constants.Gender.Female, 10, 8, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Miyu', cloudlanguagetools.constants.Gender.Female, 12, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Show', cloudlanguagetools.constants.Gender.Male, 12, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Misaki', cloudlanguagetools.constants.Gender.Female, 12, 3, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Sayaka', cloudlanguagetools.constants.Gender.Female, 12, 4, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Hikari', cloudlanguagetools.constants.Gender.Female, 12, 5, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Haruka', cloudlanguagetools.constants.Gender.Female, 12, 6, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Ryo', cloudlanguagetools.constants.Gender.Male, 12, 7, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Takeru', cloudlanguagetools.constants.Gender.Male, 12, 8, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Yumi', cloudlanguagetools.constants.Gender.Female, 13, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Junwoo', cloudlanguagetools.constants.Gender.Male, 13, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Sujin', cloudlanguagetools.constants.Gender.Female, 13, 3, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Hyeryun', cloudlanguagetools.constants.Gender.Female, 13, 4, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Jimin', cloudlanguagetools.constants.Gender.Female, 13, 5, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Sena', cloudlanguagetools.constants.Gender.Female, 13, 6, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Dayoung', cloudlanguagetools.constants.Gender.Female, 13, 7, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Hyuna', cloudlanguagetools.constants.Gender.Female, 13, 8, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Yura', cloudlanguagetools.constants.Gender.Female, 13, 9, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ko_KR, 'Jihun', cloudlanguagetools.constants.Gender.Male, 13, 10, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.th_TH, 'Sarawut', cloudlanguagetools.constants.Gender.Male, 26, 1, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.th_TH, 'Somsi', cloudlanguagetools.constants.Gender.Female, 26, 2, 3),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_GB, 'Olivia', cloudlanguagetools.constants.Gender.Female, 1, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_GB, 'Oliver', cloudlanguagetools.constants.Gender.Male, 1, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_AU, 'Matilda', cloudlanguagetools.constants.Gender.Female, 1, 3, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_AU, 'Jackson', cloudlanguagetools.constants.Gender.Male, 1, 4, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_IN, 'Lakshmi', cloudlanguagetools.constants.Gender.Female, 1, 5, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_IN, 'Prashant', cloudlanguagetools.constants.Gender.Male, 1, 6, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Brenda', cloudlanguagetools.constants.Gender.Female, 1, 7, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.en_US, 'Warren', cloudlanguagetools.constants.Gender.Male, 1, 8, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.de_DE, 'Hilda', cloudlanguagetools.constants.Gender.Female, 3, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.de_DE, 'Heinz', cloudlanguagetools.constants.Gender.Male, 3, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Beatrice', cloudlanguagetools.constants.Gender.Female, 4, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_FR, 'Antoine', cloudlanguagetools.constants.Gender.Male, 4, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_CA, 'Leonie', cloudlanguagetools.constants.Gender.Female, 4, 3, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fr_CA, 'Gaspard', cloudlanguagetools.constants.Gender.Male, 4, 4, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_BR, 'Ana', cloudlanguagetools.constants.Gender.Female, 6, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_BR, 'Antonio', cloudlanguagetools.constants.Gender.Male, 6, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_PT, 'Leonor', cloudlanguagetools.constants.Gender.Female, 6, 3, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pt_PT, 'Tiago', cloudlanguagetools.constants.Gender.Male, 6, 4, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Bianca', cloudlanguagetools.constants.Gender.Female, 7, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.it_IT, 'Alessandro', cloudlanguagetools.constants.Gender.Male, 7, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.el_GR, 'Eleni', cloudlanguagetools.constants.Gender.Female, 8, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.el_GR, 'Giorgos', cloudlanguagetools.constants.Gender.Male, 8, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.sv_SE, 'Astrid', cloudlanguagetools.constants.Gender.Female, 9, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.sv_SE, 'Gustav', cloudlanguagetools.constants.Gender.Male, 9, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_TW, 'Chia-ling', cloudlanguagetools.constants.Gender.Female, 10, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_TW, 'Chia-hao', cloudlanguagetools.constants.Gender.Male, 10, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_HK, 'Yan', cloudlanguagetools.constants.Gender.Female, 10, 3, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.zh_HK, 'Chan', cloudlanguagetools.constants.Gender.Male, 10, 4, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nl_NL, 'Famke', cloudlanguagetools.constants.Gender.Female, 11, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nl_NL, 'Dirk', cloudlanguagetools.constants.Gender.Male, 11, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Himari', cloudlanguagetools.constants.Gender.Female, 12, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ja_JP, 'Kaito', cloudlanguagetools.constants.Gender.Male, 12, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pl_PL, 'Danota', cloudlanguagetools.constants.Gender.Female, 14, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.pl_PL, 'Wojciech', cloudlanguagetools.constants.Gender.Male, 14, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.tr_TR, 'Zehra', cloudlanguagetools.constants.Gender.Female, 16, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.tr_TR, 'Eymen', cloudlanguagetools.constants.Gender.Male, 16, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.cs_CZ, 'Pavla', cloudlanguagetools.constants.Gender.Female, 18, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.cs_CZ, 'Janek', cloudlanguagetools.constants.Gender.Male, 18, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.da_DK, 'Dagny', cloudlanguagetools.constants.Gender.Female, 19, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.da_DK, 'Erik', cloudlanguagetools.constants.Gender.Male, 19, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nb_NO, 'Dagrun', cloudlanguagetools.constants.Gender.Female, 20, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.nb_NO, 'Lars', cloudlanguagetools.constants.Gender.Male, 20, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fi_FI, 'Sanna', cloudlanguagetools.constants.Gender.Female, 23, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fi_FI, 'Mikko', cloudlanguagetools.constants.Gender.Male, 23, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.hi_IN, 'Swathi', cloudlanguagetools.constants.Gender.Female, 24, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.hi_IN, 'Karan', cloudlanguagetools.constants.Gender.Male, 24, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ar_XA, 'Amina', cloudlanguagetools.constants.Gender.Female, 27, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.ar_XA, 'Jamal', cloudlanguagetools.constants.Gender.Male, 27, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.id_ID, 'Putri', cloudlanguagetools.constants.Gender.Female, 28, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.id_ID, 'Bintang', cloudlanguagetools.constants.Gender.Male, 28, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.hu_HU, 'Flora', cloudlanguagetools.constants.Gender.Female, 29, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.hu_HU, 'Laszlo', cloudlanguagetools.constants.Gender.Male, 29, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fil_PH, 'Mayumi', cloudlanguagetools.constants.Gender.Female, 32, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.fil_PH, 'Datu', cloudlanguagetools.constants.Gender.Male, 32, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.sk_SK, 'Eliska', cloudlanguagetools.constants.Gender.Female, 37, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.sk_SK, 'Jakub', cloudlanguagetools.constants.Gender.Male, 37, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.uk_UA, 'Vira', cloudlanguagetools.constants.Gender.Female, 40, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.uk_UA, 'Bohdan', cloudlanguagetools.constants.Gender.Male, 40, 2, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'Nguyet', cloudlanguagetools.constants.Gender.Female, 41, 1, 7),
            VocalWareVoice(cloudlanguagetools.languages.AudioLanguage.vi_VN, 'Phuong', cloudlanguagetools.constants.Gender.Male, 41, 2, 7),
        ]

    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result
   