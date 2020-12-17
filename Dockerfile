FROM ubuntu:20.04

RUN apt-get update -y && apt-get install -y libasound2 python3-pip

COPY requirements.txt app.py cloudlanguagetools ./
RUN pip3 install -r requirements.txt

EXPOSE 8042
ENTRYPOINT ["exec gunicorn -b :8042 --timeout 120 --access-logfile - --error-logfile - app:app"]
