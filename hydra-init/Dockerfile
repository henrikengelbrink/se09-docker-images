FROM python:3.7.7-alpine
LABEL maintainer="henrik.engelbrink@code.berlin"

RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add bash

RUN pip install requests

COPY ./main.py main.py

CMD ["python","main.py"]