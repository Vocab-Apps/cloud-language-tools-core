import unittest
import clt_wenlin
import tempfile


class TestWenlinSqlite(unittest.TestCase):
    def test_create_sqlite_file(self):
        dictionary_filepath = '/home/luc/cpp/wenlin/server/cidian.u8'
        sqlite_tempfile = tempfile.NamedTemporaryFile(suffix='.db')

        clt_wenlin.create_sqlite_file(dictionary_filepath, sqlite_tempfile.name)


