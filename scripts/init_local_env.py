#!/usr/bin/env python3
"""Inicializa credencial local para compose.local.yaml sem imprimir segredos.

Sem dependências externas e sem sobrescrever .env existente.
"""
from __future__ import annotations

from pathlib import Path
import secrets


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    target = project_root / ".env"
    if target.exists() or target.is_symlink():
        raise SystemExit("Já existe .env (ou link). Não será alterado; revise-o localmente.")

    token = secrets.token_urlsafe(48)
    lines = [
        "# Gerado localmente; NÃO faça commit, não compartilhe.",
        "ROBOCOPA_HOST_PORT=18080",
        f"ROBOCOPA_DB_PASSWORD={token}",
        "",
    ]
    # 'x' é exclusivo e evita sobrescrever dados de outra aplicação.
    with target.open("x", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines))
    print(".env local criado com senha aleatória. Segredo não exibido.")


if __name__ == "__main__":
    main()
