#!/bin/sh
CWD=`pwd`
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/tts_keys.sh  --decrypt tts_keys.sh.gpg
. ${CWD}/tts_keys.sh
exec gunicorn -b :8042 --timeout 120 --access-logfile - --error-logfile - app:app