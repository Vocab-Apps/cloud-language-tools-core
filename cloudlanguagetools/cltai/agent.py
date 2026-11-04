"""CLT-AI Agent: fulfills user instructions with the CLT-AI API, using pydantic-ai and OpenAI models.

Two modes:
- code generation mode (Anki addon, online spreadsheet): agent.generate_transformation() explores
  the API like a coding agent (python execution, source search with rg/grep, discovery functions),
  then returns a Transformation: python code which can be stored and re-run over many rows.
- instant mode (chatbot): agent.run_instant() calls the CLT-AI verbs directly as tools and answers.

Executing generated code is not sandboxed yet.
"""

import io
import os
import json
import shlex
import logging
import contextlib
import subprocess
import traceback
import dataclasses
from typing import Any, Callable, Dict, List, Optional

import pydantic
from pydantic import Field
import pydantic_ai
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import cloudlanguagetools
import cloudlanguagetools.constants
from cloudlanguagetools.cltai import defaults
from cloudlanguagetools.cltai.api import CltAIClientV1
from cloudlanguagetools.cltai.types import CltAIError
from cloudlanguagetools.cltai.models import (
    SoundRequest, SoundResult, TranslateRequest, TranslateResult, TransliterateRequest, TransliterateResult,
    TranscribeRequest, TranscribeResult, LlmRequest, LlmResult)
from cloudlanguagetools.cltai.transformation import Transformation, build_namespace, compile_transform

logger = logging.getLogger(__name__)

# pydantic-ai prints a banner on first run, keep library output quiet unless asked otherwise
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

DEFAULT_AGENT_MODEL = 'gpt-5.5'

# root for source exploration: the cloudlanguagetools package directory
SOURCE_ROOT = os.path.dirname(os.path.abspath(cloudlanguagetools.__file__))
ALLOWED_SHELL_COMMANDS = ['rg', 'grep', 'ls', 'cat', 'head', 'tail', 'find', 'wc']
MAX_TOOL_OUTPUT = 12000
MAX_LISTED_ITEMS = 60

NO_USER_ANSWER = 'No user is available to answer. Make the most reasonable choice and mention the assumption in the description.'


