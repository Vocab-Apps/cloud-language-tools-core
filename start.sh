#!/bin/sh
CWD=`pwd`
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/tts_keys.sh  --decrypt tts_keys.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/getcheddar.sh  --decrypt getcheddar.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/convertkit.sh  --decrypt convertkit.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/airtable.sh  --decrypt airtable.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/digitalocean_spaces.sh  --decrypt digitalocean_spaces.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/patreon_prod_digitalocean.sh  --decrypt patreon_prod_digitalocean.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/rsync_net.sh  --decrypt rsync_net.sh.gpg
gpg --batch --yes --passphrase ${GPG_PASSPHRASE} --output ${CWD}/ssh_id_rsync_redis_backup  --decrypt ssh_id_rsync_redis_backup.gpg
if [ -n "$RUN_SCHEDULED_TASKS" ]
then
. ${CWD}/convertkit.sh
. ${CWD}/airtable.sh
. ${CWD}/digitalocean_spaces.sh
. ${CWD}/patreon_prod_digitalocean.sh
. ${CWD}/rsync_net.sh
python3 scheduled_tasks.py
else
. ${CWD}/tts_keys.sh
. ${CWD}/convertkit.sh
exec gunicorn --workers 3 -b :8042 --timeout 120 --access-logfile - --error-logfile - app:app
fi