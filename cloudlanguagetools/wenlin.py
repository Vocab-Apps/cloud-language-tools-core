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
            'language': self.language.name,
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
        result = []
        for language in [
            cloudlanguagetools.languages.Language.zh_cn,
            cloudlanguagetools.languages.Language.zh_tw,
            cloudlanguagetools.languages.Language.yue
        ]:
            result.extend([
                WenlinDictionaryLookup(language, cloudlanguagetools.constants.DictionaryLookupType.Definitions),
                WenlinDictionaryLookup(language, cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeech),
                WenlinDictionaryLookup(language, cloudlanguagetools.constants.DictionaryLookupType.MeasureWord),
                WenlinDictionaryLookup(language, cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeechDefinitions),
            ])

        return result

    def get_connection(self):
        db_filepath = clt_wenlin.get_wenlin_db_path()
        connection = sqlite3.connect(db_filepath)
        return connection

    def iterate_dictionary_results(self, text, lookup_key):
        connection = self.get_connection()

        language = cloudlanguagetools.languages.Language[lookup_key['language']]
        column_map = {
            cloudlanguagetools.languages.Language.zh_cn: 'simplified',
            cloudlanguagetools.languages.Language.zh_tw: 'traditional',
            cloudlanguagetools.languages.Language.yue: 'traditional',
        }
        column = column_map[language]

        query = f"""SELECT entry FROM words WHERE {column}='{text}'"""
        cur = connection.cursor()
        for row in cur.execute(query):
            entry_json_str = row[0]
            entry_json = json.loads(entry_json_str)
            yield entry_json

        connection.close()

    def collect_definitions(self, generator):
        result = []
        for entry in generator:
            # definitions
            for part_of_speech in entry['parts_of_speech']:
                for definition in part_of_speech['definitions']:
                    result.append(definition['definition'])        
        return result

    def collect_partofspeech(self, generator):
        result = []
        for entry in generator:
            for part_of_speech in entry['parts_of_speech']:
                result.append(part_of_speech['part_of_speech'])

        result = list(set(result))
        result.sort()                
        return result

    def collect_measureword(self, generator):
        result = []
        for entry in generator:
            for part_of_speech in entry['parts_of_speech']:
                for definition in part_of_speech['definitions']:
                    if 'measure_word' in definition:
                        result.append(definition['measure_word'])
        result = list(set(result))
        result.sort()                
        return result                      

    def collect_partofspeech_definitions(self, generator):
        result = {}
        for entry in generator:
            for part_of_speech in entry['parts_of_speech']:
                if part_of_speech['part_of_speech'] not in result:
                    result[part_of_speech['part_of_speech']] = []
                for definition in part_of_speech['definitions']:
                    result[part_of_speech['part_of_speech']].append(definition['definition'])
        return result

    def collect_result_check_empty(self, generator, collect_result_fn, text):
        result = collect_result_fn(generator)

        not_found_error_msg = f'Wenlin: no results found for {text}'

        if type(result) is list:
            if len(result) == 0:
                raise cloudlanguagetools.errors.NotFoundError(not_found_error_msg)
        if type(result) is dict:
            if len(result.keys()) == 0:
                raise cloudlanguagetools.errors.NotFoundError(not_found_error_msg)

        return result

    def get_dictionary_lookup(self, text, lookup_key):
        lookup_type = cloudlanguagetools.constants.DictionaryLookupType[lookup_key['lookup_type']]
        lookup_type_fn_map = {
            cloudlanguagetools.constants.DictionaryLookupType.Definitions: self.collect_definitions,
            cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeech: self.collect_partofspeech,
            cloudlanguagetools.constants.DictionaryLookupType.MeasureWord: self.collect_measureword,
            cloudlanguagetools.constants.DictionaryLookupType.PartOfSpeechDefinitions: self.collect_partofspeech_definitions,
        }

        collect_result_fn = lookup_type_fn_map[lookup_type]
        generator = self.iterate_dictionary_results(text, lookup_key)

        return self.collect_result_check_empty(generator, collect_result_fn, text)