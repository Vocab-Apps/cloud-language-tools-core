import re

class DictionaryEntry():
    def __init__(self):
        self.pinyin = None
        self.simplified = None
        self.traditional = None
        self.definitions = []
        self.measure_word = None
        self.part_of_speech = None

    def add_definition(self, definition):
        self.definitions.append(definition)




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

def read_dictionary_file(filepath):
    f = open(filepath, 'r')
    lines_read = 0
    current_entry = None
    entries = []
    for line in f:
        m = re.match('\.py\s+([^\s]+)', line)
        if m != None:
            pinyin = m.groups()[0]
            if current_entry != None:
                entries.append(current_entry)
            current_entry = DictionaryEntry()
            current_entry.pinyin = pinyin
        m = re.match('char\s+(.+)$', line)
        if m != None:
            simplified, traditional = process_characters(m.groups()[0])
            current_entry.simplified = simplified
            current_entry.traditional = traditional

        m = re.match('[0-9]*df\s+(.+)$', line)
        if m != None:
            definition = process_definition(m.groups()[0])
            if definition != None:
                current_entry.add_definition(definition)

        m = re.match('mw\s+(.+)$', line)
        if m != None:
            current_entry.measure_word = m.groups()[0]

        m = re.match('ps\s+(.+)$', line)
        if m != None:
            current_entry.part_of_speech = m.groups()[0]

        lines_read += 1
        if lines_read % 10000 == 0:
            print(f'read {lines_read} lines')
    f.close()

    return entries