FROM debian:latest

RUN apt update && apt full-upgrade -y && \
    apt install dnsmasq dnsutils -y && \
    apt clean && apt autoclean && apt autoremove --purge -y && \
    rm -rf /var/lib/apt/lists/*

VOLUME ["/etc/dnsmasq.d"]

COPY dnsmasq.conf /etc/dnsmasq.d/default.conf

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD dig @127.0.0.1 localhost || exit 1

ENTRYPOINT ["dnsmasq", "--no-daemon", "--conf-dir=/etc/dnsmasq.d"]
