#!/usr/bin/env python3

from flask import Flask, request, send_file, jsonify
import flask_restful
import json
import functools
import os
import cloudlanguagetools.servicemanager
import cloudlanguagetools.errors
import redisdb
import patreon
import patreon.schemas

app = Flask(__name__)
api = flask_restful.Api(app)

manager = cloudlanguagetools.servicemanager.ServiceManager()
manager.configure()

redis_connection = redisdb.RedisDb()

def authenticate(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('api_key', None)
        # is this API key valid ?
        result = redis_connection.api_key_valid(api_key)
        if result['key_valid']:
            # authentication successful
            return func(*args, **kwargs)
        return {'error': result['msg']}, 401
    return wrapper


class LanguageList(flask_restful.Resource):
    def get(self):
        return manager.get_language_list()

class VoiceList(flask_restful.Resource):
    def get(self):
        return manager.get_tts_voice_list_json()

class TranslationLanguageList(flask_restful.Resource):
    def get(self):
        return manager.get_translation_language_list_json()

class TransliterationLanguageList(flask_restful.Resource):
    def get(self):
        return manager.get_transliteration_language_list_json()

class Translate(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        try:
            data = request.json
            return {'translated_text': manager.get_translation(data['text'], data['service'], data['from_language_key'], data['to_language_key'])}
        except cloudlanguagetools.errors.RequestError as err:
            return {'error': str(err)}, 400

class TranslateAll(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        try:
            data = request.json
            return manager.get_all_translations(data['text'], data['from_language'], data['to_language'])
        except cloudlanguagetools.errors.RequestError as err:
            return {'error': str(err)}, 400

class Transliterate(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        try:
            data = request.json
            return {'transliterated_text': manager.get_transliteration(data['text'], data['service'], data['transliteration_key'])}
        except cloudlanguagetools.errors.RequestError as err:
            return {'error': str(err)}, 400    

class Detect(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        data = request.json
        text_list = data['text_list']
        result = manager.detect_language(text_list)
        return {'detected_language': result.name}

class Audio(flask_restful.Resource):
    method_decorators = [authenticate]
    def post(self):
        data = request.json
        audio_temp_file = manager.get_tts_audio(data['text'], data['service'], data['voice_key'], data['options'])
        return send_file(audio_temp_file.name, mimetype='audio/mpeg')

class VerifyApiKey(flask_restful.Resource):
    def post(self):
        data = request.json
        api_key = data['api_key']
        result = redis_connection.api_key_valid(api_key)
        return result

class PatreonKey(flask_restful.Resource):
    def get(self):
        client_id = os.environ['PATREON_CLIENT_ID']
        client_secret = os.environ['PATREON_CLIENT_SECRET']
        redirect_uri = os.environ['PATREON_REDIRECT_URI']
        oauth_client = patreon.OAuth(client_id, client_secret)
        tokens = oauth_client.get_tokens(request.args.get('code'), redirect_uri)
        access_token = tokens['access_token']

        api_client = patreon.API(access_token)

        # user_response = api_client.fetch_user()
        # user = user_response.data()
        # pledges = user.relationship('pledges')
        # pledge = pledges[0] if pledges and len(pledges) > 0 else None

        # print(f'pledge: {pledge}')

        user_response = api_client.get_identity(includes=['memberships','campaign'])
        user_data = user_response.json_data
        print(f'user_data: {user_data}')
        user_id = user_data['data']['id']
        print(f'user_id: {user_id}')

        # # now, get member data
        # member_response = api_client.get_members_by_id(user_id)
        # print(type(member_response))
        # print(dir(member_response))
        # print(member_response)



        # user = user_response.data()
        # user = api_client.fetch_user()
        # print(type(user))
        # print(dir(user))
        # print(user)
        # print(user.json_data)
        return 'query done'

api.add_resource(LanguageList, '/language_list')
api.add_resource(VoiceList, '/voice_list')
api.add_resource(TranslationLanguageList, '/translation_language_list')
api.add_resource(TransliterationLanguageList, '/transliteration_language_list')
api.add_resource(Translate, '/translate')
api.add_resource(TranslateAll, '/translate_all')
api.add_resource(Transliterate, '/transliterate')
api.add_resource(Detect, '/detect')
api.add_resource(Audio, '/audio')
api.add_resource(VerifyApiKey, '/verify_api_key')
api.add_resource(PatreonKey, '/patreon_key')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')