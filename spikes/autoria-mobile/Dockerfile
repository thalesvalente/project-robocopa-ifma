# Built on the local reference image, whose upstream artifacts/base digests are pinned.
FROM robocopa-ifma/tank-spike:1.4.0
USER root
COPY MobileBattle.java /opt/spike/MobileBattle.java
RUN javac -cp /opt/spike/runner.jar -d /opt/spike/classes /opt/spike/MobileBattle.java
USER 10001:10001
ENTRYPOINT ["java", "-cp", "/opt/spike/runner.jar:/opt/spike/classes", "MobileBattle"]
