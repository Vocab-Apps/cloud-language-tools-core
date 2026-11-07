import os
import sys
import json
import base64
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import boto3
import pydantic
import cryptography.fernet

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cloudlanguagetools.configuration
import cloudlanguagetools.encryption
import cloudlanguagetools.errors
import cloudlanguagetools.servicemanager
import cloudlanguagetools.google
import cloudlanguagetools.gemini
from cloudlanguagetools.configuration import (
    ServicesConfiguration, AzureConfig, DeepLConfig, GoogleConfig, GeminiConfig,
    EpitranConfig,
)
from cloudlanguagetools.constants import Service


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
            google=GoogleConfig(api_key='google-key'),
            mandarin_cantonese=cloudlanguagetools.configuration.MandarinCantoneseConfig())
        json_str = configuration.dump_json()
        data = json.loads(json_str)
        # secrets are serialized in clear, disabled services are omitted
        self.assertEqual(data['azure'], {'api_key': 'super-secret-key', 'region': 'eastus'})
        self.assertEqual(data['mandarin_cantonese'], {})
        self.assertNotIn('deepl', data)
        self.assertEqual(data['google'], {'api_key': 'google-key'})
        self.assertEqual(ServicesConfiguration.model_validate_json(json_str), configuration)

class TestRegions(unittest.TestCase):
    def test_azure_region(self):
        config = AzureConfig(api_key='key', region='westeurope')
        self.assertIs(config.region, cloudlanguagetools.configuration.AzureRegion.westeurope)
        self.assertEqual(json.loads(ServicesConfiguration(azure=config).dump_json())['azure']['region'], 'westeurope')

    def test_azure_invalid_region_rejected(self):
        for region in ['eastus9', 'EastUS', 'us-east-1', '', 'global']:
            with self.assertRaises(pydantic.ValidationError, msg=region):
                AzureConfig(api_key='key', region=region)

    def test_amazon_region(self):
        config = cloudlanguagetools.configuration.AmazonConfig(access_key_id='id', secret_access_key='secret', region='eu-west-1')
        self.assertIs(config.region, cloudlanguagetools.configuration.AmazonRegion.eu_west_1)
        self.assertEqual(json.loads(ServicesConfiguration(amazon=config).dump_json())['amazon']['region'], 'eu-west-1')

    def test_amazon_invalid_region_rejected(self):
        for region in ['us-east-9', 'US-EAST-1', 'eastus', '']:
            with self.assertRaises(pydantic.ValidationError, msg=region):
                cloudlanguagetools.configuration.AmazonConfig(access_key_id='id', secret_access_key='secret', region=region)

    def test_amazon_regions_match_polly(self):
        # fails when botocore's endpoint data adds or removes a Polly region: update AmazonRegion
        polly_regions = set(boto3.session.Session().get_available_regions('polly'))
        self.assertEqual({region.value for region in cloudlanguagetools.configuration.AmazonRegion}, polly_regions)
        translate_regions = set(boto3.session.Session().get_available_regions('translate'))
        self.assertTrue(translate_regions <= polly_regions)

    def test_services_receive_region_string(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(
            azure=AzureConfig(api_key='key', region='japaneast'),
            amazon=cloudlanguagetools.configuration.AmazonConfig(access_key_id='id', secret_access_key='secret', region='ap-northeast-1')))
        self.assertEqual(type(manager.services[Service.Azure].region), str)
        self.assertEqual(manager.services[Service.Azure].region, 'japaneast')
        self.assertEqual(manager.services[Service.Amazon].polly_client.meta.region_name, 'ap-northeast-1')


