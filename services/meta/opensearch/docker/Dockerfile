FROM opensearchproject/opensearch:latest

LABEL IMAGE="opensearch"
LABEL VERSION="1.2.3"
LABEL CI_IGNORE="False"

RUN whoami
RUN mkdir /usr/share/opensearch/config/certs
ADD files/* /usr/share/opensearch/config/certs
USER root
RUN chown -R 1000:1000 /usr/share/opensearch/config/certs
RUN chmod 0600 /usr/share/opensearch/config/certs/*
USER opensearch
