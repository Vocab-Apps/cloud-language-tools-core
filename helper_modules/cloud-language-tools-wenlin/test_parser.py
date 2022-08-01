import unittest
import clt_wenlin
import pprint


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


    def test_parse_sections_1(self):
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

        self.assertEqual(entry.entry_id, 1000000063)
        self.assertEqual(len(entry.parts_of_speech), 1)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 5)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'used as phrase suffix')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 'in enumeration')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].example_pinyin, 'Qián ∼, shū ∼, biǎo ∼, wǒ dōu diū le.')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].example_chinese, '钱∼, 书∼, 表∼, 我都丢了。')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].example_translation, 'Money, books, watch, I lost everything.')

        expected_dict = {'parts_of_speech': [
                                    {'definitions': [
                                                {'definition': 'used as phrase suffix'},
                                                {'definition': 'in enumeration',
                                                'example_chinese': '钱∼, 书∼, 表∼, 我都丢了。',
                                                'example_pinyin': 'Qián ∼, shū ∼, biǎo '
                                                                    '∼, wǒ dōu diū le.',
                                                'example_translation': 'Money, books, '
                                                                        'watch, I lost '
                                                                        'everything.'},
                                                {'definition': 'in direct address and '
                                                                'exclamation',
                                                'example_chinese': '老王∼, 这可不行∼!',
                                                'example_pinyin': 'Lǎo Wáng ∼, zhè kě '
                                                                    'bùxíng ∼!',
                                                'example_translation': 'Wang, this '
                                                                        "won't do!"},
                                                {'definition': 'indicating '
                                                                'obviousness/impatience',
                                                'example_chinese': '来∼!',
                                                'example_pinyin': 'Lái ∼!',
                                                'example_translation': 'Come on!'},
                                                {'definition': 'for confirmation',
                                                'example_chinese': '你不来∼?',
                                                'example_pinyin': 'Nǐ bù lái ∼?',
                                                'example_translation': "So you're not "
                                                                        'coming?'}],
                                            'part_of_speech': 'm.p.'}
                                        ],
        'simplified': '啊',
        'traditional': '啊'}

        # pprint.pprint(entry.to_dict())
        self.assertEqual(entry.to_dict(), expected_dict)


    def test_parse_sections_2(self):
        pass
        input = """.py   āizhe
char   挨着[-著]
ser   1000039833
gr   *
ref   61
1ps   v.
1df   be next to; get close to
2ps   adv.
2df@   one by one
2ex   yī gè ∼ yī gè guòqu
2hz   一个∼一个过去
2tr   pass one by one
--meta--
timestamp 2015-06-25T14:46:25Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertEqual(entry.simplified, '挨着')
        self.assertEqual(entry.traditional, '挨著')
        self.assertEqual(len(entry.parts_of_speech), 2)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 1)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'be next to; get close to')
        self.assertEqual(entry.parts_of_speech[1].definitions[0].definition, 'one by one')
        self.assertEqual(entry.parts_of_speech[1].definitions[0].example_pinyin, 'yī gè ∼ yī gè guòqu')
        self.assertEqual(entry.parts_of_speech[1].definitions[0].example_chinese, '一个∼一个过去')
        self.assertEqual(entry.parts_of_speech[1].definitions[0].example_translation, 'pass one by one')

    def test_parse_sections_3(self):
        pass
        input = """.py   ¹ànlǐ*
char   按理
ser   1000069612
gr   E
ref   260
ps   adv.
1df@fd7a5   [en] according to reason; in ordinary course of events; normally; theoretically; in principle
1df@fd7a5   [fr] raisonnablement ; dans le cours normal des événements ; normalement ; théoriquement ; en principe
1ex@JDF   ∼, xiàtiān shì zuì rè de jìjié.
1hz   ∼, 夏天是最热的季节。
1tr   [en] Normally, summer is the hottest season.
1tr   [fr] Normalement, l'été est la saison la plus chaude.
2df@vj   [en] by rights
2df@vj   [fr] par droit
freq   5 [gr:E]
--meta--
timestamp 2015-12-21T15:44:55Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertEqual(entry.simplified, '按理')
        self.assertEqual(entry.traditional, '按理')
        self.assertEqual(len(entry.parts_of_speech), 1)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 2)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'according to reason; in ordinary course of events; normally; theoretically; in principle')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 'by rights')

    
    def test_parse_sections_4(self):
        pass
        input = """.py   ¹báiyú
char   白鱼[-魚]
ser   1000223260
gr   *
ref   vfe924c5
ps   n.
1df   whitefish
1mw   tiáo [条]
2df   insect which eats clothing/paper
2mw   ²zhī [只]
--meta--
timestamp 2015-06-25T14:46:25Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertEqual(entry.simplified, '白鱼')
        self.assertEqual(entry.traditional, '白魚')
        self.assertEqual(len(entry.parts_of_speech), 1)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 2)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'whitefish')
        self.assertEqual(entry.parts_of_speech[0].definitions[0].measure_word, 'tiáo [条]')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 'insect which eats clothing/paper')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].measure_word, '²zhī [只]')

    def test_parse_sections_5(self):
        pass
        input = """.py   zhūniǎo
