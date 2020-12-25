FROM ubuntu:20.04

RUN apt-get update -y && apt-get install -y libasound2 python3-pip

COPY start.sh requirements.txt app.py redisdb.py ./
COPY cloudlanguagetools/ /cloudlanguagetools/
RUN pip3 install -r requirements.txt

EXPOSE 8042
ENTRYPOINT ["./start.sh"]
