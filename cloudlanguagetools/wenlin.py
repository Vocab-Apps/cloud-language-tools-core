import json
import requests
import tempfile
import logging
import clt_wenlin
import sqlite3

import cloudlanguagetools.service
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import cloudlanguagetools.errors
import cloudlanguagetools.dictionarylookup

class WenlinDictionaryLookup(cloudlanguagetools.dictionarylookup.DictionaryLookup):
    def __init__(self, source_language, lookup_type):
        self.service = cloudlanguagetools.constants.Service.Wenlin
        self.target_language = cloudlanguagetools.languages.Language.en
        self.language = source_language
        self.lookup_type = lookup_type

    def get_lookup_key(self):
        return {
            'lookup_type': self.lookup_type.name
        }        

    def get_lookup_name(self):
        return f'Wenlin ({self.language.lang_name} to {self.target_language.lang_name}), {self.lookup_type.name}'

    def get_lookup_shortname(self):
        return f'Wenlin, {self.lookup_type.name}'


class WenlinService(cloudlanguagetools.service.Service):
    def __init__(self):
        pass

    def configure(self, config):
        pass
    
    def get_tts_voice_list(self):
        return []

    def get_translation_language_list(self):
        return []

    def get_tts_voice_list(self):
        return []

    def get_tts_audio(self, text, voice_key, options):
        raise Exception('not supported')

    def get_transliteration_language_list(self):
        return []

    def get_translation(self, text, from_language_key, to_language_key):
        raise Exception('not supported')

    def get_dictionary_lookup_list(self):
        return [
            WenlinDictionaryLookup(cloudlanguagetools.languages.Language.zh_cn, 
                                   cloudlanguagetools.constants.DictionaryLookupType.Definitions)
        ]

    def get_connection(self):
        db_filepath = clt_wenlin.get_wenlin_db_path()
        connection = sqlite3.connect(db_filepath)
        return connection

    def get_dictionary_lookup(self, text, lookup_key):
        result = []
        connection = self.get_connection()
        query = f"""SELECT entry FROM words WHERE simplified='{text}'"""
        cur = connection.cursor()
        for row in cur.execute(query):
            entry_json_str = row[0]
            entry_json = json.loads(entry_json_str)
            for part_of_speech in entry_json['parts_of_speech']:
                for definition in part_of_speech['definitions']:
                    result.append(definition['definition'])
        connection.close()

        return result
