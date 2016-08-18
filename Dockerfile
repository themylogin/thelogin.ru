FROM ubuntu:16.04

RUN apt-get update && \
    apt-get -y install python \
                       python-dev \
                       python-pip \
                       python-virtualenv \
                       libjpeg-dev \
                       libpng-dev \
                       libxml2-dev \
                       libxslt1-dev \
                       libmysqlclient-dev

RUN python -m virtualenv --python=python /virtualenv

ADD requirements.txt /requirements.txt
RUN /virtualenv/bin/pip install -r requirements.txt

ADD . /thelogin
