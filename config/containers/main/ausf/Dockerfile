FROM shynuu/sa-ntn:base as builder
FROM debian:buster-slim
WORKDIR /ausf
COPY --from=builder /go/src/free5gc/bin/ausf /usr/local/bin/ausf
ENTRYPOINT ["ausf"]
CMD ["-h"]