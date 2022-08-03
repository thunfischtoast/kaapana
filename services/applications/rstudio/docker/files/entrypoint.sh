#!/bin/bash

# rstudio-server start
# nginx
# nginx -g 'daemon off;'


echo "Starting user-api ..."
# uvicorn user_api:app --reload
cd /src
SCRIPT_NAME=$APPLICATION_ROOT gunicorn user_api:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000 --access-logfile - --error-logfile - --daemon

echo "Starting RStudio-Server..."
/usr/lib/rstudio-server/bin/rserver --server-daemonize 0
