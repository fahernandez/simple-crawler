FROM alpine:3.9

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

RUN apk add --no-cache --update ca-certificates gcc musl-dev libxml2-dev libxslt-dev python3-dev && rm -rf /var/cache/apk/*

COPY ./requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt

COPY ./ /
ENTRYPOINT ["python", "/crawler.py"]