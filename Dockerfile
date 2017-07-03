FROM python:3-alpine

RUN apk add --no-cache bash jq zip

COPY requirements.txt /src/requirements.txt
RUN pip install --no-cache-dir -r /src/requirements.txt
