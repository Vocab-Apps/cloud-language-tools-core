"""
Forvo (https://forvo.com) service integration.

Forvo is a crowdsourced pronunciation dictionary: real human recordings of words
in many languages, contributed and rated by its community. It is exposed to
HyperTTS as a `constants.ServiceType.dictionary` service, so each "voice" is
really a (language, country, gender) filter over Forvo's contributor pool, and
the audio returned is a real human recording, not synthesised speech.

------------------------------------------------------------------------------
Forvo API reference
------------------------------------------------------------------------------

The Forvo API is a REST-style, key-authenticated, URL-path-parameter API. There
are two hosts:

- ``https://apifree.forvo.com``    -- free tier
- ``https://apicommercial.forvo.com`` -- paid/commercial tier (used here)

Every request has the shape::

    {url_base}/key/{api_key}/format/{format}/action/{action}/<...params...>

where:

- ``key``     : the account's API key (see https://api.forvo.com/account/).
- ``format``  : response encoding. One of:
                  - ``xml``
                  - ``json`` (used throughout this module; for JSONP, add a
                    ``callback/function_name`` parameter)
                  - ``js-tag`` (returns a <script> tag per pronunciation with a
                    play icon, for direct embedding in a web page)
- ``action``  : the endpoint name (see the endpoint list below).

Authentication is solely via the ``key`` path segment; there is no header-based
auth or OAuth. Requests must carry a browser-like ``User-Agent`` header because
Forvo sits behind Cloudflare, which rejects empty/default UA strings.

------------------------------------------------------------------------------
Documented endpoints (https://api.forvo.com/documentation/)
------------------------------------------------------------------------------

All endpoints are read-only. The Forvo API exposes **no write endpoints**: you
cannot rate, vote, upload, edit, or delete pronunciations through the API. The
only rating-related capabilities are read-side filters/sorts (see
``word-pronunciations`` below). Submitting ratings, uploading audio, etc. is
only possible through the forvo.com website UI for logged-in users.

1. word-pronunciations   -- the main endpoint used by HyperTTS.
   Doc: https://api.forvo.com/documentation/word-pronunciations/

   Returns all pronunciations Forvo has for a given word, optionally filtered.

   Required parameters:
     - ``word``   : the word to look up (URL-encoded).

   Optional parameters (all are server-side filters/sorts):
     - ``language``  : Forvo language code (e.g. ``en``, ``zh``, ``yue``,
                       ``nan``, ``wuu``). Restricts results to recordings
                       contributed under that language. See the language-list
                       endpoint for the full set of codes; Forvo exposes many
                       distinct Chinese-variety codes (``zh`` = Mandarin
                       Chinese, ``yue`` = Cantonese, ``nan`` = Min Nan,
                       ``wuu`` = Wu Chinese, ``jliu`` = Jiaoliao Mandarin,
                       ``jlua`` = Jilu Mandarin, ``juai`` = Lower Yangtze
                       Mandarin, ``xghu`` = Southwestern Mandarin, ``hak`` =
                       Hakka, ``gan`` = Gan Chinese, ``cjy`` = Jin Chinese,
                       ``hsn`` = Xiang Chinese, ``cdo`` = Min Dong,
                       ``tisa`` = Toisanese Cantonese, ``jusi`` =
                       Shanghainese, ``taiu`` = Taihu Wu, ``ltc`` = Middle
                       Chinese, ``plig`` = Changzhou, ``fzho`` = Fuzhou).
     - ``country``   : ISO 3166-1 Alpha-3 country code of the *contributor*
                       (e.g. ``USA``, ``GBR``, ``CHN``, ``TWN``, ``HKG``).
                       Filters by the contributor's country, not by the
                       language's region. There is no sub-national filter, so
                       ``country/CHN`` cannot distinguish Liaoning from
                       Sichuan.
     - ``username``  : a specific Forvo contributor's username. Returns only
                       that user's recording(s) for the word. Used by this
                       module's ``preferred_user`` voice-key feature.
     - ``sex``       : ``m`` (male) or ``f`` (female).
     - ``rate``      : integer minimum rating. Returns only recordings rated
                       at least this high.
     - ``order``     : sort order. One of:
                         - ``date-desc`` (newest first)
                         - ``date-asc``  (oldest first)
                         - ``rate-desc`` (highest rated first) [used here]
                         - ``rate-asc``  (lowest rated first)
     - ``limit``     : integer; maximum number of pronunciations to return.
                       This module uses ``limit/1`` because it only needs one
                       recording per request.
     - ``group-in-languages``: ``true`` / ``false`` (default ``false``).
                       Groups the returned items by language.

   Response (JSON): an object with an ``items`` array. Each item includes at
   least:
     - ``pathmp3``      : URL of the MP3 recording (fetched separately).
     - ``username``     : contributor's Forvo username.
     - ``sex``          : ``m`` / ``f``.
     - ``country``      : Alpha-3 code of the contributor's country.
     - ``rate``         : integer rating (counts of positive votes, roughly).
     - ``num_votes``    : number of votes received.
     - ``addtime``      : when the recording was added.
     - ``lang``         : Forvo language code of the recording.
     - ``standard``     : whether this is the "standard" pronunciation.

   Quirks handled by this module:
     - HTTP 200 with a bare ``false`` JSON body when the word exists but has
       no pronunciations; treated as NotFoundError.
     - HTTP 200 with an empty ``{"items": []}``; treated as NotFoundError.
     - Redirect to ``https://forvo.com/404`` (HTTP 403 from Cloudflare) when
       the word truly does not exist; treated as NotFoundError.
     - HTTP 414 when the input text is too long for the URL; treated as
       InputError.
     - Occasional non-``{"items": ...}`` JSON shapes (bare bools, lists);
       logged and surfaced as RequestError.

2. standard-pronunciation
   Doc: https://api.forvo.com/documentation/standard-pronunciation/

   Returns Forvo's designated "standard" pronunciation for a word in a given
   language (the recording Forvo's editors have marked as canonical). Takes the
   same ``word`` and ``language`` parameters as ``word-pronunciations``. Not
   currently used by this module.

3. language-list
   Doc: https://api.forvo.com/documentation/language-list/

   Returns the list of languages Forvo has recordings for. Used by this module
   in ``get_tts_voice_list`` to discover the available languages (with a
   ``min-pronunciations`` filter to skip near-empty languages). Each item
   carries a ``code`` (the value to pass as ``language/`` to
   ``word-pronunciations``), an ``en`` name, and the native ``language`` name.
   A cached copy lives at ``temp_data_files/forvo_language_list``.

   Optional parameter:
     - ``min-pronunciations`` : integer; only list languages with at least
                                this many recordings. This module uses 5000.

4. language-popular
   Doc: https://api.forvo.com/documentation/language-popular/

   Returns the most popular languages on Forvo. Not used by this module.

5. pronounced-words-search
   Doc: https://api.forvo.com/documentation/pronounced-words-search/

   Searches for words that have been pronounced, by substring. Not used by
   this module.

6. words-search
   Doc: https://api.forvo.com/documentation/words-search/

   General word search across Forvo's dictionary. Not used by this module.

7. popular-pronounced-words
   Doc: https://api.forvo.com/documentation/popular-pronounced-words/

   Returns the most popularly pronounced words (optionally per language). Not
   used by this module.

------------------------------------------------------------------------------
What the API does *not* let us do
------------------------------------------------------------------------------

- Rate or vote on a recording (no write endpoint).
- Upload, replace, or delete a recording (no write endpoint).
- Filter by sub-national region (only by contributor's country, Alpha-3).
- Filter by dialect tag other than the top-level ``language`` code. Forvo's
  dialect granularity is entirely encoded in the ``language`` parameter: each
  recognized variety has its own code (``zh`` vs ``yue`` vs ``nan`` vs
  ``wuu`` vs ``jliu`` etc.). Varieties without a dedicated code (e.g.
  Zhongyuan Mandarin / Lanyin Mandarin) cannot be targeted at all and fall
  into the generic ``zh`` bucket.
- Authenticate via headers/OAuth (key is a path segment only).
- Paginate explicitly; ``limit`` truncates, there is no cursor/offset.

------------------------------------------------------------------------------
How this module uses the API
------------------------------------------------------------------------------

- ``get_tts_voice_list`` calls ``language-list`` to discover languages, then
  expands each into one ``ForvoVoice`` per (audio_language, gender) pair.
- ``get_tts_audio`` calls ``word-pronunciations`` with
  ``language``, optional ``sex``, optional ``country``, optional
  ``username`` (the ``preferred_user`` feature), ``order/rate-desc`` and
  ``limit/1``, then downloads the MP3 at ``items[0].pathmp3``.

See ``20260705_CLT_FORVO_CHINESE_ISSUE.md`` for the known issue around
Chinese-dialect voices where ``get_voices_for_language_entry`` does not yet
override the ``language_code`` per ``audio_language``, causing e.g.
``nan_CN`` / ``wuu_CN`` / ``zh_CN_liaoning`` voices to all request
``language/zh``.
"""

