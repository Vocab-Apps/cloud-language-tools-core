import re


class Definition():
    def __init__(self, definition):
        self.definition = definition
        self.example_pinyin = None
        self.example_chinese = None
        self.example_translation = None

class PartOfSpeech():
    def __init__(self, entry, part_of_speech):
        self.entry = entry
        self.part_of_speech = part_of_speech
        self.measure_word = None
        self.definitions = []        

    def add_measure_word(self, measure_word):
        if self.measure_word != None:
            raise Exception('already set')
        self.measure_word = measure_word

    def add_definition(self, definition):
        self.definitions.append(Definition(definition))

    def add_example_pinyin(self, example_pinyin):
        self.definitions[-1].example_pinyin = example_pinyin

    def add_example_chinese(self, example_chinese):
        self.definitions[-1].example_chinese = example_chinese

    def add_example_translation(self, example_translation):
        self.definitions[-1].example_translation = example_translation

class DictionaryEntry():
    def __init__(self):
        self.pinyin = None
        self.simplified = None
        self.traditional = None
        self.measure_word = None
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
        try:
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

            m = re.match('[0-9]*ps.{0,1}\s+(.+)$', line)
            if m != None:
                current_entry.add_part_of_speech(m.groups()[0])

            m = re.match('[0-9]*df\s+(.+)$', line)
            if m != None:
                definition = process_definition(m.groups()[0])
                if definition != None:
                    current_entry.add_definition(definition)

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
                current_entry.add_example_translation(m.groups()[0])

            

            lines_read += 1
            if lines_read % 10000 == 0:
                print(f'read {lines_read} lines')
        except Exception as e:
            print(line)
            print(e)
            # raise e
    f.close()

    return entries