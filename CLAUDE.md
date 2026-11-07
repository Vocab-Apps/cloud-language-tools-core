# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment
- Python 3.14, managed with `uv`. `.python-version` pins the interpreter.
- `uv sync` creates/updates the environment. `.venv` is a gitignored symlink to
  `/home/luc/python-env/cloud-language-tools-core`; if that target is ever deleted,
  recreate it with `uv venv --python 3.14 /home/luc/python-env/cloud-language-tools-core`
  and re-create the symlink, otherwise `uv sync` replaces the dangling symlink with a
  real directory.

### Testing
- Run all tests: `uv run pytest`
- Run tests in parallel: `uv run pytest -n auto` (requires pytest-xdist)
- Run specific test: `uv run pytest tests/test_audio.py`
- Run with logging output: `uv run pytest --log-cli-level=INFO`
- pytest config lives in `[tool.pytest.ini_options]` in `pyproject.toml` (there is no pytest.ini)
- **Audio tests make real API calls**: Tests in `test_audio.py` will invoke cloud APIs and may incur costs
  - This is normal and expected behavior for integration testing
  - Requires `CLOUDLANGUAGETOOLS_CORE_KEY` to decrypt the service keys in `cloudlanguagetools/keys.py`
  - Only use `@skip_unreliable_clt_test()` for services that are genuinely unreliable
- Tests should be located in the `tests/` directory
- Python imports should always be placed at the top of the file.

### Package Management
- Set up / update the environment: `uv sync`
- Dependencies are declared in `pyproject.toml`: runtime in `[project.dependencies]`,
  dev/test in `[dependency-groups] dev`. There is no requirements.txt, and the
  `clt_requirements` helper package no longer exists.
- Add a dependency: `uv add <package>` / `uv add --dev <package>`
- `uv.lock` is committed. Regenerate with `uv lock` (or `uv lock --upgrade-package X`)
  and commit it alongside the change.

### Building and Release
- Build and release (with version bump): `./package.sh [major|minor|patch]`
  - Bumps `[project].version` in pyproject.toml via `bump`, re-locks, commits, tags,
    builds sdist + wheel with `uv build`, uploads with `uv publish`
  - Builds the Docker image and runs the tests in Docker
- Manual build: `uv build` (produces sdist + wheel in `dist/`)
- `bump` rewrites the *first* `version = "..."` line in pyproject.toml, so do not
  introduce another one above `[project].version`.

### Docker
- Build core Docker image: `./build_clt_core_docker.sh VERSION` (uses `Dockerfile`)
  - Based on `python:3.14-slim-trixie`; dependencies are installed with
    `uv pip install --system` into global site-packages, so downstream images that do
    `FROM vocabai/cloud-language-tools-core:VERSION` keep using plain `pip3`/`python3`.
  - `WORKDIR` is left at `/` because the downstream `cloud-language-tools` image
    COPYs into `/` and uses `ENTRYPOINT ["./start.sh"]`.
- Run Docker tests: `./run_clt_docker.test.sh VERSION`
- There is no `clt-requirements` image any more.

### Notes
- The Wenlin dictionary comes from the PyPI package `cloud-language-tools-wenlin`
  (import name `clt_wenlin`), which bundles the sqlite DB inside the wheel. It lives in
  its own repo at ~/code/python/cloud-language-tools-wenlin.
- `pydub` imports the stdlib `audioop` module, which was removed in Python 3.13, so
  `audioop-lts` is a declared runtime dependency.
