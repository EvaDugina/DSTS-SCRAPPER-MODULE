# https://devops.org.ru/dockerfile-summary#d16

FROM python:3.10.9

WORKDIR .
COPY . .
RUN pip install -r requirements.txt --no-cache-dir

CMD uvicorn server:app --port 8083 --reload