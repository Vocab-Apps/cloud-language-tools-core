import unittest
import clt_wenlin
import tempfile
import sqlite3
import json


class TestWenlinSqlite(unittest.TestCase):
    def test_create_sqlite_file(self):
        dictionary_filepath = '/home/luc/cpp/wenlin/server/cidian.u8'
        sqlite_tempfile = tempfile.NamedTemporaryFile(suffix='.db')

        clt_wenlin.create_sqlite_file(dictionary_filepath, sqlite_tempfile.name)

        # try to query the file
        connection = sqlite3.connect(sqlite_tempfile.name)
        cur = connection.cursor()

        query = """SELECT entry FROM words WHERE simplified='啊'"""
        results = []
        for row in cur.execute(query):
            results.append(row[0])

        self.assertEqual(len(results), 5)
        entry_json_str = results[0]
        entry_dict = json.loads(entry_json_str)

        expected_entry_dict = {'parts_of_speech': [
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

        self.maxDiff = None
        self.assertEqual(entry_dict, expected_entry_dict)


