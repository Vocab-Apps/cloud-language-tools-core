"""CLT-AI API: a versioned, LLM friendly API over cloudlanguagetools.

    from cloudlanguagetools.cltai import create_client, CltAPIVersion, SoundRequest
    clt = create_client(CltAPIVersion.v1)
    result = clt.sound(SoundRequest(text='こんにちは', language='ja', gender='Female'))
    print(result.audio_path, result.voice_name)

Verbs: sound, translate, transliterate, transcribe, llm. Each takes a pydantic request model and
returns a pydantic result model. See cloudlanguagetools/cltai/api.py, or print(clt.describe_api()).
The CLT-AI Agent (cloudlanguagetools.cltai.agent.CltAIAgent) uses this API to fulfill natural
language instructions, either directly (instant mode) or by generating python code (Transformation).
"""

from cloudlanguagetools.cltai.types import CltAPIVersion, LATEST_VERSION, CltAIError
from cloudlanguagetools.cltai.models import (
    SoundRequest, SoundResult, VoiceInfo,
    TranslateRequest, TranslateResult, TranslationServiceInfo,
    TransliterateRequest, TransliterateResult, TransliterationInfo,
    TranscribeRequest, TranscribeResult,
    LlmRequest, LlmResult,
    LanguageInfo, AudioLanguageInfo,
)
from cloudlanguagetools.cltai.api import CltAIClientV1, create_client
from cloudlanguagetools.cltai.transformation import Transformation
from cloudlanguagetools.constants import Service, Gender
from cloudlanguagetools.options import AudioFormat

__all__ = [
    'CltAPIVersion', 'LATEST_VERSION', 'CltAIError',
    'SoundRequest', 'SoundResult', 'VoiceInfo',
    'TranslateRequest', 'TranslateResult', 'TranslationServiceInfo',
    'TransliterateRequest', 'TransliterateResult', 'TransliterationInfo',
    'TranscribeRequest', 'TranscribeResult',
    'LlmRequest', 'LlmResult',
    'LanguageInfo', 'AudioLanguageInfo',
    'CltAIClientV1', 'create_client', 'Transformation',
    'Service', 'Gender', 'AudioFormat',
]
