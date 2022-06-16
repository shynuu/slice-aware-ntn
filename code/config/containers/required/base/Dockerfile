FROM golang:1.14
RUN apt-get update && DEBIAN_FRONTEND=non-interactive apt-get install -qy --no-install-recommends --no-install-suggests \
    autoconf automake cmake gcc libtool pkg-config libmnl-dev libyaml-dev ca-certificates \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && rm -rf /var/lib/apt/lists/*

RUN git -C /go/src clone --recursive -b main -j $(nproc) https://github.com/shynuu/5g-core-ntn.git
WORKDIR /go/src/5g-core-ntn/free5gc
RUN make amf
RUN make ausf
RUN make nrf
RUN make nssf
RUN make pcf
RUN make udm
RUN make udr
RUN make upf
RUN make nssf
RUN make smf

WORKDIR /go/src/5g-core-ntn
RUN make ntnqof
RUN make qof