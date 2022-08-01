import re
import logging
import sqlite3
import json

logger = logging.getLogger(__name__)

class Definition():
    def __init__(self, definition):
        # logger.debug(f'creating Definition [{definition}]')
        self.definition = definition
        self.example_pinyin = None
        self.example_chinese = None
        self.example_translation = None
        self.measure_word = None

    def to_dict(self):
        result = {
            'definition': self.definition
        }
        if self.example_pinyin != None:
            result['example_pinyin'] = self.example_pinyin
        if self.example_chinese != None:
            result['example_chinese'] = self.example_chinese
        if self.example_translation != None:
            result['example_translation'] = self.example_translation
        if self.measure_word != None:
            result['measure_word'] = self.measure_word
        return result

class PartOfSpeech():
    def __init__(self, entry, part_of_speech):
        # logger.debug(f'creating PartOfSpeech [{part_of_speech}]')
        self.entry = entry
        self.part_of_speech = part_of_speech
        self.definitions = []        

    def add_measure_word(self, measure_word):
        if len(self.definitions) > 0:
            self.definitions[-1].measure_word = measure_word

    def add_definition(self, definition):
        self.definitions.append(Definition(definition))

    def add_example_pinyin(self, example_pinyin):
        self.definitions[-1].example_pinyin = example_pinyin

    def add_example_chinese(self, example_chinese):
        self.definitions[-1].example_chinese = example_chinese

    def add_example_translation(self, example_translation):
        self.definitions[-1].example_translation = example_translation

    def to_dict(self):
        return {
            'part_of_speech': self.part_of_speech,
            'definitions': [x.to_dict() for x in self.definitions]
        }

class DictionaryEntry():
    def __init__(self):
        self.pinyin = None
        self.simplified = None
        self.traditional = None
        # https://wenlin.co/wow/Project:Ci_Chinese_Parts_of_Speech_and_Other_Entry_Labels
        self.parts_of_speech = []

    def add_definition(self, definition):
        self.definitions.append(definition)

    def add_part_of_speech(self, part_of_speech):
        self.parts_of_speech.append(PartOfSpeech(self, part_of_speech))

    def add_definition(self, definition):
        if len(self.parts_of_speech) == 0:
            # raise Exception(f'unknown part of speech for {definition}')
            self.add_part_of_speech(None)
        self.parts_of_speech[-1].add_definition(definition)
        
    def add_measure_word(self, measure_word):
        self.parts_of_speech[-1].add_measure_word(measure_word)

    def add_example_pinyin(self, example_pinyin):
        self.parts_of_speech[-1].add_example_pinyin(example_pinyin)

    def add_example_chinese(self, example_chinese):
        self.parts_of_speech[-1].add_example_chinese(example_chinese)

    def add_example_translation(self, example_translation):
        self.parts_of_speech[-1].add_example_translation(example_translation)

    def to_dict(self):
        return {
            'simplified': self.simplified,
            'traditional': self.traditional,
            'parts_of_speech': [x.to_dict() for x in self.parts_of_speech]
        }

    def __str__(self):
        return f'simplified: {self.simplified}'

def process_characters(chars):
    m = re.match('([^\]]+)\[(.*)\]', chars)
    if m == None:
        return chars, chars
    simplified = m.groups()[0]
    traditional = m.groups()[1]
    final_traditional = ''
    for simplified_char, traditional_char in zip(simplified, traditional):
        if traditional_char == '-':
            final_traditional += simplified_char
        else:
            final_traditional += traditional_char
    return simplified, final_traditional

def process_definition(definition):
    if '[fr]' in definition:
        return None
    
    definition = definition.replace('[en] ', '')
    return definition

def iterate_lines(lines):
    current_entry = None
    ignore_current_entry = False
    lines_read = 0    
    entries = []    
    ignored_entries = []
    for line in lines:
        try:
            m = re.match('\.py\s+([^\s]+)', line)
            if m != None:
                pinyin = m.groups()[0]
                if current_entry != None and ignore_current_entry == False:
                    entries.append(current_entry)
                if ignore_current_entry == True:
                    ignored_entries.append(current_entry)
                ignore_current_entry = False
                current_entry = DictionaryEntry()
                current_entry.pinyin = pinyin
            m = re.match('char\s+(.+)$', line)
            if m != None:
                simplified, traditional = process_characters(m.groups()[0])
                current_entry.simplified = simplified
                current_entry.traditional = traditional

            m = re.match('[0-9]*(df[^\s]*|psx.{0,1})\s+(.+)$', line)
            if m != None:
                definition = process_definition(m.groups()[1])
                if definition != None:
                    current_entry.add_definition(definition)
                continue

            m = re.match('[0-9]*ps.{0,1}\s+(.+)$', line)
            if m != None:
                current_entry.add_part_of_speech(m.groups()[0])
                continue

            m = re.match('[0-9]*mw\s+(.+)$', line)
            if m != None:
                current_entry.add_measure_word(m.groups()[0])

            m = re.match('[0-9]*ex\s+(.+)$', line)
            if m != None:
                current_entry.add_example_pinyin(m.groups()[0])                

            m = re.match('[0-9]*hz\s+(.+)$', line)
            if m != None:
                current_entry.add_example_chinese(m.groups()[0])

            m = re.match('[0-9]*tr\s+(.+)$', line)
            if m != None:
                translation = process_definition(m.groups()[0])
                if translation != None:
                    current_entry.add_example_translation(translation)

            lines_read += 1
            if lines_read % 10000 == 0:
                logger.debug(f'read {lines_read} lines')
        except Exception as e:
            logger.exception(f'while processing {[line.strip()]}, {current_entry}')
            ignore_current_entry = True
            # raise e

    if ignore_current_entry == False:
        entries.append(current_entry)

    logger.error(f'ignored entries: {len(ignored_entries)}')

    return entries

def read_dictionary_file(filepath):
    f = open(filepath, 'r')
    entries = iterate_lines(f)
    f.close()

    return entries

def create_sqlite_file(dict_filepath, sqlite_filepath):
    entries = read_dictionary_file(dict_filepath)

    connection = sqlite3.connect(sqlite_filepath)
    cur = connection.cursor()
    cur.execute('''CREATE TABLE words (simplified text, traditional text, entry text)''')

    i = 0
    for entry in entries:
        json_string = json.dumps(entry.to_dict())
        query = f"""INSERT INTO words VALUES ('{entry.simplified}', '{entry.traditional}', '{json_string}')"""
        i += 1
        if i % 10000 == 0:
            logger.info(f'inserted {i} entries into sqlite')
        
    # add indices
    

    connection.commit()
    connection.close()
