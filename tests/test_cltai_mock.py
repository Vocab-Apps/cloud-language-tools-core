"""CLT-AI API tests running offline, against the mock test services and a scripted pydantic-ai model.
run with: uv run pytest tests/test_cltai_mock.py
"""
import os
import sys
import json

import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart, TextPart, ToolReturnPart, RetryPromptPart
from pydantic_ai.models.function import FunctionModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.servicemanager
import cloudlanguagetools.configuration
import cloudlanguagetools.cltai.agent
from cloudlanguagetools.constants import Service
from cloudlanguagetools.cltai import (create_client, CltAPIVersion, CltAIError, Transformation,
    SoundRequest, SoundResult, TranslateRequest, TransliterateRequest, TranscribeRequest, LlmRequest)

TEST_SERVICES_CONFIGURATION = cloudlanguagetools.configuration.ServicesConfiguration(
    test_service_a=cloudlanguagetools.configuration.TestServiceConfig(),
    test_service_b=cloudlanguagetools.configuration.TestServiceConfig(),
)


@pytest.fixture
def clt(tmp_path):
    manager = cloudlanguagetools.servicemanager.ServiceManager(TEST_SERVICES_CONFIGURATION)
    return create_client(CltAPIVersion.v1, manager=manager, output_dir=str(tmp_path))


# client and versioning
# =====================

def test_create_client_version(clt):
    assert clt.api_version == CltAPIVersion.v1
    with pytest.raises(ValueError):
        create_client('v999', manager=clt.manager)


# sound
# =====

def test_sound_defaults(clt):
    resolved = clt.validate_sound(SoundRequest(text='bonjour', language='fr'))
    # TestServiceA comes first, no preference applies to test services
    assert resolved.service == Service.TestServiceA
    assert resolved.voice_name == 'Paul'
    assert resolved.voice_key == {'voice_id': 'paul'}
    assert resolved.audio_language.name == 'fr_FR'

    result = clt.sound(SoundRequest(text='bonjour', language='fr'))
    assert isinstance(result, SoundResult)
    assert result.audio_path.endswith('.mp3')
    assert os.path.dirname(result.audio_path) == clt.output_dir
    assert json.loads(result.read_bytes())['text'] == 'bonjour'


def test_sound_keyword_arguments(clt):
    result = clt.sound(text='bonjour', language='French', service='TestServiceB', voice_name='paul')
    assert result.service == Service.TestServiceB
    assert result.voice_name == 'Paul'


def test_sound_dict_request(clt):
    result = clt.sound({'text': 'bonjour', 'language': 'fr', 'service': 'TestServiceB', 'voice_key': {'voice_id': 'paul'}})
    assert result.service == Service.TestServiceB


def test_sound_invalid_requests(clt):
    # unknown field
    with pytest.raises(CltAIError, match='Extra inputs'):
        clt.sound(text='bonjour', language='fr', speed=1.0)
    # unknown language code
    with pytest.raises(CltAIError, match='unknown language'):
        clt.sound(text='bonjour', language='xx')
    # no voice for language
    with pytest.raises(CltAIError, match='no voice found for language ja'):
        clt.validate_sound(text='こんにちは', language='ja')
    # voice requires service
    with pytest.raises(CltAIError, match='service'):
        clt.validate_sound(text='bonjour', language='fr', voice_name='Paul')
    # unknown voice name: valid alternatives are listed
    with pytest.raises(CltAIError, match='valid voice names: Paul'):
        clt.validate_sound(text='bonjour', language='fr', service='TestServiceA', voice_name='Pierre')
    # unknown voice key
    with pytest.raises(CltAIError, match='voice_key'):
        clt.validate_sound(text='bonjour', language='fr', service='TestServiceA', voice_key={'voice_id': 'pierre'})
    # options are validated against the voice's options model (test voices have no options)
    with pytest.raises(CltAIError, match='invalid options'):
        clt.validate_sound(text='bonjour', language='fr', options={'speed': 1.5})
    # locale which doesn't belong to the language
    with pytest.raises(CltAIError, match='not a locale of language fr'):
        clt.validate_sound(text='bonjour', language='fr', audio_language='en_US')
    # gender not available
    with pytest.raises(CltAIError, match='no Male voice'):
        clt.validate_sound(text='bonjour', language='fr', gender='Male')
    # mp3_hq can't be produced from mp3
    with pytest.raises(CltAIError, match='format mp3_hq'):
        clt.validate_sound(text='bonjour', language='fr', format='mp3_hq')


