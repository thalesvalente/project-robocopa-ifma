FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS download
WORKDIR /build
COPY prepare.py upstream.lock.json ./
RUN python prepare.py /dist

FROM eclipse-temurin:21-jdk-jammy@sha256:e0c60c487345d1dc9d0fc7b6f0496f3cc941e5132e09296cc17a6decc71b902b
RUN groupadd -g 10001 spike && useradd --no-log-init -u 10001 -g spike -d /tmp/home spike
WORKDIR /opt/spike
COPY --from=download /dist/ ./
COPY SpikeBattle.java ./
RUN mkdir classes && javac -cp runner.jar -d classes SpikeBattle.java && rm samples.zip
USER 10001:10001
ENV HOME=/tmp/home
ENV JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=2 -Xmx256m -XX:+ExitOnOutOfMemoryError"
ENTRYPOINT ["java", "-cp", "/opt/spike/runner.jar:/opt/spike/classes", "SpikeBattle"]
