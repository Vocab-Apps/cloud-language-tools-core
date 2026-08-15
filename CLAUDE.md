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
  - Requires valid API keys in `services_configuration.json`
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
- Service configurations stored in `services_configuration.json`

**Request Flow**:
1. ServiceManager loads all available services on initialization
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
- Service API keys stored in `services_configuration.json` (dev/test only)
- Production uses encrypted key management through `encryption.py`
- Each service can be configured independently
- Test services available via `CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes`

### Testing Strategy
- Comprehensive test suite covering all service types
- Mock services (`test_services.py`) for testing without API calls
- Integration tests against real APIs (when keys available)
- Audio processing tests using `pydub` for validation
- **Audio tests**: Located in `tests/test_audio.py` and follow the pattern of existing tests like `test_mandarin_amazon`
  - Make actual API calls and verify audio generation works correctly
  - **Normal behavior**: It's expected and acceptable for tests to invoke cloud APIs and incur costs
  - **@skip_unreliable_clt_test()**: Only use this decorator for services that are genuinely unreliable or frequently fail
  - **Environment variable**: Some legacy tests may require `CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes` but new services should not
- if you need to write some temporary code for debugging, add a new function in @utils/debug.py