import json
import requests
import urllib
import urllib3
import tempfile
import logging
import os
import pprint

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.ttsvoice
import cloudlanguagetools.translationlanguage
import cloudlanguagetools.transliterationlanguage
import cloudlanguagetools.errors

GENDER_MAP = {
    cloudlanguagetools.constants.Gender.Male: 'm',
    cloudlanguagetools.constants.Gender.Female: 'f'
}

COUNTRY_ANY = 'ANY'

logger = logging.getLogger(__name__)

class ForvoVoice(cloudlanguagetools.ttsvoice.TtsVoice):
    def __init__(self, language_code, country_code, audio_language, gender):
        # print(voice_data)
        self.service = cloudlanguagetools.constants.Service.Forvo
        self.service_fee = cloudlanguagetools.constants.ServiceFee.paid
        self.language_code = language_code
        self.country_code = country_code
        self.audio_language = audio_language
        self.gender = gender

    def get_voice_key(self):
        result = {
            'language_code': self.language_code,
            'country_code': self.country_code
        }
        if self.gender != cloudlanguagetools.constants.Gender.Any:
            result['gender'] = GENDER_MAP[self.gender]
        return result

    def get_voice_description(self):
        return f'{self.get_audio_language_name()}, {self.get_gender().name}, {self.service.name}'

    def get_voice_shortname(self):
        return f'{self.language_code}-{self.country_code}'

    def get_options(self):
        return {}



