FROM alpine:latest

ARG HE_URI="myhubitatdevice"
ARG HE_ACCESS_TOKEN="my-access-token"
ARG HE_ATTRIBUTES="battery,humidity,illuminence,level,switch,temperature"
ARG HE_PROM_PREFIX="hubitat_"

ENV HE_URI=$HE_URI
ENV HE_ACCESS_TOKEN=$HE_ACCESS_TOKEN
ENV HE_ATTRIBUTES=$HE_ATTRIBUTES
ENV HE_PROM_PREFIX=$HE_PROM_PREFIX

RUN apk add --no-cache python3 py3-pip

RUN mkdir -p /app/config

COPY requirements.txt /app/requirements.txt
COPY app.py /app/app.py
COPY templates /app/templates

WORKDIR /app

RUN /usr/bin/python3 -m pip install -r requirements.txt

EXPOSE 5000

CMD gunicorn -w 4 -b 0.0.0.0:5000 app:app
