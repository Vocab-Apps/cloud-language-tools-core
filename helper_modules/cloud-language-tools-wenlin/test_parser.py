import unittest
import clt_wenlin


class TestWenlinParser(unittest.TestCase):
    def test_process_characters(self):
        input = '阿拉伯半岛[----島]'
        simplified, traditional = clt_wenlin.process_characters(input)
        self.assertEqual(simplified, '阿拉伯半岛')
        self.assertEqual(traditional, '阿拉伯半島')

        input = '按例'
        simplified, traditional = clt_wenlin.process_characters(input)
        self.assertEqual(simplified, '按例')
        self.assertEqual(traditional, '按例')

        input = '按铃儿[-鈴兒]'
        simplified, traditional = clt_wenlin.process_characters(input)
        self.assertEqual(simplified, '按铃儿')
        self.assertEqual(traditional, '按鈴兒')  


    def test_process_definition(self):
        self.assertEqual(clt_wenlin.process_definition('[en] respectful address for an elderly man'), 'respectful address for an elderly man')
        self.assertEqual(clt_wenlin.process_definition("[fr] façon respectueuse de s'adresser à un homme plus âgé que soi"), None)

    
    def test_parse_full_file(self):
        entries = clt_wenlin.read_dictionary_file('/home/luc/cpp/wenlin/server/cidian.u8')
        simplified_dict = {}
        for entry in entries:
            simplified_dict[entry.simplified] = entry


        # do some checks
        self.assertEqual(len(simplified_dict['组织者'].parts_of_speech), 1)
        self.assertEqual(len(simplified_dict['组织者'].parts_of_speech[0].definitions), 1)
        self.assertEqual(simplified_dict['组织者'].parts_of_speech[0].definitions[0].definition, 'organizer')
        self.assertEqual(simplified_dict['组织者'].parts_of_speech[0].measure_word, '²wèi [位]')

        entry = simplified_dict['坐地铁']
        self.assertEqual(entry.simplified, '坐地铁')
        self.assertEqual(entry.traditional, '坐地鐵')
        self.assertEqual(entry.parts_of_speech[0].part_of_speech, 'v.o.')
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'ride in a subway train')
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 1)

        entry = simplified_dict['坐定']
        self.assertEqual(entry.simplified, '坐定')
        self.assertEqual(entry.traditional, '坐定')
        self.assertEqual(len(entry.parts_of_speech), 1)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 2)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'be seated')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 'be destined/doomed')
        self.assertEqual(entry.parts_of_speech[0].part_of_speech, 'r.v.')

        entry = simplified_dict['来']
        self.assertEqual(entry.pinyin, '¹lái*')
        self.assertEqual(len(entry.parts_of_speech), 6)
        # self.assertEqual(len(entry.definitions), 18)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 
            'come; arrive')
        self.assertEqual(entry.parts_of_speech[0].definitions[0].example_chinese, '到这边(儿)∼。')
        self.assertEqual(entry.parts_of_speech[0].definitions[0].example_translation, 'Come over here.')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 
             'crop up; take place')             


        entry = simplified_dict['爱']
        self.assertEqual(len(entry.parts_of_speech), 3)
        self.assertEqual(entry.parts_of_speech[0].measure_word, None)
        self.assertEqual(entry.parts_of_speech[1].measure_word, 'zhǒng/²chǎng [种/场]')
        self.assertEqual(entry.parts_of_speech[2].measure_word, None)


