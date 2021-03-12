FROM ubuntu:20.04

RUN apt-get update -y && apt-get install -y libasound2 python3-pip git gnupg

COPY start.sh requirements.txt app.py redisdb.py patreon_utils.py quotas.py convertkit.py tts_keys.sh.gpg convertkit.sh.gpg ./
COPY cloudlanguagetools/ /cloudlanguagetools/
RUN pip3 install -r requirements.txt
RUN pip3 install git+https://github.com/Patreon/patreon-python

EXPOSE 8042
ENTRYPOINT ["./start.sh"]
