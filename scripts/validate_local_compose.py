#!/usr/bin/env python3
"""Valida propriedades de segurança do Compose normalizado pelo Docker.

Não publica senhas ou o conteúdo completo do YAML/JSON, mesmo em erro.
Exige Docker Compose V2 instalado, mas não inicializa serviços.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def _networks(service: dict) -> set[str]:
    networks = service.get("networks", {})
    if isinstance(networks, dict):
        return set(networks)
    if isinstance(networks, list):
        return set(networks)
    return set()


def validate(config: dict) -> list[str]:
    errors: list[str] = []
    if config.get("name") != "robocopa-ifma-local":
        errors.append("O projeto Compose precisa de nome exclusivo.")
    services = config.get("services", {})
    if not isinstance(services, dict) or set(services) != {"database", "infra-probe"}:
        return errors + ["Serviços inesperados ou ausentes."]
    database, probe = services["database"], services["infra-probe"]
    if database.get("ports"):
        errors.append("O banco de dados não pode publicar portas no host.")
    if _networks(database) != {"data"}:
        errors.append("O banco precisa ficar somente na rede interna data.")
    if not bool(config.get("networks", {}).get("data", {}).get("internal")):
        errors.append("A rede data precisa ser internal:true.")
    if "edge" not in _networks(probe) or "data" in _networks(probe):
        errors.append("A sonda deve usar apenas a rede edge, sem acesso ao banco.")
    ports = probe.get("ports", [])
    if len(ports) != 1:
        errors.append("Somente uma porta local deve ser publicada.")
    else:
        entry = ports[0]
        if (not isinstance(entry, dict)
                or entry.get("host_ip") != "127.0.0.1"
                or int(entry.get("target", 0)) != 8080
                or entry.get("protocol", "tcp") != "tcp"):
            errors.append("Sonda deve estar restrita a 127.0.0.1 e porta interna 8080.")
    for name, svc in services.items():
        if svc.get("privileged"):
            errors.append(f"{name} não pode ser privilegiado.")
        if svc.get("network_mode") == "host" or svc.get("pid") == "host":
            errors.append(f"{name} não pode compartilhar rede/PID do host.")
        if not svc.get("mem_limit") or not svc.get("cpus") or not svc.get("pids_limit"):
            errors.append(f"{name} deve ter limite de memória, CPU e PIDs.")
        for volume in svc.get("volumes", []):
            if isinstance(volume, dict) and "/var/run/docker.sock" in str(volume.get("source", "")):
                errors.append("Docker socket não pode ser montado nos serviços.")
    if not probe.get("read_only"):
        errors.append("O filesystem da sonda deve ser somente leitura.")
    if "ALL" not in probe.get("cap_drop", []):
        errors.append("A sonda deve remover todas as capabilities.")
    if "POSTGRES_PASSWORD" not in database.get("environment", {}):
        errors.append("A credencial do banco deve ser definida externamente.")
    postgres_volumes = database.get("volumes", [])
    if not any(isinstance(v, dict) and v.get("type") == "volume"
               and v.get("target") == "/var/lib/postgresql/data" for v in postgres_volumes):
        errors.append("Dados do PostgreSQL precisam de volume nomeado no caminho correto.")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    command = ["docker", "compose", "-f", "compose.local.yaml", "config", "--format", "json"]
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        print("ERRO: Docker Compose indisponível ou sem resposta.", file=sys.stderr)
        return 2
    if result.returncode:
        print("ERRO: arquivo .env ausente/inválido ou Compose não configurado.", file=sys.stderr)
        return 2
    try:
        config = json.loads(result.stdout)
        errors = validate(config)
    except (ValueError, TypeError, KeyError):
        print("ERRO: saída normalizada do Docker Compose inválida.", file=sys.stderr)
        return 2
    for error in errors:
        print(f"ERRO: {error}", file=sys.stderr)
    if errors:
        return 1
    print("PASS: projeto isolado, banco privado, uma porta apenas em loopback e limites verificados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
