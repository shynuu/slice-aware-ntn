FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /pcf
COPY --from=builder /go/src/5g-core-ntn/free5gc/bin/pcf /usr/local/bin/pcf
ENTRYPOINT ["pcf"]
CMD ["-h"]