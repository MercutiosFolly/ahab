FROM python:3.7

MAINTAINER James Hind (jhind): jhind@mirantis.com

WORKDIR /usr/src/app

COPY ./app ./

RUN pip install -r requirements.txt

ENTRYPOINT [ "python3", "./msr-unknown-blob.py" ]

