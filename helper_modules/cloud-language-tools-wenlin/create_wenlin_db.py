

from genericpath import isfile
import clt_wenlin
import os

sqlite_filepath = 'wenlin.db'
if os.path.isfile(sqlite_filepath):
    os.remove(sqlite_filepath)
dict_filepath = '/home/luc/cpp/wenlin/server/cidian.u8'
clt_wenlin.create_sqlite_file(dict_filepath, sqlite_filepath)

