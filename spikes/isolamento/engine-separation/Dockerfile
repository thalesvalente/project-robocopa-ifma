FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS assets
WORKDIR /input
COPY spikes/tank-royale/prepare.py spikes/tank-royale/upstream.lock.json ./
RUN python prepare.py /dist
COPY spikes/isolamento/engine-separation/prepare.py /extract.py
RUN python /extract.py /dist

FROM eclipse-temurin:21-jdk-jammy@sha256:e0c60c487345d1dc9d0fc7b6f0496f3cc941e5132e09296cc17a6decc71b902b AS compiled
WORKDIR /opt/i2
COPY --from=assets /dist/runner.jar /dist/server.jar /dist/api.jar ./
COPY --from=assets /dist/bots/ ./bots/
COPY spikes/isolamento/engine-separation/*.java ./
RUN mkdir classes && javac -cp server.jar:runner.jar:api.jar -d classes *.java \
    && javac -cp api.jar -d bots/Walls bots/Walls/Walls.java \
    && javac -cp api.jar -d bots/SpinBot bots/SpinBot/SpinBot.java \
    && java -cp classes:server.jar:runner.jar:api.jar ContractTest

FROM eclipse-temurin:21-jdk-jammy@sha256:e0c60c487345d1dc9d0fc7b6f0496f3cc941e5132e09296cc17a6decc71b902b AS runtime
WORKDIR /opt/i2
USER 10001:10001
ENV HOME=/tmp JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=2 -Xmx192m -XX:+ExitOnOutOfMemoryError"
COPY --from=compiled /opt/i2/classes/ ./classes/
ENTRYPOINT ["java", "-cp", "/opt/i2/classes:/opt/i2/api.jar:/opt/i2/server.jar:/opt/i2/runner.jar"]

FROM runtime AS judge
COPY --from=compiled /opt/i2/server.jar /opt/i2/runner.jar /opt/i2/api.jar ./
CMD ["Judge", "server"]

FROM runtime AS gateway
COPY --from=compiled /opt/i2/server.jar /opt/i2/api.jar ./
CMD ["ProtocolGate"]

FROM runtime AS bot
COPY --from=compiled /opt/i2/api.jar ./
COPY --from=compiled /opt/i2/bots/ ./bots/
CMD ["Probe", "idle"]
