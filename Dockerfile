FROM ubuntu:20.04

RUN apt-get update -y && apt-get install -y libasound2 python3-pip git gnupg
RUN gpg --batch --yes --passphrase $GPG_PASSPHRASE --output tts_keys.sh  --decrypt tts_keys.sh.gpg

COPY start.sh requirements.txt app.py redisdb.py patreon_utils.py quotas.py tts_keys.sh ./
COPY cloudlanguagetools/ /cloudlanguagetools/
RUN pip3 install -r requirements.txt
RUN pip3 install git+https://github.com/Patreon/patreon-python

EXPOSE 8042
ENTRYPOINT ["./start.sh"]
