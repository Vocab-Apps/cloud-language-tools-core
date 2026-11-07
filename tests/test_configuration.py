import os
import sys
import json
import base64
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import pydantic
import cryptography.fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.configuration
import cloudlanguagetools.encryption
import cloudlanguagetools.errors
import cloudlanguagetools.servicemanager
import cloudlanguagetools.google
import cloudlanguagetools.gemini
from cloudlanguagetools.configuration import (
    ServicesConfiguration, AzureConfig, DeepLConfig, GoogleConfig, GeminiConfig, GoogleServiceAccount,
    EpitranConfig,
)
from cloudlanguagetools.constants import Service


def generate_service_account_info(project_id='test-project'):
    """A structurally valid service account key, with a real (throwaway) RSA private key."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()).decode('utf-8')
    return {
        'type': 'service_account',
        'project_id': project_id,
        'private_key_id': 'abcdef',
        'private_key': private_key_pem,
        'client_email': f'tts@{project_id}.iam.gserviceaccount.com',
        'client_id': '1234',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }


SERVICE_ACCOUNT_INFO = generate_service_account_info()


class TestServicesConfigurationModel(unittest.TestCase):
    def test_empty_configuration(self):
        configuration = ServicesConfiguration()
        self.assertEqual(configuration.version, 1)
        self.assertEqual(configuration.enabled_services(), {})
        self.assertFalse(configuration.is_enabled(Service.Azure))

    def test_enabled_services(self):
        configuration = ServicesConfiguration(
            azure=AzureConfig(api_key='azure-key', region='eastus'),
            epitran=EpitranConfig())
        self.assertEqual(list(configuration.enabled_services().keys()), [Service.Azure, Service.Epitran])
        self.assertTrue(configuration.is_enabled(Service.Azure))
        self.assertFalse(configuration.is_enabled(Service.Google))

    def test_with_keyless_services(self):
        configuration = ServicesConfiguration.with_keyless_services(deepl=DeepLConfig(api_key='deepl-key'))
        self.assertEqual(set(configuration.enabled_services().keys()), {
            Service.Epitran, Service.PyThaiNLP, Service.Spacy, Service.MandarinCantonese, Service.Wenlin, Service.DeepL})

    def test_every_service_field_is_mapped(self):
        model_fields = set(ServicesConfiguration.model_fields.keys()) - {'version'}
        self.assertEqual(model_fields, set(cloudlanguagetools.configuration.SERVICE_FIELDS.keys()))
        self.assertEqual(set(cloudlanguagetools.configuration.SERVICE_FIELDS.values()),
            set(cloudlanguagetools.servicemanager.SERVICE_CLASSES.keys()))

    def test_empty_api_key_rejected(self):
        with self.assertRaises(pydantic.ValidationError):
            AzureConfig(api_key='', region='eastus')
        with self.assertRaises(pydantic.ValidationError):
            AzureConfig(api_key='key', region='   ')

    def test_missing_field_rejected(self):
        with self.assertRaises(pydantic.ValidationError):
            ServicesConfiguration.model_validate({'version': 1, 'azure': {'api_key': 'key'}})

    def test_unknown_fields_rejected(self):
        # typo in a service name
        with self.assertRaises(pydantic.ValidationError):
            ServicesConfiguration.model_validate({'version': 1, 'azur': {'api_key': 'key', 'region': 'eastus'}})
        # legacy key name
        with self.assertRaises(pydantic.ValidationError):
            ServicesConfiguration.model_validate({'version': 1, 'deepl': {'key': 'key'}})

    def test_unsupported_version_rejected(self):
        with self.assertRaises(pydantic.ValidationError):
            ServicesConfiguration.model_validate({'version': 2})

    def test_secrets_hidden_in_repr(self):
        configuration = ServicesConfiguration(azure=AzureConfig(api_key='super-secret-key', region='eastus'))
        self.assertNotIn('super-secret-key', repr(configuration))
        self.assertNotIn('super-secret-key', str(configuration))

    def test_json_round_trip(self):
        configuration = ServicesConfiguration(
            azure=AzureConfig(api_key='super-secret-key', region='eastus'),
            google=GoogleConfig(service_account=SERVICE_ACCOUNT_INFO),
            mandarin_cantonese=cloudlanguagetools.configuration.MandarinCantoneseConfig())
        json_str = configuration.dump_json()
        data = json.loads(json_str)
        # secrets are serialized in clear, disabled services are omitted
        self.assertEqual(data['azure'], {'api_key': 'super-secret-key', 'region': 'eastus'})
        self.assertEqual(data['mandarin_cantonese'], {})
        self.assertNotIn('deepl', data)
        self.assertEqual(data['google']['service_account']['client_id'], '1234')
        self.assertEqual(ServicesConfiguration.model_validate_json(json_str), configuration)

    def test_service_account_from_json_text(self):
        service_account = GoogleServiceAccount.model_validate(json.dumps(SERVICE_ACCOUNT_INFO))
        self.assertEqual(service_account.project_id, 'test-project')
        self.assertEqual(service_account.get_info(), SERVICE_ACCOUNT_INFO)

    def test_service_account_invalid(self):
        with self.assertRaises(pydantic.ValidationError):
            GoogleServiceAccount.model_validate('not json')
        with self.assertRaises(pydantic.ValidationError):
            GoogleServiceAccount.model_validate({**SERVICE_ACCOUNT_INFO, 'private_key': ''})
        with self.assertRaises(pydantic.ValidationError):
            GoogleServiceAccount.model_validate({**SERVICE_ACCOUNT_INFO, 'type': 'authorized_user'})


class TestLegacyConfiguration(unittest.TestCase):
    LEGACY = {
        'Azure': {'region': 'eastus', 'key': 'azure-key'},
        'Google': {'key': base64.b64encode(json.dumps(SERVICE_ACCOUNT_INFO).encode('utf-8')).decode('utf-8')},
        'Amazon': {'AWS_ACCESS_KEY_ID': 'aws-id', 'AWS_SECRET_ACCESS_KEY': 'aws-secret', 'AWS_DEFAULT_REGION': 'us-east-1'},
        'DeepL': {'key': 'deepl-key'},
        'Voicen': {'key': 'voicen-key'},
    }

    def test_from_legacy_dict(self):
        configuration = cloudlanguagetools.configuration.load_configuration(self.LEGACY)
        self.assertEqual(configuration.azure.api_key.get_secret_value(), 'azure-key')
        self.assertEqual(configuration.amazon.access_key_id, 'aws-id')
        self.assertEqual(configuration.amazon.secret_access_key.get_secret_value(), 'aws-secret')
        self.assertEqual(configuration.amazon.region, 'us-east-1')
        self.assertEqual(configuration.deepl.api_key.get_secret_value(), 'deepl-key')
        self.assertEqual(configuration.google.service_account.get_info(), SERVICE_ACCOUNT_INFO)
        # legacy behavior: gemini uses the google service account, keyless services are enabled
        self.assertEqual(configuration.gemini.service_account, configuration.google.service_account)
        for service in [Service.Epitran, Service.PyThaiNLP, Service.Spacy, Service.MandarinCantonese, Service.Wenlin]:
            self.assertTrue(configuration.is_enabled(service))
        self.assertIsNone(configuration.watson)

    def test_versioned_data_not_treated_as_legacy(self):
        with self.assertRaises(pydantic.ValidationError):
            cloudlanguagetools.configuration.load_configuration({'version': 1, **self.LEGACY})


class TestServiceManagerConfiguration(unittest.TestCase):
    def test_no_configuration(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager()
        self.assertEqual(manager.services, {})
        self.assertEqual(manager.get_tts_voice_list(), [])
        self.assertEqual(manager.get_translation_language_list(), [])
        with self.assertRaises(cloudlanguagetools.errors.ServiceNotEnabledError):
            manager.get_translation('text', 'Azure', 'en', 'fr')

    def test_configure_rejects_dict(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager()
        with self.assertRaises(TypeError):
            manager.configure({'Azure': {'key': 'key', 'region': 'eastus'}})

    def test_only_enabled_services_consulted(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(
            ServicesConfiguration(test_service_a=cloudlanguagetools.configuration.TestServiceConfig()))
        self.assertEqual(manager.get_enabled_services(), [Service.TestServiceA])
        self.assertTrue(manager.is_enabled('TestServiceA'))
        self.assertFalse(manager.is_enabled('TestServiceB'))
        services = {voice.service for voice in manager.get_tts_voice_list()}
        self.assertEqual(services, {Service.TestServiceA})
        services = {language.service for language in manager.get_translation_language_list()}
        self.assertEqual(services, {Service.TestServiceA})
        self.assertEqual(list(manager.get_all_translations('text', 'fr', 'en').keys()), ['TestServiceA'])

    def test_disabled_service_raises(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(
            ServicesConfiguration(test_service_a=cloudlanguagetools.configuration.TestServiceConfig()))
        calls = [
            lambda: manager.get_tts_audio('text', 'TestServiceB', {}, {}),
            lambda: manager.get_translation('text', 'TestServiceB', 'fr', 'en'),
            lambda: manager.get_transliteration('text', 'TestServiceB', {}),
            lambda: manager.get_tokenization('text', 'Spacy', {}),
            lambda: manager.get_dictionary_lookup('text', 'TestServiceB', {}),
            lambda: manager.get_pinyin('text', False, False),
            lambda: manager.openai_single_prompt('text'),
            lambda: manager.detect_language(['text']),
        ]
        for call in calls:
            with self.assertRaises(cloudlanguagetools.errors.ServiceNotEnabledError):
                call()
        # get_tts_audio_v5 lets the PermanentError through, without wrapping it
        with self.assertRaises(cloudlanguagetools.errors.ServiceNotEnabledError):
            manager.get_tts_audio_v5('text', 'TestServiceB', {}, {})
        self.assertTrue(issubclass(cloudlanguagetools.errors.ServiceNotEnabledError, cloudlanguagetools.errors.PermanentError))

    def test_reconfigure_clears_cache(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(
            ServicesConfiguration(test_service_a=cloudlanguagetools.configuration.TestServiceConfig()))
        self.assertEqual({voice.service for voice in manager.get_tts_voice_list()}, {Service.TestServiceA})
        manager.configure(ServicesConfiguration(test_service_b=cloudlanguagetools.configuration.TestServiceConfig()))
        self.assertEqual({voice.service for voice in manager.get_tts_voice_list()}, {Service.TestServiceB})
        with self.assertRaises(cloudlanguagetools.errors.ServiceNotEnabledError):
            manager.get_translation('text', 'TestServiceA', 'fr', 'en')

    def test_cache_per_manager_instance(self):
        manager_a = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(test_service_a=cloudlanguagetools.configuration.TestServiceConfig()))
        manager_b = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(test_service_b=cloudlanguagetools.configuration.TestServiceConfig()))
        self.assertEqual({voice.service for voice in manager_a.get_tts_voice_list()}, {Service.TestServiceA})
        self.assertEqual({voice.service for voice in manager_b.get_tts_voice_list()}, {Service.TestServiceB})

    def test_services_receive_configuration(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(
            azure=AzureConfig(api_key='azure-key', region='westeurope'),
            deepl=DeepLConfig(api_key='deepl-key'),
            epitran=EpitranConfig(base_url='http://localhost:8042')))
        self.assertEqual(manager.services[Service.Azure].key, 'azure-key')
        self.assertEqual(manager.services[Service.Azure].region, 'westeurope')
        self.assertEqual(manager.services[Service.DeepL].api_key, 'deepl-key')
        self.assertEqual(manager.services[Service.Epitran].base_url, 'http://localhost:8042')


class TestGoogleGeminiConfiguration(unittest.TestCase):
    def test_google_in_memory_credentials(self):
        previous = os.environ.pop('GOOGLE_APPLICATION_CREDENTIALS', None)
        try:
            service = cloudlanguagetools.google.GoogleService()
            service.configure(GoogleConfig(service_account=SERVICE_ACCOUNT_INFO))
            # no key file written, no environment variable set
            self.assertNotIn('GOOGLE_APPLICATION_CREDENTIALS', os.environ)
            self.assertEqual(service.credentials.service_account_email, SERVICE_ACCOUNT_INFO['client_email'])
            self.assertIsNone(service.api_key)
            # the transport may re-scope (copy) the credentials, so compare the account
            self.assertEqual(service.get_client()._transport._credentials.service_account_email, SERVICE_ACCOUNT_INFO['client_email'])
        finally:
            if previous is not None:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = previous

    def test_google_service_account_translation_uses_bearer_token(self):
        service = cloudlanguagetools.google.GoogleService()
        service.configure(GoogleConfig(service_account=SERVICE_ACCOUNT_INFO))
        service.credentials = MagicMock(valid=True, token='bearer-token')
        with patch('cloudlanguagetools.google.requests.request', return_value=_json_response(
                {'data': {'translations': [{'translatedText': 'Hello &amp; welcome'}]}})) as mock_request:
            self.assertEqual(service.get_translation('Bonjour', 'fr', 'en'), 'Hello & welcome')
        self.assertEqual(mock_request.call_args.kwargs['headers'], {'Authorization': 'Bearer bearer-token'})

    def test_credentials_exactly_one(self):
        for config_class in [GoogleConfig, GeminiConfig]:
            with self.assertRaises(pydantic.ValidationError):
                config_class()
            with self.assertRaises(pydantic.ValidationError):
                config_class(api_key='key', service_account=SERVICE_ACCOUNT_INFO)
            with self.assertRaises(pydantic.ValidationError):
                config_class(api_key='')
            self.assertEqual(config_class(api_key='key').api_key.get_secret_value(), 'key')

    def test_gemini_project_id_requires_service_account(self):
        with self.assertRaises(pydantic.ValidationError):
            GeminiConfig(api_key='key', project_id='project')

    def test_api_key_json_round_trip(self):
        configuration = ServicesConfiguration(google=GoogleConfig(api_key='google-key'), gemini=GeminiConfig(api_key='gemini-key'))
        data = json.loads(configuration.dump_json())
        self.assertEqual(data['google'], {'api_key': 'google-key'})
        self.assertEqual(data['gemini'], {'api_key': 'gemini-key'})
        self.assertEqual(ServicesConfiguration.model_validate(data), configuration)


def _json_response(body, status_code=200):
    response = MagicMock(status_code=status_code)
    response.json.return_value = body
    response.text = json.dumps(body)
    return response


class TestGoogleApiKey(unittest.TestCase):
    def setUp(self):
        self.service = cloudlanguagetools.google.GoogleService()
        self.service.configure(GoogleConfig(api_key='google-key'))

    def test_configure(self):
        self.assertEqual(self.service.api_key, 'google-key')
        self.assertIsNone(self.service.credentials)
        # the TTS client is built from the API key, without looking up default credentials
        self.service.get_client()

    def test_translation(self):
        with patch('cloudlanguagetools.google.requests.request', return_value=_json_response(
                {'data': {'translations': [{'translatedText': 'Hello world'}]}})) as mock_request:
            self.assertEqual(self.service.get_translation('Bonjour le monde', 'fr', 'en'), 'Hello world')
        args, kwargs = mock_request.call_args
        self.assertEqual(args, ('POST', cloudlanguagetools.google.TRANSLATION_URL))
        self.assertEqual(kwargs['json'], {'q': 'Bonjour le monde', 'source': 'fr', 'target': 'en'})
        # the key goes in a header, never in the URL
        self.assertEqual(kwargs['headers'], {'x-goog-api-key': 'google-key'})
        self.assertNotIn('params', kwargs)

    def test_translation_languages(self):
        with patch('cloudlanguagetools.google.requests.request', return_value=_json_response(
                {'data': {'languages': [{'language': 'fr'}, {'language': 'en'}]}})):
            languages = self.service.get_translation_language_list()
        self.assertEqual(sorted(language.get_language_id() for language in languages), ['en', 'fr'])

    def test_translation_errors(self):
        with patch('cloudlanguagetools.google.requests.request', return_value=_json_response(
                {'error': {'message': 'Invalid Value'}}, status_code=400)):
            with self.assertRaisesRegex(cloudlanguagetools.errors.RequestError, 'Invalid Value'):
                self.service.get_translation('text', 'xx', 'en')
        with patch('cloudlanguagetools.google.requests.request', return_value=_json_response(
                {'error': {'message': 'API key not valid'}}, status_code=403)):
            with self.assertRaises(cloudlanguagetools.errors.AuthenticationError):
                self.service.get_translation('text', 'fr', 'en')

    def test_detect_language(self):
        with patch('cloudlanguagetools.google.requests.request', return_value=_json_response(
                {'data': {'detections': [[{'language': 'fr', 'confidence': 1, 'isReliable': False}]]}})):
            self.assertEqual(self.service.detect_language('Bonjour')['language'], 'fr')


class TestGeminiApiKey(unittest.TestCase):
    def setUp(self):
        self.service = cloudlanguagetools.gemini.GeminiService()
        self.service.configure(GeminiConfig(api_key='gemini-key'))

    def post(self, model, options=None):
        audio = base64.b64encode(b'\x00\x00' * 2400).decode('utf-8')
        response = _json_response({'candidates': [{'content': {'parts': [
            {'inlineData': {'mimeType': 'audio/L16;codec=pcm;rate=24000', 'data': audio}}]}}]})
        with patch('cloudlanguagetools.gemini.requests.post', return_value=response) as mock_post:
            self.service.get_tts_audio('Hello', {'name': 'Kore'}, {'model': model, **(options or {})})
        return mock_post.call_args

    def test_configure(self):
        self.assertEqual(self.service.api_key, 'gemini-key')
        self.assertIsNone(self.service.google_credentials)

    def test_gemini_3_8_request(self):
        args, kwargs = self.post('gemini-3.8-flash-tts', {'prompt': 'cheerful', 'language_code': 'fr-FR'})
        self.assertEqual(args[0], 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent')
        self.assertEqual(kwargs['headers'], {'x-goog-api-key': 'gemini-key'})
        self.assertEqual(kwargs['json']['contents'][0]['parts'][0], {'text': 'Hello', 'speechMetadata': {'style': 'cheerful'}})
        self.assertEqual(kwargs['json']['generationConfig']['speechConfig'],
            {'voiceConfig': {'voice': 'Kore'}, 'languageCode': 'fr-FR'})

    def test_older_model_request(self):
        args, kwargs = self.post('gemini-2.5-flash-tts', {'prompt': 'Say cheerfully'})
        # Cloud TTS model name mapped to the Gemini API name
        self.assertEqual(args[0], 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent')
        # older models reject speechMetadata, the style prompt is a text prefix
        self.assertEqual(kwargs['json']['contents'][0]['parts'][0], {'text': 'Say cheerfully: Hello'})
        self.assertEqual(kwargs['json']['generationConfig']['speechConfig'],
            {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': 'Kore'}}})

    def test_unavailable_model(self):
        with patch('cloudlanguagetools.gemini.requests.post') as mock_post:
            with self.assertRaises(cloudlanguagetools.errors.InputError):
                self.service.get_tts_audio('Hello', {'name': 'Kore'}, {'model': 'gemini-2.5-flash-lite-preview-tts'})
        mock_post.assert_not_called()

    def test_voice_options_exclude_unavailable_models(self):
        voices = self.service.get_tts_voice_list_v3()
        models = voices[0].options['model']['values']
        self.assertNotIn('gemini-2.5-flash-lite-preview-tts', models)
        self.assertIn('gemini-3.8-flash-tts', models)
        self.assertEqual(set(models), set(cloudlanguagetools.gemini.GEMINI_API_MODEL_NAMES))
        # the module-level options (service account) are unchanged
        self.assertIn('gemini-2.5-flash-lite-preview-tts', cloudlanguagetools.gemini.VOICE_OPTIONS['model']['values'])

    def test_authentication_error_hint(self):
        with patch('cloudlanguagetools.gemini.requests.post', return_value=_json_response(
                {'error': {'message': 'API key not valid'}}, status_code=403)):
            with self.assertRaisesRegex(cloudlanguagetools.errors.AuthenticationError, 'Gemini API key'):
                self.service.get_tts_audio('Hello', {'name': 'Kore'}, {'model': 'gemini-3.8-flash-tts'})

    def test_gemini_independent_from_google(self):
        gemini_account = generate_service_account_info('gemini-project')
        manager = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(
            google=GoogleConfig(service_account=SERVICE_ACCOUNT_INFO),
            gemini=GeminiConfig(service_account=gemini_account)))
        google_service = manager.services[Service.Google]
        gemini_service = manager.services[Service.Gemini]
        self.assertEqual(google_service.credentials.service_account_email, SERVICE_ACCOUNT_INFO['client_email'])
        self.assertEqual(gemini_service.google_credentials.service_account_email, gemini_account['client_email'])
        self.assertEqual(gemini_service.google_project, 'gemini-project')

    def test_gemini_without_google(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(
            gemini=GeminiConfig(service_account=SERVICE_ACCOUNT_INFO, project_id='other-project')))
        self.assertEqual(manager.get_enabled_services(), [Service.Gemini])
        self.assertEqual(manager.services[Service.Gemini].google_project, 'other-project')
        self.assertTrue(len(manager.get_tts_voice_list_v3()) > 0)


class TestEncryption(unittest.TestCase):
    def setUp(self):
        self.settings = cloudlanguagetools.encryption.EncryptionSettings(key=cryptography.fernet.Fernet.generate_key().decode('utf-8'))

    def test_round_trip(self):
        configuration = ServicesConfiguration.with_keyless_services(
            azure=AzureConfig(api_key='azure-key', region='eastus'),
            google=GoogleConfig(service_account=SERVICE_ACCOUNT_INFO))
        token = cloudlanguagetools.encryption.encrypt_configuration(configuration, self.settings)
        self.assertNotIn('azure-key', token)
        decrypted = cloudlanguagetools.encryption.decrypt_configuration(token, self.settings)
        self.assertEqual(decrypted, configuration)

    def test_decrypt_legacy_format(self):
        legacy = {'DeepL': {'key': 'deepl-key'}}
        token = self.settings.get_fernet().encrypt(json.dumps(legacy).encode('utf-8')).decode('utf-8')
        configuration = cloudlanguagetools.encryption.decrypt_configuration(token, self.settings)
        self.assertEqual(configuration.deepl.api_key.get_secret_value(), 'deepl-key')

    def test_wrong_key(self):
        configuration = ServicesConfiguration(deepl=DeepLConfig(api_key='deepl-key'))
        token = cloudlanguagetools.encryption.encrypt_configuration(configuration, self.settings)
        other_settings = cloudlanguagetools.encryption.EncryptionSettings(key=cryptography.fernet.Fernet.generate_key().decode('utf-8'))
        with self.assertRaises(cryptography.fernet.InvalidToken):
            cloudlanguagetools.encryption.decrypt_configuration(token, other_settings)

    def test_invalid_key_rejected(self):
        with self.assertRaises(pydantic.ValidationError):
            cloudlanguagetools.encryption.EncryptionSettings(key='too-short')
        with self.assertRaises(pydantic.ValidationError):
            cloudlanguagetools.encryption.EncryptionSettings(key='')

    def test_key_hidden_in_repr(self):
        self.assertNotIn(self.settings.key.get_secret_value(), repr(self.settings))

    def test_from_environment(self):
        key = cryptography.fernet.Fernet.generate_key().decode('utf-8')
        settings = cloudlanguagetools.encryption.EncryptionSettings.from_environment({'CLOUDLANGUAGETOOLS_CORE_KEY': key})
        self.assertEqual(settings.key.get_secret_value(), key)
        with self.assertRaises(KeyError):
            cloudlanguagetools.encryption.EncryptionSettings.from_environment({})

    def test_encrypt_file_writes_keys_module(self):
        # encrypt() validates services_configuration.json and writes keys.py, check it without touching the real files
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = os.path.join(temp_dir, 'services_configuration.json')
            keys_path = os.path.join(temp_dir, 'keys.py')
            with open(json_path, 'w') as f:
                f.write(ServicesConfiguration(deepl=DeepLConfig(api_key='deepl-key')).dump_json())
            cloudlanguagetools.encryption.encrypt(self.settings, json_path=json_path, keys_module_path=keys_path)
            namespace = {}
            with open(keys_path) as f:
                exec(f.read(), namespace)
            configuration = cloudlanguagetools.encryption.decrypt_configuration(namespace['KEYS'], self.settings)
            self.assertEqual(configuration.deepl.api_key.get_secret_value(), 'deepl-key')
