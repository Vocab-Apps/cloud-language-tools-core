"""Default selection rules for the CLT-AI API.

When a request leaves a choice open (no service, no voice...), the client resolves it with the
preference lists below. The same lists are rendered as text rules (DEFAULT_RULES_TEXT) for the
CLT-AI Agent, so what the LLM is told and what the code does stay consistent.
"""

from cloudlanguagetools.constants import Service, Gender
from cloudlanguagetools.languages import Language


# services are tried in this order, then any other available service
SOUND_SERVICE_PREFERENCE = [
    Service.Azure,
    Service.Google,
    Service.Amazon,
    Service.OpenAI,
    Service.ElevenLabs,
    Service.Watson,
    Service.Naver,
    Service.CereProc,
    Service.VocalWare,
    Service.FptAi,
]

SOUND_GENDER_PREFERENCE = [Gender.Female, Gender.Male, Gender.Any]

TRANSLATION_SERVICE_PREFERENCE = [
    Service.DeepL,
    Service.Azure,
    Service.Google,
    Service.Amazon,
    Service.Watson,
]

TRANSLITERATION_SERVICE_PREFERENCE = [
    Service.MandarinCantonese,
    Service.EasyPronunciation,
    Service.Azure,
    Service.PyThaiNLP,
    Service.Epitran,
]

# Chinese transliteration defaults to pinyin/jyutping with tone marks (diacritics), no spaces
CHINESE_LANGUAGES = [Language.zh_cn, Language.zh_tw, Language.zh_lit, Language.yue]
CHINESE_TRANSLITERATION_DEFAULT_KEY = {'tone_numbers': False, 'spaces': False}

TRANSCRIPTION_SERVICE_PREFERENCE = [
    Service.OpenAI,
    Service.Azure,
]

LLM_SERVICE_PREFERENCE = [
    Service.OpenAI,
]


def order_by_preference(available, preference):
    """available services sorted by preference, services not in the preference list come last"""
    available = list(dict.fromkeys(available))
    preferred = [service for service in preference if service in available]
    others = [service for service in available if service not in preference]
    return preferred + others


def _names(services):
    return ', '.join(service.name for service in services)


DEFAULT_RULES_TEXT = f"""\
Default choices, apply them when the user doesn't specify:
- sound (audio): if the user doesn't specify which service to use, choose Azure. Preference order: {_names(SOUND_SERVICE_PREFERENCE)}.
- sound: if the user doesn't specify a gender, use a female voice.
- sound: if the user doesn't specify an accent, use the main locale of the language (e.g. en_US for English, fr_FR for French, zh_CN for Mandarin, zh_HK for Cantonese).
- sound: prefer a voice native to that locale over a multilingual voice. Output mp3 unless asked otherwise.
- translate: if the user doesn't specify a service, choose DeepL. Preference order: {_names(TRANSLATION_SERVICE_PREFERENCE)}.
- transliterate: Chinese pinyin / Cantonese jyutping use MandarinCantonese, with tone marks (diacritics) and no spaces unless the user asks for tone numbers or spaces.
- transliterate: IPA and other romanizations: preference order {_names(TRANSLITERATION_SERVICE_PREFERENCE)}. Use transliteration_name to pick the kind of output ("ipa", "romaji", "pinyin"...).
- transcribe: if the user doesn't specify a service, choose OpenAI. Preference order: {_names(TRANSCRIPTION_SERVICE_PREFERENCE)}.
- llm: use OpenAI. Only use llm when sound / translate / transliterate / transcribe can't do the job.
- when a request leaves a field unset (service, voice, gender...), the CLT-AI client applies these same rules,
  and the result reports the choice that was made (e.g. SoundResult.voice_key).
"""
