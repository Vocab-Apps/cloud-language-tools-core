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


    def test_parse_sections(self):
        pass
        input = """.py   a*
char   啊
gr   A
rem@yy200307   Added gr A.
ser   1000000063
ref   1
ps   m.p.
psx   [en] used as phrase suffix
psx   [fr] utilisé comme suffixe de phrase
1psx   [en] in enumeration
1psx   [fr] dans les énumérations
1ex   Qián ∼, shū ∼, biǎo ∼, wǒ dōu diū le.
1hz   钱∼, 书∼, 表∼, 我都丢了。
1tr   [en] Money, books, watch, I lost everything.
1tr   [fr] J'ai tout perdu : de l'argent, des livres et ma montre.
2psx   [en] in direct address and exclamation
2psx   [fr] pour s'adresser directement à quelqu'un ou pour une exclamation
2ex   Lǎo Wáng ∼, zhè kě bùxíng ∼!
2hz   老王∼, 这可不行∼!
2tr   [en] Wang, this won't do!
2tr   [fr] Wang, ça ne marchera pas !
rem@2004.05.24   ?missing: {wang} cw: Ignore. Proper N.
3psx   [en] indicating obviousness/impatience
3psx   [fr] indique une évidence / une impatience
3ex   Lái ∼!
3hz   来∼!
3tr   [en] Come on!
3tr   [fr] Aller !
4psx   [en] for confirmation
4psx   [fr] pour une confirmation
4ex   Nǐ bù lái ∼?
4hz   你不来∼?
4tr   [en] So you're not coming?
4tr   [fr] Tu ne viens pas alors ?
hh   ¹ā [1000000160]
hh   á [1000000354]
hh   ǎ [1000000451]
hh   à [1000000548]
freq   609.7 [XHPC:1102]
--meta--
timestamp 2015-12-18T09:57:26Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertEqual(len(entry.parts_of_speech), 1)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 5)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'used as phrase suffix')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 'in enumeration')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].example_pinyin, 'Qián ∼, shū ∼, biǎo ∼, wǒ dōu diū le.')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].example_chinese, '钱∼, 书∼, 表∼, 我都丢了。')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].example_translation, 'Money, books, watch, I lost everything.')


    
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

        part_of_speech = entry.parts_of_speech[1]
        self.assertEqual(part_of_speech.part_of_speech, 'suf.')
        self.assertEqual(part_of_speech.definitions[0].definition, 'ability')
        self.assertEqual(part_of_speech.definitions[0].example_pinyin, 'zuòbu∼')
        self.assertEqual(part_of_speech.definitions[0].example_chinese, '作不∼')
        self.assertEqual(part_of_speech.definitions[0].example_translation, "don't know how to do it")



        entry = simplified_dict['爱']
        self.assertEqual(len(entry.parts_of_speech), 3)
        self.assertEqual(entry.parts_of_speech[0].measure_word, None)
        self.assertEqual(entry.parts_of_speech[1].measure_word, 'zhǒng/²chǎng [种/场]')
        self.assertEqual(entry.parts_of_speech[2].measure_word, None)


