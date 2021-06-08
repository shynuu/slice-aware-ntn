FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /nrf
COPY --from=builder /go/src/free5gc/bin/nrf /usr/local/bin/nrf
ENTRYPOINT ["nrf"]
CMD ["-h"]