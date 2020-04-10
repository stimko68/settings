FROM python:3.8-alpine

ENV PYTHONBUFFERED=1

COPY requirements.txt .

RUN pip3 install -U -r requirements.txt