FROM golang:1.16-alpine as builder

LABEL IMAGE=minio
LABEL VERSION=2021.09.24
LABEL maintainer="MinIO Inc <dev@min.io>"

ENV GOPATH /go
ENV CGO_ENABLED 0
ENV GO111MODULE on

RUN  \
     apk add --no-cache git && \
     git clone https://github.com/minio/minio && cd minio && \
     git checkout 769f0b1e24c42d6ef1a370a5c657c9f6d5484fe7

WORKDIR /go/minio

COPY jwt.go /go/minio/internal/config/identity/openid/

RUN go install -v -ldflags "$(go run buildscripts/gen-ldflags.go)"

FROM registry.access.redhat.com/ubi8/ubi-minimal:8.4

# ARG TARGETARCH

# # ARG RELEASE
ENV RELEASE=RELEASE.2021-09-24T00-24-24Z

LABEL name="MinIO" \
      vendor="MinIO Inc <dev@min.io>" \
      maintainer="MinIO Inc <dev@min.io>" \
      version="${RELEASE}" \
      release="${RELEASE}" \
      summary="MinIO is a High Performance Object Storage, API compatible with Amazon S3 cloud storage service." \
      description="MinIO object storage is fundamentally different. Designed for performance and the S3 API, it is 100% open-source. MinIO is ideal for large, private cloud environments with stringent security requirements and delivers mission-critical availability across a diverse range of workloads."

ENV MINIO_ACCESS_KEY_FILE=access_key \
    MINIO_SECRET_KEY_FILE=secret_key \
    MINIO_ROOT_USER_FILE=access_key \
    MINIO_ROOT_PASSWORD_FILE=secret_key \
    MINIO_KMS_SECRET_KEY_FILE=kms_master_key \
    MINIO_UPDATE_MINISIGN_PUBKEY="RWTx5Zr1tiHQLwG9keckT0c45M3AGeHD6IvimQHpyRywVWGbP1aVSGav" \
    MINIO_CONFIG_ENV_FILE=config.env \
    PATH=$PATH:/opt/bin

# COPY dockerscripts/verify-minio.sh /usr/bin/verify-minio.sh
# COPY dockerscripts/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
# COPY CREDITS /licenses/CREDITS
# COPY LICENSE /licenses/LICENSE

# COPY --from=builder /go/minio/dockerscripts/verify-minio.sh /usr/bin/verify-minio.sh
COPY --from=builder /go/minio/dockerscripts/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
COPY --from=builder /go/minio/CREDITS licenses/CREDITS
COPY --from=builder /go/minio/LICENSE /licenses/LICENSE
COPY --from=builder /go/bin/minio /opt/bin/minio
RUN \
     microdnf update --nodocs && \
     microdnf install curl ca-certificates shadow-utils util-linux iproute iputils --nodocs && \
     rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm && \
     microdnf install minisign --nodocs && \
     mkdir -p /opt/bin && chmod -R 777 /opt/bin && \
     # curl -s -q https://dl.min.io/server/minio/release/linux-${TARGETARCH}/archive/minio.${RELEASE} -o /opt/bin/minio && \
     # curl -s -q https://dl.min.io/server/minio/release/linux-${TARGETARCH}/archive/minio.${RELEASE}.sha256sum -o /opt/bin/minio.sha256sum && \
     # curl -s -q https://dl.min.io/server/minio/release/linux-${TARGETARCH}/archive/minio.${RELEASE}.minisig -o /opt/bin/minio.minisig && \
     microdnf clean all && \
     chmod +x /opt/bin/minio && \
     chmod +x /usr/bin/docker-entrypoint.sh
     # chmod +x /usr/bin/verify-minio.sh && \
     # /usr/bin/verify-minio.sh

EXPOSE 9000

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

VOLUME ["/data"]

CMD ["minio"]