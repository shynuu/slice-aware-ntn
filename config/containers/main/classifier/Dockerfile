FROM golang:1.14 AS builder

WORKDIR /
RUN git clone https://github.com/shynuu/slice-classifier.git
WORKDIR /slice-classifier
RUN go build -o classifier classifier-runtime.go


FROM ubuntu:20.04
RUN apt-get update && DEBIAN_FRONTEND=non-interactive apt-get install -qy --no-install-recommends --no-install-suggests \
    iproute2 iptables procps tcpdump iputils-ping \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /slice-classifier/classifier /usr/local/sbin/classifier-runtime
WORKDIR /classifier