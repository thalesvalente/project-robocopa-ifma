# Pinned dependency already used by reference spikes; patch review remains a gate.
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
WORKDIR /opt/probe
COPY --chown=10001:10001 probe.py /opt/probe/probe.py
RUN chown 10001:10001 /opt/probe
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ROBOCOPA_CONTAINED_PROBE=1
ENTRYPOINT ["python", "/opt/probe/probe.py"]