def test_list_voices(clt):
    voices = clt.list_voices(language='fr')
    assert len(voices) == 2
    assert set(v.service for v in voices) == {Service.TestServiceA, Service.TestServiceB}
    assert clt.list_voices(language='ja') == []
    assert len(clt.list_voices(language='fr', service='TestServiceB', name_contains='pau')) == 1


# translate
# =========

def test_translate(clt):
    result = clt.translate(TranslateRequest(text='bonjour', source_language='fr', target_language='en', service='TestServiceB'))
    assert result.service == Service.TestServiceB
    assert json.loads(result.text) == {'text': 'bonjour', 'from_language_key': 'fr', 'to_language_key': 'en'}
    assert result.source_language.name == 'fr'

    services = clt.list_translation_services('fr', 'zh_cn')
    assert [s.service for s in services] == [Service.TestServiceA, Service.TestServiceB]
    assert services[0].target_language_id == 'zh'


def test_translate_invalid(clt):
    with pytest.raises(CltAIError, match='no translation service found from fr to ja'):
        clt.validate_translate(text='bonjour', source_language='fr', target_language='ja')
    with pytest.raises(CltAIError, match='both fr'):
        clt.validate_translate(text='bonjour', source_language='fr', target_language='fr')
    with pytest.raises(CltAIError, match='Azure is not enabled|cannot translate'):
        clt.validate_translate(text='bonjour', source_language='fr', target_language='en', service='Azure')


# transliterate
# =============

def test_transliterate(clt):
    result = clt.transliterate(TransliterateRequest(text='你好', language='zh_cn', transliteration_name='pinyin'))
    assert result.transliteration_name == 'Pinyin'
    assert json.loads(result.text) == {'text': '你好', 'transliteration_key': 'pinyin'}
    resolved = clt.validate_transliterate(text='你好', language='zh_cn', service='TestServiceB', transliteration_key='pinyin')
    assert resolved.service == Service.TestServiceB

    with pytest.raises(CltAIError, match='available: Pinyin'):
        clt.validate_transliterate(text='你好', language='zh_cn', transliteration_name='jyutping')
    with pytest.raises(CltAIError, match='no transliteration available for fr'):
        clt.validate_transliterate(text='bonjour', language='fr')


def test_sanitize_key():
    key = {'url_path': '/french-api.php', 'api_key': 'secret'}
    assert cloudlanguagetools.cltai.api.sanitize_key(key) == {'url_path': '/french-api.php'}
    assert cloudlanguagetools.cltai.api.sanitize_key('pinyin') == 'pinyin'


# transcribe
# ==========

def test_transcribe(clt):
    sound_result = clt.sound(text='bonjour', language='fr')
    # pass the SoundResult directly
    result = clt.transcribe(audio=sound_result)
    assert result.text == 'bonjour'
    assert result.language.name == 'fr'
    # or a path, format inferred from the extension
    result = clt.transcribe(TranscribeRequest(audio_path=sound_result.audio_path, service='TestServiceB'))
    assert result.service == Service.TestServiceB


def test_transcribe_invalid(clt, tmp_path):
    with pytest.raises(CltAIError, match='audio file not found'):
        clt.transcribe(audio_path='/nonexistent/file.mp3')
    unknown_extension = tmp_path / 'audio.xyz'
    unknown_extension.write_text('{}')
    with pytest.raises(CltAIError, match='cannot guess audio format'):
        clt.validate_transcribe(audio_path=str(unknown_extension))
    assert clt.validate_transcribe(audio_path=str(unknown_extension), format='wav').format.name == 'wav'


# llm
# ===

