FROM eclipse-temurin:21-jdk-jammy@sha256:e0c60c487345d1dc9d0fc7b6f0496f3cc941e5132e09296cc17a6decc71b902b AS jdk
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS build
WORKDIR /build
COPY spikes/tank-royale/prepare.py spikes/tank-royale/upstream.lock.json ./
RUN python prepare.py /dist
COPY spikes/isolamento/arena/prepare_arena.py ./
RUN python prepare_arena.py

FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS runtime
COPY --from=jdk /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk PATH=/opt/java/openjdk/bin:$PATH HOME=/tmp PYTHONDONTWRITEBYTECODE=1
ENV JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true -XX:ActiveProcessorCount=1 -Xmx256m -XX:+ExitOnOutOfMemoryError"
WORKDIR /app
COPY spikes/isolamento/arena/requirements.txt ./
RUN python -m pip install --disable-pip-version-check --no-cache-dir --no-deps --require-hashes -r requirements.txt
COPY services/worker_agent/arena_protocol.py ./
COPY spikes/isolamento/arena/gateway.py spikes/isolamento/arena/role.py ./
COPY --from=build /dist/build-manifest.json ./
# Idle, trusted process only. No payload runs until supervisor verifies ACLs.
USER 10001:10001
ENTRYPOINT ["python", "-u", "-c", "import time; time.sleep(600)"]

FROM runtime AS referee
COPY --from=build /dist/referee/ /opt/engine/

FROM runtime AS walls
USER 0
COPY --from=build /dist/bots/Walls/ /opt/bot/
RUN cd /opt/bot && javac -cp 'lib/*' Walls.java
USER 10001:10001

FROM runtime AS spin
USER 0
COPY --from=build /dist/bots/SpinBot/ /opt/bot/
RUN cd /opt/bot && javac -cp 'lib/*' SpinBot.java
USER 10001:10001
