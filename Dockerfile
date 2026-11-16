FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libstdc++6 libatomic1 tini passwd \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 beeper \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /data --shell /usr/sbin/nologin beeper
WORKDIR /app
COPY boot.py probe.py releases.json /app/
ENV BEEPER_SERVER_DATA_DIR=/data/profile PYTHONUNBUFFERED=1
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s CMD ["python", "/app/probe.py"]
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/app/boot.py"]