char   朱鸟[-鳥]
ser   1018027804
gr   *
ref   vwei1341a8
ps   n.
see   zhūquè [1018068544]
mw   ²zhī [只]
--meta--
timestamp 2015-06-25T14:46:25Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertEqual(entry.simplified, '朱鸟')
        self.assertEqual(entry.traditional, '朱鳥')
        self.assertEqual(len(entry.parts_of_speech), 1)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 0)


    def test_parse_sections_6(self):
        pass
        input = """.py   ²bǎzi
char   把子
ser   1000439085
gr   E
ref   561
1ps@   n.
11df   [en] bundle
11df   [fr] paquet
12df   [en] theatrical weapon
12df   [fr] arme factice
13df   [en] movement involving theatrical weapons
13df   [fr] mouvement implicant une arme factice
14df   [en] gang brother
14df   [fr] frères jurés (dans un gang)
2ps   m.
rem@TB2001.08   Added 2ps per Hawaii.
2psx@   [en] for certain abstract ideas
2psx@   [fr] pour certaines idées abstraites
2ex   jiā ∼ jìnr
2hz   加∼劲儿
2tr   [en] make an extra effort
2tr   [fr] faire un effort supplémentaire
hh   ²bàzi [1000439279]
freq   5 [gr:E]
--meta--
timestamp 2016-01-13T12:32:27Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertEqual(entry.simplified, '把子')
        self.assertEqual(entry.traditional, '把子')
        self.assertEqual(len(entry.parts_of_speech), 2)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 4)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'bundle')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 'theatrical weapon')
        self.assertEqual(entry.parts_of_speech[0].definitions[2].definition, 'movement involving theatrical weapons')
        self.assertEqual(entry.parts_of_speech[0].definitions[3].definition, 'gang brother')

    def test_parse_sections_7(self):
        pass
        input = """.py   ¹ài*
