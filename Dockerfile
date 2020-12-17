FROM ubuntu:20.04

RUN apt-get update -y && apt-get install -y libasound2-dev

COPY requirements.txt app.py cloudlanguagetools ./
RUN pip install -r requirements.txt

EXPOSE 8042
ENTRYPOINT ["exec gunicorn -b :8042 --timeout 120 --access-logfile - --error-logfile - app:app"]
