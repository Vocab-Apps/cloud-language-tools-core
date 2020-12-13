#!/usr/bin/env python3

from flask import Flask, request
from flask_restful import Resource, Api, inputs, reqparse
import json
import cloudlanguagetools.servicemanager

app = Flask(__name__)
api = Api(app)

manager = cloudlanguagetools.servicemanager.ServiceManager()
manager.configure()    

class LanguageList(Resource):
    def get(self):
        return manager.get_language_list()

class VoiceList(Resource):
    def get(self):
        return manager.get_tts_voice_list_json()

class TranslationLanguageList(Resource):
    def get(self):
        return manager.get_translation_language_list_json()

class Translate(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('text', type=str, required=True)
        parser.add_argument('service', type=str, required=True)
        parser.add_argument('from_language_key', type=str, required=True)
        parser.add_argument('to_language_key', type=str, required=True)
        args = parser.parse_args()
        return {'translated_text': manager.get_translation(args['text'], args['service'], args['from_language_key'], args['to_language_key'])}

api.add_resource(LanguageList, '/language_list')
api.add_resource(VoiceList, '/voice_list')
api.add_resource(TranslationLanguageList, '/translation_language_list')
api.add_resource(Translate, '/translate')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')