def _truncate(text: str, limit: int = MAX_TOOL_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f'\n... [truncated, {len(text) - limit} more characters]'


def _limited(items: List[Any], limit: int):
    items = list(items)
    result = {'count': len(items), 'items': items[:limit]}
    if len(items) > limit:
        result['note'] = f'only the first {limit} of {len(items)} are shown, narrow down the filters'
    return result


@dataclasses.dataclass
class AgentDeps:
    clt: CltAIClientV1
    available_fields: List[str] = dataclasses.field(default_factory=list)
    sample_row: Optional[Dict[str, Any]] = None
    ask_user: Optional[Callable[[str], str]] = None
    standing_instructions: Optional[str] = None
    # results of the verbs called in instant mode
    results: List[pydantic.BaseModel] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class InstantResponse:
    text: str
    results: List[pydantic.BaseModel]
    messages: List[Any]

    @property
    def sounds(self) -> List[SoundResult]:
        return [r for r in self.results if isinstance(r, SoundResult)]


class GeneratedCode(pydantic.BaseModel):
    """final output in code generation mode"""
    description: str = Field(description='short description of what the transformation does, including any assumption made')
    input_fields: List[str] = Field(description='row fields the code reads')
    output_fields: List[str] = Field(description='row fields the code returns')
    code: str = Field(description='python source defining transform(clt, row) -> dict')


def _call_api(function, *args, **kwargs):
    """run a CLT-AI function, turning invalid requests into retries so the model can fix them"""
    try:
        return function(*args, **kwargs)
    except (CltAIError, ValueError) as e:
        raise ModelRetry(f'{type(e).__name__}: {e}') from e


# tools
# =====

def list_voices(ctx: RunContext[AgentDeps], language: Optional[str] = None, audio_language: Optional[str] = None,
        service: Optional[str] = None, gender: Optional[str] = None, name_contains: Optional[str] = None) -> Dict[str, Any]:
    """list TTS voices. Filter by language code (e.g. "ja"), locale (e.g. "en_GB"), service (e.g. "Azure"),
    gender ("Male"/"Female") and voice name substring. Use filters, the full list is very long."""
    voices = _call_api(ctx.deps.clt.list_voices, language=language, audio_language=audio_language,
        service=service, gender=gender, name_contains=name_contains)
    return _limited([v.model_dump(mode='json') for v in voices], MAX_LISTED_ITEMS)


def describe_voice_options(ctx: RunContext[AgentDeps], service: str, voice_name: Optional[str] = None,
        voice_key: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """JSON schema of the options (speed, pitch, style...) accepted by a voice"""
    return _call_api(ctx.deps.clt.describe_voice_options, service, voice_name=voice_name, voice_key=voice_key)


def list_audio_languages(ctx: RunContext[AgentDeps], language: Optional[str] = None) -> List[Dict[str, Any]]:
    """locales (accents) available for a language code, e.g. language="en" gives en_US, en_GB, en_AU..."""
    return [a.model_dump() for a in _call_api(ctx.deps.clt.list_audio_languages, language)]


def find_languages(ctx: RunContext[AgentDeps], name_contains: str) -> List[Dict[str, Any]]:
    """find language codes by name, e.g. "chinese" or "portuguese" """
    return [l.model_dump() for l in ctx.deps.clt.list_languages() if name_contains.lower() in l.name.lower() or name_contains.lower() == l.code.lower()]


def list_translation_services(ctx: RunContext[AgentDeps], source_language: str, target_language: str) -> List[Dict[str, Any]]:
    """translation services able to translate between two language codes, in order of preference"""
    return [s.model_dump(mode='json') for s in _call_api(ctx.deps.clt.list_translation_services, source_language, target_language)]


def list_transliterations(ctx: RunContext[AgentDeps], language: Optional[str] = None, service: Optional[str] = None,
        name_contains: Optional[str] = None) -> Dict[str, Any]:
    """transliteration options (pinyin, jyutping, IPA, romaji...) for a language code"""
    options = _call_api(ctx.deps.clt.list_transliterations, language=language, service=service, name_contains=name_contains)
    return _limited([o.model_dump(mode='json') for o in options], MAX_LISTED_ITEMS)


def describe_service_options(ctx: RunContext[AgentDeps], verb: str, service: str) -> Dict[str, Any]:
    """JSON schema of the options accepted by a service for verb "transcribe" or "llm" """
    if verb == 'transcribe':
        return _call_api(ctx.deps.clt.describe_transcription_options, service)
    if verb == 'llm':
        return _call_api(ctx.deps.clt.describe_llm_options, service)
    raise ModelRetry('verb must be "transcribe" or "llm", for sound use describe_voice_options')


DISCOVERY_TOOLS = [list_voices, describe_voice_options, list_audio_languages, find_languages,
    list_translation_services, list_transliterations, describe_service_options]


# instant mode tools: the CLT-AI verbs

def sound(ctx: RunContext[AgentDeps], request: SoundRequest) -> SoundResult:
    """generate audio for some text. The audio file is delivered to the user automatically"""
    result = _call_api(ctx.deps.clt.sound, request)
    ctx.deps.results.append(result)
    return result


def translate(ctx: RunContext[AgentDeps], request: TranslateRequest) -> TranslateResult:
    """translate text from one language to another"""
    result = _call_api(ctx.deps.clt.translate, request)
    ctx.deps.results.append(result)
    return result


def transliterate(ctx: RunContext[AgentDeps], request: TransliterateRequest) -> TransliterateResult:
    """transliterate text: pinyin, jyutping, IPA, romaji..."""
    result = _call_api(ctx.deps.clt.transliterate, request)
    ctx.deps.results.append(result)
    return result


def transcribe(ctx: RunContext[AgentDeps], request: TranscribeRequest) -> TranscribeResult:
    """convert an audio file into text"""
    result = _call_api(ctx.deps.clt.transcribe, request)
    ctx.deps.results.append(result)
    return result


def llm(ctx: RunContext[AgentDeps], request: LlmRequest) -> LlmResult:
    """ask a separate LLM call to generate text. Only for tasks the other tools can't do and that you
    shouldn't answer yourself, e.g. when the user explicitly asks for a specific model"""
    result = _call_api(ctx.deps.clt.llm, request)
    ctx.deps.results.append(result)
    return result


INSTANT_TOOLS = [sound, translate, transliterate, transcribe]


# code generation mode tools

def run_python(ctx: RunContext[AgentDeps], code: str) -> str:
    """execute python code to explore or test the CLT-AI API. A configured client is available as `clt`,
    and the request models are importable from cloudlanguagetools.cltai. Returns stdout, or the traceback.
    Discovery and validate_* functions are free, verbs (clt.sound, clt.translate...) make real paid API calls."""
    namespace = build_namespace()
    namespace['clt'] = ctx.deps.clt
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            exec(compile(code, '<run_python>', 'exec'), namespace)
    except Exception:
        return _truncate(stdout.getvalue() + '\n' + traceback.format_exc())
    output = stdout.getvalue()
    return _truncate(output) if output else '(no output, use print() to see values)'


def search_source(ctx: RunContext[AgentDeps], command: str) -> str:
    """run a read-only shell command to explore the cloudlanguagetools source code. Allowed commands:
    rg, grep, ls, cat, head, tail, find, wc (no pipes or redirections). The working directory is the
    cloudlanguagetools package: cltai/ contains the CLT-AI API, the other modules are service implementations
    (azure.py, google.py...). Example: rg -n "def get_transliteration" mandarincantonese.py"""
    try:
        args = shlex.split(command)
    except ValueError as e:
        raise ModelRetry(f'could not parse command: {e}')
    if len(args) == 0 or args[0] not in ALLOWED_SHELL_COMMANDS:
        raise ModelRetry(f'only these commands are allowed: {", ".join(ALLOWED_SHELL_COMMANDS)}. No pipes or redirections.')
    # basic guard against options which execute or write, full sandboxing is a separate step
    if args[0] == 'find' and any(a in ('-delete', '-exec', '-execdir', '-ok', '-okdir') or a.startswith('-fprint') for a in args[1:]):
        raise ModelRetry('find may only be used read-only')
    if args[0] == 'rg' and any(a.startswith('--pre') for a in args[1:]):
        raise ModelRetry('rg --pre is not allowed')
    try:
        completed = subprocess.run(args, cwd=SOURCE_ROOT, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return 'command timed out'
    except FileNotFoundError:
        raise ModelRetry(f'{args[0]} is not installed here, use another command (e.g. grep -rn instead of rg)')
    output = completed.stdout + (f'\n[stderr]\n{completed.stderr}' if completed.stderr else '')
    return _truncate(output) if output.strip() else f'(no output, exit code {completed.returncode})'


def ask_user(ctx: RunContext[AgentDeps], question: str) -> str:
    """ask the user a clarifying question, e.g. which column / field contains the source text.
    Only ask when the instruction is ambiguous and a wrong guess would make the transformation useless."""
    if ctx.deps.ask_user is None:
        return NO_USER_ANSWER
    return ctx.deps.ask_user(question)


def test_transform(ctx: RunContext[AgentDeps], code: str, row: Dict[str, Any]) -> str:
    """compile transformation code and run transform(clt, row) on one sample row. Makes real API calls.
    Returns the output dict (as JSON) or the error."""
    try:
        function = compile_transform(code)
        output = function(ctx.deps.clt, row)
    except Exception:
        return _truncate(traceback.format_exc())
    if not isinstance(output, dict):
        return f'error: transform must return a dict, got {type(output).__name__}'
    return _truncate(json.dumps({k: (v.model_dump(mode='json') if isinstance(v, pydantic.BaseModel) else v)
        for k, v in output.items()}, ensure_ascii=False, indent=1, default=str))


CODEGEN_TOOLS = [run_python, search_source, ask_user, test_transform]


# instructions
# ============

COMMON_INSTRUCTIONS = """You are the CLT-AI Agent. You help language learners by processing text with the CLT-AI API
(Cloud Language Tools), which gives access to many cloud services for text to speech, translation,
transliteration, transcription and LLM text generation.

Choose the right verb:
- sound: the user wants audio / pronunciation
- translate: translation from one language to another
- transliterate: pinyin, jyutping, IPA, romaji, romanization, converting scripts
- transcribe: convert audio into text
- llm: anything else (explanations, example sentences, definitions, grammar notes...)

{default_rules}
When the user asks for a specific service, voice, gender or accent, look it up with the discovery tools
and use exactly that. Invalid requests return an error which lists valid alternatives: fix the request and retry.
"""

CODEGEN_INSTRUCTIONS = """
You are in code generation mode: write python code which implements the user's instruction as a repeatable
transformation that will be applied to many rows (Anki notes or spreadsheet rows).

The code must define:

    def transform(clt, row: dict) -> dict:

- `row` maps field / column names to their values (strings, may contain HTML in Anki, may be empty).
- return a dict mapping output field names to values: str for text, the SoundResult object for audio.
  Only return the output fields, never return input fields unless the instruction says to overwrite them.
- if the input is empty or blank, return {{}}.
- import what you need from cloudlanguagetools.cltai at the top of the code, e.g.
  from cloudlanguagetools.cltai import SoundRequest, TranslateRequest
- only use `clt` for language operations, no other network access, no printing, no file writing.
- pin the choices: explore with the discovery tools / clt.validate_*() first, then hardcode the resolved
  service, voice_key, transliteration_key etc. in the request, so the transformation gives the same result every time.
- keep the code short and readable, the user may look at it.

Available fields: {available_fields}
{sample_row}
Workflow: explore the API (discovery tools, run_python, search_source), write the code, test it with
test_transform on a sample row, fix any error, then return the final code with input_fields / output_fields.
If it is not clear which field holds the input or where the output should go, use ask_user.

CLT-AI API reference:
{api_description}
"""

INSTANT_INSTRUCTIONS = """
You are in instant mode (chatbot): call the tools directly to fulfill the user's request and reply with the results.
Audio generated with the sound tool is sent to the user automatically, don't include file paths in your reply.
Keep replies concise, present each result clearly (e.g. translation, pinyin, then a note that audio is attached).
{standing_instructions}
"""


class CltAIAgent():
    """the CLT-AI Agent. clt is a CLT-AI client, model is an OpenAI model name or a pydantic-ai Model."""

    def __init__(self, clt: CltAIClientV1, model: str | pydantic_ai.models.Model = DEFAULT_AGENT_MODEL,
            openai_api_key: str = None, retries: int = 4, request_limit: int = 40):
        self.clt = clt
        self.retries = retries
        self.usage_limits = UsageLimits(request_limit=request_limit)
        if isinstance(model, str):
            model = OpenAIResponsesModel(model, provider=OpenAIProvider(api_key=openai_api_key or self._get_openai_api_key()))
        self.model = model

    def _get_openai_api_key(self):
        openai_service = self.clt.manager.services.get(cloudlanguagetools.constants.Service.OpenAI)
        api_key = getattr(openai_service, 'api_key', None) or os.environ.get('OPENAI_API_KEY')
        if api_key is None:
            raise CltAIError('no OpenAI API key: configure the OpenAI service or set OPENAI_API_KEY')
        return api_key

    def _common_instructions(self):
        return COMMON_INSTRUCTIONS.format(default_rules=defaults.DEFAULT_RULES_TEXT)

    # code generation mode
    # ====================

    def build_codegen_agent(self, available_fields: List[str], sample_row: Optional[Dict[str, Any]]) -> Agent:
        instructions = self._common_instructions() + CODEGEN_INSTRUCTIONS.format(
            available_fields=', '.join(available_fields) if available_fields else '(not specified, ask the user if needed)',
            sample_row=f'Sample row: {json.dumps(sample_row, ensure_ascii=False)}' if sample_row else '',
            api_description=self.clt.describe_api())
        agent = Agent(self.model, deps_type=AgentDeps, output_type=GeneratedCode, instructions=instructions,
            tools=DISCOVERY_TOOLS + CODEGEN_TOOLS, retries=self.retries)

        @agent.output_validator
        def validate_code(ctx: RunContext[AgentDeps], output: GeneratedCode) -> GeneratedCode:
            try:
                compile_transform(output.code)
            except CltAIError as e:
                raise ModelRetry(str(e))
            if ctx.deps.available_fields:
                unknown = [f for f in output.input_fields if f not in ctx.deps.available_fields]
                if unknown:
                    raise ModelRetry(f'input_fields {unknown} are not available fields: {ctx.deps.available_fields}')
            return output

        return agent

    def generate_transformation(self, instruction: str, available_fields: List[str] = None,
            sample_row: Dict[str, Any] = None, ask_user: Callable[[str], str] = None) -> Transformation:
        """code generation mode: create a repeatable Transformation implementing the instruction.
        available_fields: names of the row fields / columns. sample_row: example input used for testing.
        ask_user: callback(question) -> answer, for clarifying questions (None: the agent makes its best guess)."""
        available_fields = available_fields or (list(sample_row.keys()) if sample_row else [])
        deps = AgentDeps(clt=self.clt, available_fields=available_fields, sample_row=sample_row, ask_user=ask_user)
        agent = self.build_codegen_agent(available_fields, sample_row)
        result = agent.run_sync(instruction, deps=deps, usage_limits=self.usage_limits)
        output = result.output
        return Transformation(api_version=self.clt.api_version, instruction=instruction, description=output.description,
            input_fields=output.input_fields, output_fields=output.output_fields, code=output.code)

    # instant mode
    # ============

    def build_instant_agent(self, standing_instructions: Optional[str], allow_llm: bool) -> Agent:
        instructions = self._common_instructions() + INSTANT_INSTRUCTIONS.format(
            standing_instructions=f'Standing instructions from the user, apply them to every message:\n{standing_instructions}'
                if standing_instructions else '')
        tools = DISCOVERY_TOOLS + INSTANT_TOOLS + ([llm] if allow_llm else [])
        return Agent(self.model, deps_type=AgentDeps, output_type=str, instructions=instructions,
            tools=tools, retries=self.retries)

    def run_instant(self, message: str, standing_instructions: str = None, message_history: List[Any] = None,
            allow_llm: bool = True) -> InstantResponse:
        """instant mode: fulfill a chat message by calling the CLT-AI verbs as tools.
        standing_instructions: user instructions applied to every message, e.g. "if I type chinese text,
        give me the translation, pinyin and audio". message_history: InstantResponse.messages of the previous turn."""
        deps = AgentDeps(clt=self.clt, standing_instructions=standing_instructions)
        agent = self.build_instant_agent(standing_instructions, allow_llm)
        result = agent.run_sync(message, deps=deps, message_history=message_history, usage_limits=self.usage_limits)
        return InstantResponse(text=result.output, results=deps.results, messages=result.all_messages())
