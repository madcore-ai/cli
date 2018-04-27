FROM ubuntu:16.04

ENV CLI_BRANCH=development
ENV CLI_COMMIT=latest
ENV CORE_BRANCH=development
ENV CORE_COMMIT=latest
ENV PLUGINS_BRANCH=development
ENV PLUGINS_COMMIT=latest
ENV CLOUDFORMATION_BRANCH=development
ENV CLOUDFORMATION_COMMIT=latest
ENV CONTAINERS_BRANCH=development
ENV CONTAINERS_COMMIT=latest

ENV PATH_BASE /var/madcore
ENV PATH_DATA /opt/madcore

RUN mkdir -p $PATH_BASE
RUN mkdir -p $PATH_DATA

COPY . $PATH_BASE/

WORKDIR $PATH_BASE

RUN apt-get update
RUN apt-get install python-pip -y

RUN pip install -r requirements/requirements.txt
RUN python setup.py install