def test_llm(clt):
    result = clt.llm(LlmRequest(prompt='explain this word: pomme', instructions='be concise'))
    data = json.loads(result.text)
    assert data['prompt'] == 'explain this word: pomme'
    assert data['instructions'] == 'be concise'
    # the service default is filled in by the options model
    assert result.options == {'model': 'test-model'}
    with pytest.raises(CltAIError, match='invalid options'):
        clt.llm(prompt='hello', options={'temperature': 0.5})


def test_validate_generic(clt):
    resolved = clt.validate(TranslateRequest(text='bonjour', source_language='fr', target_language='en'))
    assert resolved.service == Service.TestServiceA
    with pytest.raises(CltAIError):
        clt.validate(SoundResult.model_construct())


def test_describe_api(clt):
    description = clt.describe_api()
    for name in ['clt.sound(', 'clt.translate(', 'clt.transliterate(', 'clt.transcribe(', 'clt.llm(',
                 'clt.list_voices(', 'clt.validate_sound(', 'SoundRequest:', 'voice_key']:
        assert name in description


# transformations
# ===============

TRANSFORMATION_CODE = '''
from cloudlanguagetools.cltai import TranslateRequest

def transform(clt, row):
    text = row.get('French', '').strip()
    if not text:
        return {}
    result = clt.translate(TranslateRequest(text=text, source_language='fr', target_language='en', service='TestServiceA'))
    return {'English': result.text}
'''

def build_transformation(code=TRANSFORMATION_CODE, version=CltAPIVersion.v1):
    return Transformation(api_version=version, instruction='translate French to English',
        description='translate', input_fields=['French'], output_fields=['English'], code=code)


def test_transformation_run_rows(clt):
    transformation = build_transformation()
    # transformations can be stored and reloaded
    transformation = Transformation.model_validate_json(transformation.model_dump_json())
    results = transformation.run_rows(clt, [{'French': 'bonjour'}, {'French': ''}, {'French': 'merci'}])
    assert json.loads(results[0]['English'])['text'] == 'bonjour'
    assert results[1] == {}
    assert json.loads(results[2]['English'])['text'] == 'merci'


def test_transformation_errors(clt):
    with pytest.raises(CltAIError, match='must define a function transform'):
        build_transformation(code='x = 1').compile()
    with pytest.raises(CltAIError, match='failed to load'):
        build_transformation(code='def transform(clt, row) return {}').compile()
    with pytest.raises(CltAIError, match='unexpected fields'):
        build_transformation(code='def transform(clt, row):\n    return {"Other": "x"}').run(clt, {'French': 'x'})
    # per row errors are returned rather than raised
    failing = build_transformation(code='def transform(clt, row):\n    raise ValueError("boom")')
    results = failing.run_rows(clt, [{'French': 'x'}])
    assert isinstance(results[0], ValueError)
    with pytest.raises(ValueError):
        failing.run_rows(clt, [{'French': 'x'}], stop_on_error=True)


# agent, with a scripted model
# ============================

def all_parts(messages):
    return [part for message in messages for part in getattr(message, 'parts', [])]


def is_retry(part):
    # pydantic-ai 2.x reports tool retries as ToolReturnPart with outcome 'retried'
    return isinstance(part, RetryPromptPart) or (isinstance(part, ToolReturnPart) and getattr(part, 'outcome', None) == 'retried')


def tool_returns(messages):
    return [part for part in all_parts(messages) if isinstance(part, ToolReturnPart) and not is_retry(part)]


def retry_prompts(messages):
    return [part for part in all_parts(messages) if is_retry(part)]


def test_agent_codegen(clt):
    def model_function(messages, info):
        returns = tool_returns(messages)
        if len(returns) == 0:
            return ModelResponse(parts=[ToolCallPart('test_transform', {'code': TRANSFORMATION_CODE, 'row': {'French': 'bonjour'}})])
        # the test_transform tool ran the code on the sample row
        assert 'bonjour' in returns[0].content
        output_tool = info.output_tools[0].name
        return ModelResponse(parts=[ToolCallPart(output_tool, {'description': 'translate French to English',
            'input_fields': ['French'], 'output_fields': ['English'], 'code': TRANSFORMATION_CODE})])

    agent = cloudlanguagetools.cltai.agent.CltAIAgent(clt, model=FunctionModel(model_function))
    transformation = agent.generate_transformation('translate the French field to English, put it in the English field',
        sample_row={'French': 'bonjour', 'English': ''})
    assert transformation.api_version == CltAPIVersion.v1
    assert transformation.output_fields == ['English']
    assert json.loads(transformation.run(clt, {'French': 'merci'})['English'])['text'] == 'merci'


