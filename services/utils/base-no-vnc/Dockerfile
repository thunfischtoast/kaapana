FROM dorowu/ubuntu-desktop-lxde-vnc:focal

LABEL REGISTRY="local-only"
LABEL IMAGE="no-vnc-base"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="False"


RUN apt-get update && apt-get install -y --no-install-recommends \
    wmctrl \
    gedit \
    libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

COPY files/startup.sh /startup.sh
RUN chmod +x /startup.sh
