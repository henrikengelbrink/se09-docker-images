FROM python:3.7.6-alpine
LABEL maintainer="henrik.engelbrink@code.berlin"

RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add bash

COPY ./main.py main.py
COPY ./pki_policy.hcl pki_policy.hcl

CMD ["python","main.py"]