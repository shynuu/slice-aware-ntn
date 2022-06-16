FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /nssf
COPY --from=builder /go/src/5g-core-ntn/free5gc/bin/nssf /usr/local/bin/nssf
ENTRYPOINT ["nssf"]
CMD ["-h"]