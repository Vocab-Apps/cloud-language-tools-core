#!/bin/sh
CWD=`pwd`
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/tts_keys.sh  --decrypt tts_keys.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/convertkit.sh  --decrypt convertkit.sh.gpg
. ${CWD}/tts_keys.sh
. ${CWD}/convertkit.sh
exec gunicorn --workers 2 -b :8042 --timeout 120 --access-logfile - --error-logfile - app:app