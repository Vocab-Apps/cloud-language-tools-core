#!/bin/sh
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output tts_keys.sh  --decrypt tts_keys.sh.gpg
source tts_keys.sh
exec gunicorn -b :8042 --timeout 120 --access-logfile - --error-logfile - app:app