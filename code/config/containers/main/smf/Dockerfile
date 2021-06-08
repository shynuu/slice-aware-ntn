FROM shynuu/sa-ntn:base AS builder
FROM debian:buster-slim
WORKDIR /smf
COPY --from=builder /go/src/5g-core-ntn/bin/smf /usr/local/bin/smf
ENTRYPOINT ["smf"]
CMD ["-h"]