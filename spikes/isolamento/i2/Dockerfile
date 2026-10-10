# Everything downloaded during build, nothing downloaded during battles.
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS fetch
WORKDIR /build
COPY spikes/tank-royale/prepare.py /build/reference_prepare.py
COPY spikes/isolamento/i2/prepare.py spikes/isolamento/i2/upstream.lock.json /build/
RUN python prepare.py

FROM eclipse-temurin:21-jdk-jammy@sha256:e0c60c487345d1dc9d0fc7b6f0496f3cc941e5132e09296cc17a6decc71b902b AS java-base
RUN groupadd -g 10001 robocopa && useradd --no-log-init -u 10001 -g robocopa -d /tmp robocopa
ENV HOME=/tmp

FROM java-base AS referee
COPY --from=fetch /dist/server.jar /opt/arena/server.jar
USER 10001:10001
WORKDIR /opt/arena
ENTRYPOINT ["java", "-jar", "/opt/arena/server.jar"]

FROM java-base AS bot
COPY --from=fetch /dist/bots/ /opt/bots/
RUN mkdir /opt/bots/classes && javac -cp '/opt/bots/lib/*' -d /opt/bots/classes /opt/bots/Walls/Walls.java /opt/bots/SpinBot/SpinBot.java
USER 10001:10001
ENTRYPOINT ["java"]

FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS ws-base
# Version pin for disposable feasibility test. Production requires per-wheel hashes/review.
RUN python -m pip install --no-cache-dir --only-binary=:all: websockets==16.0 && \
    groupadd -g 10001 robocopa && useradd --no-log-init -u 10001 -g robocopa -d /tmp robocopa
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp
USER 10001:10001
WORKDIR /app

FROM ws-base AS gateway
COPY spikes/isolamento/i2/gateway.py /app/gateway.py
ENTRYPOINT ["python", "/app/gateway.py"]

FROM ws-base AS controller
COPY spikes/isolamento/i2/controller.py /app/controller.py
COPY spikes/isolamento/i2/probe.py /app/probe.py
ENTRYPOINT ["python", "/app/controller.py"]