class ForvoService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.url_base = 'https://apicommercial.forvo.com'
        self.build_audio_language_map()
        
        # on 2024/07, forvo started throwing some errors with SSL verification, suspect an incorrect
        # setup on their side but they are taking too long to fix it.
        self.verify_ssl = True

    def configure(self, config):
        self.key = config['key']

    def get_headers(self):
        # forvo uses cloudflare or something equivalent
        return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'}

    def get_tts_audio(self, text, voice_key, options):
        """Fetch a single pronunciation MP3 from Forvo for ``text``.

        Calls the ``word-pronunciations`` endpoint
        (https://api.forvo.com/documentation/word-pronunciations/) with:

        - ``word``      : the input text, URL-encoded.
        - ``language``  : ``voice_key['language_code']`` (a Forvo language
                          code such as ``en``, ``zh``, ``yue``, ``nan``).
        - ``sex``       : ``voice_key['gender']`` (``m``/``f``), if present.
        - ``country``   : ``voice_key['country_code']`` (ISO 3166-1 Alpha-3),
                          unless it equals ``COUNTRY_ANY``.
        - ``username``  : ``voice_key['preferred_user']``, if present (picks
                          a specific contributor's recording).
        - ``order``     : ``rate-desc`` (highest-rated first).
        - ``limit``     : ``1`` (we only need one recording).

        Then downloads the MP3 at ``items[0].pathmp3`` and returns it as a
        temp file. Raises ``NotFoundError`` for any "word has no
        pronunciations" condition (404 redirect, bare ``false`` body, or
        empty ``items``), ``InputError`` for over-long text (HTTP 414),
        ``TimeoutError`` for network timeouts, and ``RequestError`` for
        everything else.
        """
        language = voice_key['language_code']

        sex_param = ''
        if 'gender' in voice_key:
            sex_param = f"/sex/{voice_key['gender']}"
        
        country_code = ''
        if voice_key['country_code'] != COUNTRY_ANY:
            # user selected a particular country
            country_code = f"/country/{voice_key['country_code']}"

        username_param = ''
        if 'preferred_user' in voice_key:
            username_param = f"/username/{voice_key['preferred_user']}"

        encoded_text = urllib.parse.quote(text)

        url = f'{self.url_base}/key/{self.key}/format/json/action/word-pronunciations/word/{encoded_text}/language/{language}{sex_param}{username_param}/order/rate-desc/limit/1{country_code}'

        try:
            response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout,
                                    verify=self.verify_ssl)
            logger.info(f'forvo response status={response.status_code} url={response.url} content={response.content}')
            if response.url == 'https://forvo.com/404':
                error_message = f"Pronunciation not found in Forvo for word [{text}], language={language}, country={voice_key['country_code']}"
                raise cloudlanguagetools.errors.NotFoundError(error_message)
            if response.status_code == 414:
                raise cloudlanguagetools.errors.InputError(f'Forvo: text too long')
            response.raise_for_status()

            data = response.json()
            # forvo sometimes returns an unexpected json shape (e.g. a bare bool or list)
            # instead of the documented {"items": [...]} object. log it so we can identify
            # the root cause instead of failing with an opaque TypeError.
            if not isinstance(data, dict) or 'items' not in data:
                # forvo returns a bare `false` json body (HTTP 200) when no
                # pronunciations exist for the requested word. this is a
                # permanent "not found" condition, not a transient failure.
                if data is False:
                    error_message = f"Pronunciation not found in Forvo for word [{text}], language={language}, country={voice_key['country_code']}"
                    raise cloudlanguagetools.errors.NotFoundError(error_message)
                logger.error(f'unexpected forvo response shape for word [{text}], language={language}, '
                             f'country={voice_key["country_code"]}: status={response.status_code} '
                             f'url={response.url} type={type(data).__name__} data={data!r} '
                             f'raw_content={response.content!r}')
                raise cloudlanguagetools.errors.RequestError('Unable to retrieve audio from Forvo')
            items = data['items']
            if len(items) == 0:
                error_message = f"Pronunciation not found in Forvo for word [{text}], language={language}, country={voice_key['country_code']}"
                raise cloudlanguagetools.errors.NotFoundError(error_message)
            audio_url = items[0]['pathmp3']
            output_temp_file = tempfile.NamedTemporaryFile()
            output_temp_filename = output_temp_file.name
            audio_request = requests.get(audio_url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout,
                                         verify=self.verify_ssl)
            audio_request.raise_for_status()

            # Check content type to ensure we received audio
            content_type = audio_request.headers.get('Content-Type', '')
            if content_type != 'audio/mpeg':
                logger.error(f'unexpected content type from forvo audio request: {content_type!r}, content: {audio_request.content!r}')
                raise cloudlanguagetools.errors.RequestError(f'Unexpected content type from Forvo: {content_type}')

            open(output_temp_filename, 'wb').write(audio_request.content)
            return output_temp_file
        except requests.exceptions.Timeout as exception:
            raise cloudlanguagetools.errors.TimeoutError(f'timeout while retrieving forvo audio') from exception
        except requests.exceptions.ConnectionError as exception:
            # requests wraps urllib3.exceptions.ReadTimeoutError in ConnectionError
            # when the timeout happens while reading the response body
            if exception.args and isinstance(exception.args[0], urllib3.exceptions.TimeoutError):
                raise cloudlanguagetools.errors.TimeoutError(f'timeout while retrieving forvo audio') from exception
            logger.warning(f'could not retrieve forvo audio: {str(exception)}')
            raise cloudlanguagetools.errors.RequestError('Unable to retrieve audio from Forvo') from exception
        except cloudlanguagetools.errors.NotFoundError as exception:
            raise
        except cloudlanguagetools.errors.RequestError as exception:
            # already logged with full context above, don't re-wrap and lose the message
            raise
        # handle json decode error
        except json.decoder.JSONDecodeError as exception:
            logger.warning(f'could not decode json response from forvo: {response.content}')
            raise cloudlanguagetools.errors.RequestError('Unable to retrieve audio from Forvo') from exception
        except Exception as exception:
            # make sure not to leak url and key
            logger.warning(f'could not retrieve forvo audio: {str(exception)}')
            raise cloudlanguagetools.errors.RequestError('Unable to retrieve audio from Forvo') from exception


    def get_language_enum(self, language_id):
        """Map a Forvo language code (e.g. ``zh``, ``ind``, ``pt``) to our
        internal ``Language`` enum. A few Forvo codes don't match our enum
        names directly and are remapped via ``forvo_language_id_map``."""
        forvo_language_id_map = {
            'zh': 'zh_cn',
            'ind': 'id_',
            'pt': 'pt_pt'
        }
        language_id = forvo_language_id_map.get(language_id, language_id)
        logger.debug(f'looking for {language_id}')
        return cloudlanguagetools.languages.Language[language_id]

    def get_audio_language_enum(self, language_id):
        pass

    def get_country_code(self, audio_language):
        """Map an ``AudioLanguage`` to an ISO 3166-1 Alpha-3 country code for
        the Forvo ``country`` parameter. Returns ``'ANY'`` (a sentinel that
        ``get_tts_audio`` translates to "no country filter") when no specific
        country applies. See https://en.wikipedia.org/wiki/ISO_3166-1."""
        # https://en.wikipedia.org/wiki/ISO_3166-1
        country_code_map = {
            cloudlanguagetools.languages.AudioLanguage.fr_FR: 'FRA',
            cloudlanguagetools.languages.AudioLanguage.fr_CH: 'CHE',
            cloudlanguagetools.languages.AudioLanguage.fr_BE: 'BEL',
            cloudlanguagetools.languages.AudioLanguage.nl_BE: 'BEL',
            cloudlanguagetools.languages.AudioLanguage.nl_NL: 'NLD',
            cloudlanguagetools.languages.AudioLanguage.de_AT: 'AUT',
            cloudlanguagetools.languages.AudioLanguage.de_DE: 'DEU',
            cloudlanguagetools.languages.AudioLanguage.de_CH: 'CHE',
            cloudlanguagetools.languages.AudioLanguage.en_AU: 'AUS',
            cloudlanguagetools.languages.AudioLanguage.en_CA: 'CAN',
            cloudlanguagetools.languages.AudioLanguage.en_GB: 'GBR',
            cloudlanguagetools.languages.AudioLanguage.en_IE: 'IRL',
            cloudlanguagetools.languages.AudioLanguage.en_IN: 'IND',
            cloudlanguagetools.languages.AudioLanguage.en_HK: 'HKG',
            cloudlanguagetools.languages.AudioLanguage.en_US: 'USA',
            cloudlanguagetools.languages.AudioLanguage.en_PH: 'PHL',
            cloudlanguagetools.languages.AudioLanguage.en_NZ: 'NZL',
            cloudlanguagetools.languages.AudioLanguage.en_SG: 'SGP',
            cloudlanguagetools.languages.AudioLanguage.en_ZA: 'ZAF',

            cloudlanguagetools.languages.AudioLanguage.en_GB_WLS: 'GBR', 
            cloudlanguagetools.languages.AudioLanguage.bn_BD: 'BGD', 
            cloudlanguagetools.languages.AudioLanguage.en_KE: 'KEN', 
            cloudlanguagetools.languages.AudioLanguage.ta_IN: 'IND', 
            cloudlanguagetools.languages.AudioLanguage.ur_IN: 'IND',
            cloudlanguagetools.languages.AudioLanguage.bn_IN: 'IND',
            # bengali, any country
            # https://github.com/Vocab-Apps/anki-hyper-tts/issues/223
            cloudlanguagetools.languages.AudioLanguage.bn_ANY: 'ANY', 
            cloudlanguagetools.languages.AudioLanguage.en_NG: 'NGA',
            cloudlanguagetools.languages.AudioLanguage.ta_LK: 'LKA',
            cloudlanguagetools.languages.AudioLanguage.ur_PK: 'PAK',
            cloudlanguagetools.languages.AudioLanguage.en_TZ: 'TZA',
            cloudlanguagetools.languages.AudioLanguage.ta_SG: 'SGP',
            cloudlanguagetools.languages.AudioLanguage.ta_MY: 'MYS',

            # portuguese
            cloudlanguagetools.languages.AudioLanguage.pt_PT: 'PRT',
            cloudlanguagetools.languages.AudioLanguage.pt_BR: 'BRA',

            # arabic
            cloudlanguagetools.languages.AudioLanguage.ar_AE: 'ARE',
            cloudlanguagetools.languages.AudioLanguage.ar_BH: 'BHR',
            cloudlanguagetools.languages.AudioLanguage.ar_DZ: 'DZA',
            cloudlanguagetools.languages.AudioLanguage.ar_EG: 'EGY',
            cloudlanguagetools.languages.AudioLanguage.ar_IQ: 'IRQ',
            cloudlanguagetools.languages.AudioLanguage.ar_JO: 'JOR',
            cloudlanguagetools.languages.AudioLanguage.ar_KW: 'KWT',
            cloudlanguagetools.languages.AudioLanguage.ar_LY: 'LBY',
            cloudlanguagetools.languages.AudioLanguage.ar_MA: 'MAR',
            cloudlanguagetools.languages.AudioLanguage.ar_SA: 'SAU',
            cloudlanguagetools.languages.AudioLanguage.ar_QA: 'QAT',
            cloudlanguagetools.languages.AudioLanguage.ar_SA: 'SAU',
            cloudlanguagetools.languages.AudioLanguage.ar_SY: 'SYR',
            cloudlanguagetools.languages.AudioLanguage.ar_TN: 'TUN',
            cloudlanguagetools.languages.AudioLanguage.ar_XA: 'ANY', # any country
            cloudlanguagetools.languages.AudioLanguage.ar_YE: 'YEM', 
            cloudlanguagetools.languages.AudioLanguage.ar_LB: 'LBN', 
            cloudlanguagetools.languages.AudioLanguage.ar_OM: 'OMN', 

            # spanish
            cloudlanguagetools.languages.AudioLanguage.es_AR: 'ARG', 
            cloudlanguagetools.languages.AudioLanguage.es_BO: 'BOL',
            cloudlanguagetools.languages.AudioLanguage.es_CL: 'CHL',
            cloudlanguagetools.languages.AudioLanguage.es_CO: 'COL',
            cloudlanguagetools.languages.AudioLanguage.es_CR: 'CRI',
            cloudlanguagetools.languages.AudioLanguage.es_CU: 'CUB',
            cloudlanguagetools.languages.AudioLanguage.es_DO: 'DOM',
            cloudlanguagetools.languages.AudioLanguage.es_EC: 'ECU',
            cloudlanguagetools.languages.AudioLanguage.es_ES: 'ESP',
            cloudlanguagetools.languages.AudioLanguage.es_GQ: 'GNQ',
            cloudlanguagetools.languages.AudioLanguage.es_GT: 'GTM',
            cloudlanguagetools.languages.AudioLanguage.es_HN: 'HND',
            cloudlanguagetools.languages.AudioLanguage.es_LA: 'ANY', # any country
            cloudlanguagetools.languages.AudioLanguage.es_MX: 'MEX',
            cloudlanguagetools.languages.AudioLanguage.es_NI: 'NIC',
            cloudlanguagetools.languages.AudioLanguage.es_PA: 'PAN',
            cloudlanguagetools.languages.AudioLanguage.es_PE: 'PER',
            cloudlanguagetools.languages.AudioLanguage.es_PR: 'PRI',
            cloudlanguagetools.languages.AudioLanguage.es_PY: 'PRY',
            cloudlanguagetools.languages.AudioLanguage.es_SV: 'SLV',
            cloudlanguagetools.languages.AudioLanguage.es_US: 'USA', 
            cloudlanguagetools.languages.AudioLanguage.es_UY: 'URY', 
            cloudlanguagetools.languages.AudioLanguage.es_VE: 'VEN', 

            cloudlanguagetools.languages.AudioLanguage.ba_RU: 'RUS',
            cloudlanguagetools.languages.AudioLanguage.eu_ES: 'ESP',
            cloudlanguagetools.languages.AudioLanguage.en_CB: 'VGB',
            
            cloudlanguagetools.languages.AudioLanguage.zh_CN: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_HK: 'HKG',
            cloudlanguagetools.languages.AudioLanguage.yue_CN: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.wuu_CN: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.nan_CN: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_henan: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_liaoning: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_shaanxi: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_shandong: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_sichuan: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_guangxi: 'CHN',

            cloudlanguagetools.languages.AudioLanguage.zh_CN_gansu: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_anhui: 'CHN',
            cloudlanguagetools.languages.AudioLanguage.zh_CN_hunan: 'CHN'

        }
        if audio_language not in country_code_map:
            logging.error(f'no country code found for {audio_language}')
        return country_code_map[audio_language]

    def get_voices_for_language_entry(self, language):
        """Expand one Forvo ``language-list`` entry into a list of
        ``ForvoVoice`` objects, one per (audio_language, gender) pair.

        ``language`` is a single item from the ``language-list`` response and
        carries ``code`` (the Forvo language code), ``en`` and ``language``
        (display names).

        The Forvo ``code`` is used verbatim as ``voice_key['language_code']``
        for every audio language in the bucket. This is correct when the
        bucket maps 1:1 to a Forvo language (e.g. ``en`` -> ``en_US`` etc.),
        but is **wrong** for languages where our ``AudioLanguage`` set is
        finer-grained than Forvo's codes -- most notably Chinese, where
        ``nan_CN`` / ``wuu_CN`` / ``zh_CN_liaoning`` etc. all inherit
        ``language_code='zh'`` and therefore all hit the same Forvo bucket.
        See ``20260705_CLT_FORVO_CHINESE_ISSUE.md``.
        """
        try:
            language_code = language['code']
            language_enum = self.get_language_enum(language_code)
            # create as many voices as there are audio languages available

            logger.debug(f'processing language_enum {language_enum}')
            audio_language_list = self.audio_language_map[language_enum]

            # special handling for portugese. we need to add both countries manually.
            if language_enum == cloudlanguagetools.languages.Language.pt_pt:
                audio_language_list = [
                    cloudlanguagetools.languages.AudioLanguage.pt_PT,
                    cloudlanguagetools.languages.AudioLanguage.pt_BR
                ]

            voices = []

            for gender in cloudlanguagetools.constants.Gender:
                if len(audio_language_list) == 1:
                    country_code = COUNTRY_ANY
                    voices.append(ForvoVoice(language_code, country_code, audio_language_list[0], gender))
                else:
                    # logging.info(f'multiple audio languages found: {audio_language_list}')
                    for audio_language in audio_language_list:
                        country_code = self.get_country_code(audio_language)
                        voices.append(ForvoVoice(language_code, country_code, audio_language, gender))

            return voices

        except KeyError:
            logging.warn(f'forvo language mapping not found: {language}')

        return []

    def build_audio_language_map(self):
        self.audio_language_map = {}
        for audio_language in cloudlanguagetools.languages.AudioLanguage:
            language = audio_language.lang
            if language not in self.audio_language_map:
                self.audio_language_map[language] = []
            self.audio_language_map[language].append(audio_language)
            

    def get_tts_voice_list(self):
        """Return the full list of Forvo voices by calling the
        ``language-list`` endpoint
        (https://api.forvo.com/documentation/language-list/) with
        ``min-pronunciations/5000`` to skip near-empty languages, then
        expanding each returned language via
        ``get_voices_for_language_entry``."""
        # returns list of TtSVoice

        voice_list = []

        # https://api.forvo.com/documentation/word-pronunciations/
        url = f'{self.url_base}/key/{self.key}/format/json/action/language-list/min-pronunciations/5000'
        response = requests.get(url, headers=self.get_headers(), timeout=cloudlanguagetools.constants.RequestTimeout,
                                    verify=self.verify_ssl)
        if response.status_code == 200:
            data = response.json()
            languages = data['items']
            for language in languages:
                language_voice_list = self.get_voices_for_language_entry(language)
                voice_list.extend(language_voice_list)

            # pprint.pprint(data)
        else:
            logger.error(f'forvo language list request failed: status={response.status_code} content={response.content}')

        return voice_list


    def get_translation_language_list(self):
        result = []
        return result

    def get_transliteration_language_list(self):
        result = []
        return result


    