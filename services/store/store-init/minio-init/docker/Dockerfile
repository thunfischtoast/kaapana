FROM minio/mc:RELEASE.2021-09-24T00-24-24Z

LABEL IMAGE="minio-init"
LABEL VERSION="0.1.3"
LABEL CI_IGNORE="False"

COPY files/minio.sh .
RUN chmod +x minio.sh
COPY files/permissions_uploads.json .
#CMD tail -f  /dev/null
ENTRYPOINT ["/bin/sh", "minio.sh"]
#ENTRYPOINT ["/bin/sh", "minio/mc"]