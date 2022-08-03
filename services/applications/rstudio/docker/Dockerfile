FROM ubuntu:20.04

LABEL IMAGE="rstudio"
LABEL VERSION="2022.07.1-554"
LABEL CI_IGNORE="False"

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
    wget \
    r-base \
    dpkg-sig \
    psmisc \
    libpq5 \
    libclang-dev \
    lsb-release \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://download2.rstudio.org/server/bionic/amd64/rstudio-server-2022.07.1-554-amd64.deb -O rstudio-server.deb \
    && gpg --keyserver keyserver.ubuntu.com --recv-keys 3F32EE77E331692F \
    && dpkg-sig --verify rstudio-server.deb \
    && dpkg -i rstudio-server.deb \
    && rm rstudio-server.deb \
    && rstudio-server stop \
    && rstudio-server verify-installation

ENV USER=rstudio
COPY files/rserver.conf /etc/rstudio/rserver.conf
COPY files/logging.conf /etc/rstudio/logging.conf
COPY files/entrypoint.sh /entrypoint.sh

ENV USER admin
ENV PASSWORD admin
ENV export LANGUAGE=en_US.UTF-8

ENTRYPOINT ["/entrypoint.sh"]
