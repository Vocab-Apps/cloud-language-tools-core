# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- Run all tests: `pytest`
- Run tests in parallel: `pytest -n auto` (requires pytest-xdist)
- Run specific test: `pytest tests/test_audio.py`
- Run with logging output: `pytest --log-cli-level=INFO`

### Package Management
- Install development dependencies: `pip install -r requirements.dev.txt`
- Install package in development mode: `pip install -e .`

### Building and Release
- Build and release (with version bump): `./package.sh [major|minor|patch]`
  - Bumps version, commits, tags, builds Python package, uploads to PyPI
  - Builds Docker image and runs tests
- Manual build: `python setup.py sdist`
- Upload to PyPI: `twine upload dist/cloudlanguagetools-VERSION.tar.gz`

### Docker
- Build core Docker image: `./build_clt_core_docker.sh VERSION`
- Run Docker tests: `./run_clt_docker.test.sh VERSION`

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
- Audio tests should be in `tests/test_audio.py` and should follow the same pattern as for example `test_mandarin_amazon`