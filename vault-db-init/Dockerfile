FROM python:3.7.6-alpine
LABEL maintainer="henrik.engelbrink@code.berlin"

RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add postgresql-dev && \
    apk add bash

RUN pip install psycopg2

COPY ./main.py main.py
COPY ./schema.sql schema.sql

CMD ["python","main.py"]