FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /pcf
COPY --from=builder /go/src/free5gc/bin/pcf /usr/local/bin/pcf
ENTRYPOINT ["pcf"]
CMD ["-h"]