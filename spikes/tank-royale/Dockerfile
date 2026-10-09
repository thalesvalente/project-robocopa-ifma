FROM python:3.13-slim AS download
WORKDIR /build
COPY prepare.py upstream.lock.json ./
RUN python prepare.py /dist

FROM eclipse-temurin:21-jdk-jammy
RUN groupadd -g 10001 spike && useradd --no-log-init -u 10001 -g spike -d /tmp/home spike
WORKDIR /opt/spike
COPY --from=download /dist/ ./
COPY SpikeBattle.java ./
RUN mkdir classes && javac -cp runner.jar -d classes SpikeBattle.java && rm samples.zip
USER 10001:10001
ENV HOME=/tmp/home
ENV JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=2 -Xmx256m -XX:+ExitOnOutOfMemoryError"
ENTRYPOINT ["java", "-cp", "/opt/spike/runner.jar:/opt/spike/classes", "SpikeBattle"]