class TestLegacyFormatRejected(unittest.TestCase):
    """The pre-versioned format (keyed by Service enum name) is not supported."""
    LEGACY = {
        'Azure': {'region': 'eastus', 'key': 'azure-key'},
        'DeepL': {'key': 'deepl-key'},
    }

    def test_legacy_format_rejected(self):
        with self.assertRaises(pydantic.ValidationError):
            ServicesConfiguration.model_validate(self.LEGACY)
        with self.assertRaises(pydantic.ValidationError):
            ServicesConfiguration.model_validate({'version': 1, **self.LEGACY})

    def test_no_legacy_converter(self):
        self.assertFalse(hasattr(cloudlanguagetools.configuration, 'from_legacy_dict'))
        self.assertFalse(hasattr(cloudlanguagetools.configuration, 'load_configuration'))


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
    def test_api_key_required(self):
        for config_class in [GoogleConfig, GeminiConfig]:
            with self.assertRaises(pydantic.ValidationError):
                config_class()
            with self.assertRaises(pydantic.ValidationError):
                config_class(api_key='')
            self.assertEqual(config_class(api_key='key').api_key.get_secret_value(), 'key')

    def test_service_account_rejected(self):
        for config_class in [GoogleConfig, GeminiConfig]:
            with self.assertRaises(pydantic.ValidationError):
                config_class(service_account={'type': 'service_account'})
            with self.assertRaises(pydantic.ValidationError):
                config_class(api_key='key', service_account={'type': 'service_account'})
        with self.assertRaises(pydantic.ValidationError):
            GeminiConfig(api_key='key', project_id='project')

    def test_separate_config_classes(self):
        # Google and Gemini are configured independently, with unrelated config classes
        self.assertFalse(issubclass(GoogleConfig, GeminiConfig))
        self.assertFalse(issubclass(GeminiConfig, GoogleConfig))
        self.assertEqual(GoogleConfig.__bases__, (cloudlanguagetools.configuration.ServiceConfig,))
        self.assertEqual(GeminiConfig.__bases__, (cloudlanguagetools.configuration.ServiceConfig,))

    def test_api_key_json_round_trip(self):
        configuration = ServicesConfiguration(google=GoogleConfig(api_key='google-key'), gemini=GeminiConfig(api_key='gemini-key'))
        data = json.loads(configuration.dump_json())
        self.assertEqual(data['google'], {'api_key': 'google-key'})
        self.assertEqual(data['gemini'], {'api_key': 'gemini-key'})
        self.assertEqual(ServicesConfiguration.model_validate(data), configuration)

    def test_gemini_independent_from_google(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(
            google=GoogleConfig(api_key='google-key'),
            gemini=GeminiConfig(api_key='gemini-key')))
        self.assertEqual(manager.services[Service.Google].api_key, 'google-key')
        self.assertEqual(manager.services[Service.Gemini].api_key, 'gemini-key')

    def test_gemini_without_google(self):
        manager = cloudlanguagetools.servicemanager.ServiceManager(ServicesConfiguration(
            gemini=GeminiConfig(api_key='gemini-key')))
        self.assertEqual(manager.get_enabled_services(), [Service.Gemini])
        self.assertTrue(len(manager.get_tts_voice_list_v3()) > 0)


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

    def test_unconfigured(self):
        service = cloudlanguagetools.google.GoogleService()
        with patch('cloudlanguagetools.google.requests.request') as mock_request:
            with self.assertRaises(cloudlanguagetools.errors.AuthenticationError):
                service.get_translation('text', 'fr', 'en')
        mock_request.assert_not_called()
        with self.assertRaises(cloudlanguagetools.errors.AuthenticationError):
            service.get_client()

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

    def test_gemini_3_8_request(self):
        args, kwargs = self.post('gemini-3.8-flash-tts', {'prompt': 'cheerful', 'language_code': 'fr-FR'})
        self.assertEqual(args[0], 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent')
        self.assertEqual(kwargs['headers'], {'x-goog-api-key': 'gemini-key'})
        self.assertEqual(kwargs['json']['contents'][0]['parts'][0], {'text': 'Hello', 'speechMetadata': {'style': 'cheerful'}})
        self.assertEqual(kwargs['json']['generationConfig']['speechConfig'],
            {'voiceConfig': {'voice': 'Kore'}, 'languageCode': 'fr-FR'})

    def test_older_model_request(self):
        args, kwargs = self.post('gemini-2.5-flash-tts', {'prompt': 'Say cheerfully'})
        # library model name mapped to the Gemini API name
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

    def test_voice_options_list_supported_models(self):
        voices = self.service.get_tts_voice_list_v3()
        models = voices[0].options['model']['values']
        self.assertNotIn('gemini-2.5-flash-lite-preview-tts', models)
        self.assertIn('gemini-3.8-flash-tts', models)
        self.assertEqual(set(models), set(cloudlanguagetools.gemini.GEMINI_API_MODEL_NAMES))

    def test_authentication_error_hint(self):
        with patch('cloudlanguagetools.gemini.requests.post', return_value=_json_response(
                {'error': {'message': 'API key not valid'}}, status_code=403)):
            with self.assertRaisesRegex(cloudlanguagetools.errors.AuthenticationError, 'Gemini API key'):
                self.service.get_tts_audio('Hello', {'name': 'Kore'}, {'model': 'gemini-3.8-flash-tts'})

class TestEncryption(unittest.TestCase):
    def setUp(self):
        self.settings = cloudlanguagetools.encryption.EncryptionSettings(key=cryptography.fernet.Fernet.generate_key().decode('utf-8'))

    def test_round_trip(self):
        configuration = ServicesConfiguration.with_keyless_services(
            azure=AzureConfig(api_key='azure-key', region='eastus'),
            google=GoogleConfig(api_key='google-key'),
            gemini=GeminiConfig(api_key='gemini-key'))
        token = cloudlanguagetools.encryption.encrypt_configuration(configuration, self.settings)
        self.assertNotIn('azure-key', token)
        decrypted = cloudlanguagetools.encryption.decrypt_configuration(token, self.settings)
        self.assertEqual(decrypted, configuration)

    def test_decrypt_legacy_format_rejected(self):
        legacy = {'DeepL': {'key': 'deepl-key'}}
        token = self.settings.get_fernet().encrypt(json.dumps(legacy).encode('utf-8')).decode('utf-8')
        with self.assertRaises(pydantic.ValidationError):
            cloudlanguagetools.encryption.decrypt_configuration(token, self.settings)

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
