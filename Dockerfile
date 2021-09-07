FROM ubuntu:20.04

# install packages first
RUN apt-get update -y && apt-get install -y libasound2 python3-pip git gnupg build-essential wget
# required by Epitran module
RUN wget http://tts.speech.cs.cmu.edu/awb/flite-2.0.5-current.tar.bz2 && tar xvjf flite-2.0.5-current.tar.bz2 && cd flite-2.0.5-current && ./configure && make && make install && cd testsuite && make lex_lookup && cp lex_lookup /usr/local/bin
COPY requirements_frozen.txt ./
RUN pip3 install -r requirements_frozen.txt
RUN pip3 install git+https://github.com/Patreon/patreon-python
# spacy trained datasets
RUN python3 -m spacy download zh_core_web_trf
RUN python3 -m spacy download en_core_web_trf
RUN python3 -m spacy download fr_dep_news_trf

COPY start.sh app.py redisdb.py patreon_utils.py quotas.py convertkit.py airtable_utils.py getcheddar_utils.py user_utils.py scheduled_tasks.py ./
COPY secrets.py.gpg secrets/tts_keys.sh.gpg secrets/convertkit.sh.gpg secrets/airtable.sh.gpg secrets/digitalocean_spaces.sh.gpg secrets/patreon_prod_digitalocean.sh.gpg secrets/rsync_net.sh.gpg secrets/ssh_id_rsync_redis_backup.gpg ./
COPY cloudlanguagetools/ /cloudlanguagetools/


EXPOSE 8042
ENTRYPOINT ["./start.sh"]
