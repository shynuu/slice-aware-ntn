FROM shynuu/sa-ntn:cmake as cmake-builder 
FROM debian:buster-slim
WORKDIR /compile
RUN apt-get update && DEBIAN_FRONTEND=non-interactive apt-get install -qy --no-install-recommends --no-install-suggests \
    make g++ git ca-certificates libsctp-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=cmake-builder /usr/local/share/cmake-3.20 /usr/local/share/cmake-3.20
COPY --from=cmake-builder /usr/local/bin/cmake /usr/local/bin/cmake
RUN git clone -b v3.2.1 https://github.com/aligungr/UERANSIM
WORKDIR /compile/UERANSIM
RUN git checkout master
RUN make