char   爱[愛]
gr   A
ser   1000004816
ref   122
1ps   v.
11df   [en] love
11df   [fr] aimer
11ex@JDF   Nǐ ∼ tā ma?
11hz   你∼她吗?
11tr   [en] Do you love her?
11tr   [fr] Tu l'aimes ?
12df   [en] like; be fond of; be keen on
12df   [fr] aimer ; être fan de ; apprécier
12ex@JDF   Tā ∼ shuōhuà.
12hz   他∼说话。
12tr   [en] He likes to talk.
12tr   [fr] Il aime parler.
12ex@JDF   Wǒ bù ∼ chī zhūròu.
12hz   我不∼吃猪肉。
12tr   [en] I don't like to eat pork.
12tr   [fr] Je n'aime pas le porc.
13df   [en] cherish
13df   [fr] chérir
14df   [en] be apt to
14df   [fr] avoir tendance à
2ps   n.
2df   [en] love
2df   [fr] amour
2mw   zhǒng/²chǎng [种/场]
3ps   cons.
31cons   ∼ V bù V
rem@TB2004.10   Changed "v.1" to "V": more consistent with 32cons below, and there is only one verb (no v.2)
rem@TB2009年03月25日   More changes to cons bands throughout; always use uppercase letters, no periods.
31df   [en] V or not as you please
31df   [fr] V ou V+nég comme il te plaît
31ex   Nǐ ∼ lái bù lái.
rem@yjc/yy200307   Separated ∼ from lai2, and separated 'lai2 bu4 lai2'.
31hz   你∼来不来。
31tr   [en] I don't care if you come or not.
31tr   [fr] Que tu viennes ou non m'importe peu.
32cons@   ∼ A ³shèng B
32df@   [en] hold A dearer than B
32df@   [fr] Chérir A plus que B
rem@TB2001.08   Revised 32ex (Mair proof).
32ex@   ∼ rén shèng jǐ
rem@yjc/yy200307   Separated 'sheng4ji3'. In fact 'ai4ren2sheng4ji3' can be treated as a lexical item?
rem@TB2004.03.27   -- If you want to add an entry for it; but the implication of "cons." is that this is a productive grammatical construction, not limited to fixed expressions. It seems OK as it stands.
32hz   ∼人胜己
32tr   [en] love others more than oneself
32tr   [fr] aimer les autres plus que soi-même
freq   342.5 [XHPC:619]
--meta--
timestamp 2015-12-16T22:08:52Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertEqual(entry.simplified, '爱')
        self.assertEqual(entry.traditional, '愛')
        self.assertEqual(len(entry.parts_of_speech), 3)
        self.assertEqual(len(entry.parts_of_speech[0].definitions), 4)
        self.assertEqual(entry.parts_of_speech[0].definitions[0].definition, 'love')
        self.assertEqual(entry.parts_of_speech[0].definitions[1].definition, 'like; be fond of; be keen on')
        self.assertEqual(entry.parts_of_speech[0].definitions[2].definition, 'cherish')
        self.assertEqual(entry.parts_of_speech[0].definitions[3].definition, 'be apt to')

        self.assertEqual(len(entry.parts_of_speech[1].definitions), 1)
        self.assertEqual(entry.parts_of_speech[1].definitions[0].definition, 'love')
        self.assertEqual(entry.parts_of_speech[1].definitions[0].measure_word, 'zhǒng/²chǎng [种/场]')

    def test_parse_sections_8(self):
        pass
        input = """.py   E
rem@TB2004.03.22   Changed "e" to "E" in hw band; otherwise the implication is that pinyin uses lowercase where Hanzi uses uppercase, which is dubious; in fact the given pinyin example sentence below has capital E. OK? cw: OK.
rem   .hw e
char   E
ser   1019310241
gr   *
ps   ab.
ab   electronic
rem@TB2004.03.22   Ordinarily in CE "ab." means a Chinese abbreviation of a Chinese word, and the "ab" band contains pinyin. In this unique case, it's an abbreviation of an English word. Wouldn't it be more appropriate to have "ps attr." and "en loan"?
rem@yjc/cw2004.09.02   Agree with Tom.(YY and John's responses need to be confirmed.)
1ex   Gěi wǒ fā yī ge ∼-mail.
1hz   给我发一个 ∼-mail。
rem@TB2004.03.22   Inserted hyphen before "mail" (to make hz band consistent with ex and tr). Also changed tilde (∼) to "E" in tr band, can use tilde in ex and hz band, never in tr band; maybe shouldn't use tilde here at all?
rem@yjc/cw2004.09.02   YY & JDF's responses need to be confirmed.Not solved yet.
1tr   Send me an email.
2ex   ∼ shídài
rem@TB2004.03.22   Inserted space before "shi2dai4". Or should it be a hyphen?
rem@yjc2004.09.01   The space is ok.(YY's note)
2hz   ∼ 时代
2tr   electronic age
rem@yjc200312   added the whole entry. (V.H.Mair & J.D.F's note)
--meta--
timestamp 2015-06-25T14:46:25Z"""
        lines = input.split('\n')
        entries = clt_wenlin.iterate_lines(lines)

        self.assertEqual(len(entries), 0)



    def test_parse_full_file(self):
        entries = clt_wenlin.read_dictionary_file('/home/luc/cpp/wenlin/server/cidian.u8')

        self.assertGreater(len(entries), 202000)

        simplified_dict = {}
        for entry in entries:
            simplified_dict[entry.simplified] = entry


        # do some checks
        self.assertEqual(len(simplified_dict['组织者'].parts_of_speech), 1)
        self.assertEqual(len(simplified_dict['组织者'].parts_of_speech[0].definitions), 1)
        self.assertEqual(simplified_dict['组织者'].parts_of_speech[0].definitions[0].definition, 'organizer')
        self.assertEqual(simplified_dict['组织者'].parts_of_speech[0].definitions[0].measure_word, '²wèi [位]')

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
        self.assertEqual(entry.parts_of_speech[0].definitions[0].measure_word, None)
        self.assertEqual(entry.parts_of_speech[1].definitions[0].measure_word, 'zhǒng/²chǎng [种/场]')


