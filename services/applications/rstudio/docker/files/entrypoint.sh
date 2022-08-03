#!/bin/bash

# rstudio-server start
# nginx
# nginx -g 'daemon off;'


echo "INIT USER: $USER"
useradd $USER 
echo "$USER:$PASSWORD" | chpasswd
mkdir -p /home/$USER && chown -R $USER /home/$USER

echo "Starting RStudio-Server..."
/usr/lib/rstudio-server/bin/rserver --server-daemonize 0