def test_agent_codegen_rejects_invalid_code(clt):
    calls = []
    def model_function(messages, info):
        calls.append(1)
        output_tool = info.output_tools[0].name
        if len(retry_prompts(messages)) == 0:
            # first attempt: no transform function, the output validator asks for a retry
            return ModelResponse(parts=[ToolCallPart(output_tool, {'description': 'x', 'input_fields': ['French'],
                'output_fields': ['English'], 'code': 'x = 1'})])
        return ModelResponse(parts=[ToolCallPart(output_tool, {'description': 'x', 'input_fields': ['French'],
            'output_fields': ['English'], 'code': TRANSFORMATION_CODE})])

    agent = cloudlanguagetools.cltai.agent.CltAIAgent(clt, model=FunctionModel(model_function))
    transformation = agent.generate_transformation('translate', available_fields=['French', 'English'])
    assert transformation.code == TRANSFORMATION_CODE
    assert len(calls) == 2


def test_agent_codegen_tools(clt):
    # exercise the code generation tools directly
    deps = cloudlanguagetools.cltai.agent.AgentDeps(clt=clt)
    ctx = type('Ctx', (), {'deps': deps})()
    output = cloudlanguagetools.cltai.agent.run_python(ctx, 'print([v.name for v in clt.list_voices(language="fr")])')
    assert "['Paul', 'Paul']" in output
    output = cloudlanguagetools.cltai.agent.run_python(ctx, 'raise ValueError("oops")')
    assert 'ValueError: oops' in output
    output = cloudlanguagetools.cltai.agent.search_source(ctx, 'rg -n "class CltAIClientV1" cltai')
    assert 'cltai/api.py' in output
    with pytest.raises(cloudlanguagetools.cltai.agent.ModelRetry):
        cloudlanguagetools.cltai.agent.search_source(ctx, 'rm -rf /')
    assert cloudlanguagetools.cltai.agent.ask_user(ctx, 'which field?') == cloudlanguagetools.cltai.agent.NO_USER_ANSWER
    deps.ask_user = lambda question: 'the Word field'
    assert cloudlanguagetools.cltai.agent.ask_user(ctx, 'which field?') == 'the Word field'


def test_agent_instant(clt):
    def model_function(messages, info):
        returns = tool_returns(messages)
        if len(returns) == 0:
            return ModelResponse(parts=[
                ToolCallPart('translate', {'request': {'text': 'bonjour', 'source_language': 'fr', 'target_language': 'en'}}),
                ToolCallPart('sound', {'request': {'text': 'bonjour', 'language': 'fr'}}),
            ])
        return ModelResponse(parts=[TextPart('translation and audio done')])

    agent = cloudlanguagetools.cltai.agent.CltAIAgent(clt, model=FunctionModel(model_function))
    response = agent.run_instant('bonjour', standing_instructions='translate french to english and generate audio')
    assert response.text == 'translation and audio done'
    assert len(response.results) == 2
    assert len(response.sounds) == 1
    assert os.path.isfile(response.sounds[0].audio_path)
    assert len(response.messages) > 0


def test_agent_instant_invalid_request_retries(clt):
    def model_function(messages, info):
        if len(retry_prompts(messages)) == 0:
            # ja has no voice with the test services: the error is sent back to the model
            return ModelResponse(parts=[ToolCallPart('sound', {'request': {'text': 'こんにちは', 'language': 'ja'}})])
        assert 'no voice found for language ja' in str(retry_prompts(messages)[0].content)
        return ModelResponse(parts=[TextPart('no Japanese voice available')])

    agent = cloudlanguagetools.cltai.agent.CltAIAgent(clt, model=FunctionModel(model_function))
    response = agent.run_instant('say こんにちは')
    assert response.text == 'no Japanese voice available'
    assert response.results == []
