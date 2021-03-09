FROM ubuntu:20.04

RUN apt-get update -y && apt-get install -y libasound2 python3-pip git git-crypt gnupg
RUN echo $GIT_CRYPT_KEY | base64 -d > git-crypt-key
RUN git-crypt unlock git-crypt-key

COPY start.sh requirements.txt app.py redisdb.py patreon_utils.py quotas.py secret/tts_keys.sh ./
COPY cloudlanguagetools/ /cloudlanguagetools/
RUN pip3 install -r requirements.txt
RUN pip3 install git+https://github.com/Patreon/patreon-python

EXPOSE 8042
ENTRYPOINT ["./start.sh"]
