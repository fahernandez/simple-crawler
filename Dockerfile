FROM python:3.6.8-alpine3.9

FROM alpine:3.9
RUN apk add --no-cache --update ca-certificates gcc musl-dev libxml2-dev libxslt-dev && rm -rf /var/cache/apk/*

COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY ./src /src
ENTRYPOINT ["python", "/src/crawler.py"]