- `utils/debug_3.py` imports `convertkit` lazily; it is deliberately not a declared dependency.
- Google and Gemini only support API keys (no service accounts), sent in the `x-goog-api-key` header.
- Gemini TTS (`gemini.py`): every model calls the Gemini API `generateContent` endpoint
  (`generativelanguage.googleapis.com`) with a Gemini API key. Model names are mapped with
  `GEMINI_API_MODEL_NAMES` (e.g. `gemini-2.5-flash-tts` -> `gemini-2.5-flash-preview-tts`); any other
  model, including the former Cloud-TTS-only `gemini-2.5-flash-lite-preview-tts`, raises InputError.
  The 3.8 models take the style prompt in `speechMetadata.style`; older models reject it, so the
  prompt is prefixed to the text (`"<prompt>: <text>"`) with `prebuiltVoiceConfig`.
  generateContent returns WAV or headerless PCM, transcoded locally.
  (The Gemini models served through Cloud Text-to-Speech / Gemini Enterprise need IAM permissions
  that an API key can't carry, which is why they are not used.)
- Google (`google.py`): TTS through the Cloud Text-to-Speech SDK with `ClientOptions(api_key=...)`;
  translation through the Cloud Translation v2 REST API (`requests`, no `google-cloud-translate` dependency).

## Architecture Overview

### Service Layer Architecture
The codebase follows a plugin-based service architecture where each cloud provider is implemented as a separate service module:

- **ServiceManager** (`servicemanager.py`): Central registry that loads and manages all available services
- **Service Base Class** (`service.py`): Abstract base class defining common interface for all services
- **Individual Services**: Each cloud provider (Azure, Google, OpenAI, etc.) implements the Service interface

### Core Components

**Service Types**:
- Translation services (text-to-text)
- Text-to-speech (TTS) services 
- Transliteration services
- Dictionary lookup services
- Chat/LLM services

**Key Data Structures**:
- `TtsVoice`: Represents available voices for TTS
- `TranslationLanguage`: Language pairs for translation
- `TransliterationLanguage`: Language pairs for transliteration
- `ServicesConfiguration` (`configuration.py`): versioned pydantic model enabling/configuring services

**Request Flow**:
1. ServiceManager instantiates and configures only the services enabled in the `ServicesConfiguration`
2. Client requests routed through ServiceManager to appropriate service
3. Each service handles authentication, API calls, and response formatting
4. Common error handling through `cloudlanguagetools.errors`

### Service Implementation Pattern
Each service module (e.g., `azure.py`, `google.py`) follows this pattern:
- Inherits from `Service` base class
- Implements service-specific API authentication
- Defines available voices/languages as class constants
- Implements required methods: `get_tts_audio()`, `get_translation()`, etc.
- Uses common utilities from base class for HTTP requests and audio processing

### Configuration and Keys
- `cloudlanguagetools/configuration.py`: `ServicesConfiguration` (version 1) has one optional sub-model per
  service (`azure`, `google`, `gemini`, `deepl`, ...). Present = enabled; absent = disabled, never consulted for
  lists, and `ServiceManager.get_service()` raises `errors.ServiceNotEnabledError` (a `PermanentError`).
  Secrets are `SecretStr` (hidden in repr, serialized in clear by `dump_json()`).
- `ServiceManager(configuration)` or `manager.configure(configuration)` (re-configuring replaces the services and
  clears the per-instance list cache). `configure_default()` / `configure_services()` no longer exist.
- Each `Service.configure(config)` receives its typed sub-model, not a dict.
- `AzureConfig.region` / `AmazonConfig.region` are `AzureRegion` / `AmazonRegion` StrEnums (exact match, e.g. `eastus`,
  `us-east-1`). Azure: the Speech service regions from the Azure docs. Amazon: Polly's regions from botocore;
  `tests/test_configuration.py` fails if botocore's Polly region list changes, then update `AmazonRegion`.
- Keyless services (Epitran, Spacy, PyThaiNLP, MandarinCantonese, Wenlin) are enabled with an empty sub-model,
  see `ServicesConfiguration.with_keyless_services()`.
- `GoogleConfig` and `GeminiConfig` are separate models (no shared base other than `ServiceConfig`), each with
  a required `api_key`. No service account support, no `GOOGLE_APPLICATION_CREDENTIALS`.
- API key files `.google_tts_translation_api_key` / `.gemini_api_key` (gitignored) hold the raw keys.
- Backend: `encryption.load_configuration()` decrypts `keys.py` with `EncryptionSettings` (from
  `CLOUDLANGUAGETOOLS_CORE_KEY`). `utils/service_keys.py --action decrypt_write_json|encrypt` round-trips it
  through the gitignored `services_configuration.json`. The pre-versioned format (keyed by Service enum name)
  is not supported and fails validation.
- Mock services: enable `test_service_a` / `test_service_b` in the configuration (see `tests/test_mock_services.py`);
  the `CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES` environment variable is gone.

### Testing Strategy
- Comprehensive test suite covering all service types
- Mock services (`test_services.py`) for testing without API calls; `tests/test_configuration.py` covers the
  configuration model, enabling/disabling and encryption without API calls
- Integration tests against real APIs (when keys available)
- Audio processing tests using `pydub` for validation
- **Audio tests**: Located in `tests/test_audio.py` and follow the pattern of existing tests like `test_mandarin_amazon`
  - Make actual API calls and verify audio generation works correctly
  - **Normal behavior**: It's expected and acceptable for tests to invoke cloud APIs and incur costs
  - **@skip_unreliable_clt_test()**: Only use this decorator for services that are genuinely unreliable or frequently fail
  - **Environment variable**: Some legacy tests may require `CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes` but new services should not
- if you need to write some temporary code for debugging, add a new function in @utils/debug.py