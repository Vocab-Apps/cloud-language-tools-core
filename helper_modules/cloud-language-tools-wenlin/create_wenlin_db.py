

from genericpath import isfile
import clt_wenlin
import os

sqlite_filepath = 'wenlin.db'
if os.path.isfile(sqlite_filepath):
    os.remove(sqlite_filepath)
dict_filepath = '/home/luc/cpp/wenlin/server/cidian.u8'
clt_wenlin.create_sqlite_file(dict_filepath, sqlite_filepath)

# encrypt the db file
command_line = f"gpg --batch --yes --passphrase-file ~/.private/gpg_passphrase_file --output wenlin.db.gpg --symmetric {sqlite_filepath}"
print(command_line)
os.system(command_line)



# to decrypt:
# gpg --batch --yes --passphrase-file ~/.private/gpg_passphrase_file --output wenlin.db  --decrypt wenlin.db.gpg