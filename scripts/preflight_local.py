#!/usr/bin/env python3
"""Preflight local de somente leitura para a infraestrutura Docker RoboCopa.

Não cria contêineres, redes, volumes nem modifica o host. Não imprime dados
de outros projetos, nem valores de .env, nem URLs externas.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys

PROJECT = "robocopa-ifma-local"
MIN_PROJECT_FREE_GIB = 5


def run(args: list[str], *, timeout: int = 15) -> tuple[bool, str]:
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=timeout,
                                stdin=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    if result.returncode:
        return False, ""
    try:
        return True, result.stdout.decode("utf-8-sig").strip()
    except UnicodeError:
        return False, ""


def check_docker_projects(text: str, project_name: str = PROJECT) -> bool:
    """False quando a lista é desconhecida ou nome já existe (falha segura)."""
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(data, list) and all(isinstance(row, dict)
                                          for row in data) and not any(
        row.get("Name") == project_name for row in data)


def port_is_free(port: int) -> bool:
    """Teste local apenas com bind IPv4, sem publicar serviço ou conectar fora."""
    if not 1 <= port <= 65535:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def env_port(env_file: Path) -> int | None:
    """Extrai apenas a porta: não mostra nem armazena a senha no relatório."""
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    ports = [line.split("=", 1)[1].strip().strip('"').strip("'")
             for line in lines if line.startswith("ROBOCOPA_HOST_PORT=")]
    if len(ports) != 1:
        return None
    try:
        port = int(ports[0])
    except ValueError:
        return None
    return port if 1024 <= port <= 65535 else None


def check_local(root: Path) -> list[tuple[str, bool]]:
    checks: list[tuple[str, bool]] = []
    checks.append(("Arquivo .env criado localmente", (root / ".env").is_file()
                   and not (root / ".env").is_symlink()))
    docker = shutil.which("docker")
    checks.append(("Docker CLI disponível", bool(docker)))
    if not docker:
        return checks
    accessible, version = run([docker, "info", "--format", "{{.ServerVersion}}"])
    checks.append(("Docker Engine acessível", accessible and bool(version)))
    if not accessible:
        return checks
    found, projects = run([docker, "compose", "ls", "-a", "--format", "json"])
    checks.append(("Nome Compose não usado por outro projeto", found
                   and check_docker_projects(projects)))
    port = env_port(root / ".env")
    checks.append(("Porta local configurada e disponível",
                   port is not None and port_is_free(port)))
    available_gib = shutil.disk_usage(root).free / 1024**3
    checks.append(("Unidade do repositório tem ao menos 5 GiB livres",
                   available_gib >= MIN_PROJECT_FREE_GIB))
    return checks


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checks = check_local(root)
    for label, good in checks:
        print(f"{'PASS' if good else 'BLOCKED'}: {label}")
    if not checks or not all(status for _, status in checks):
        print("Preflight inconclusivo ou bloqueado; não execute o up até revisar.", file=sys.stderr)
        return 1
    print("Preflight PASS. A verificação não cobre espaço livre dentro do disco virtual Docker,")
    print("backup, internet externa, segurança do executor ou prontidão para alunos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
