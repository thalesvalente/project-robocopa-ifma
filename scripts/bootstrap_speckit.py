#!/usr/bin/env python3
"""Initialize pinned upstream in staging; never overwrite project documents."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

PRESERVED = Path('.specify/memory/constitution.md')
REQUIRED = (
    Path('.specify/templates/spec-template.md'),
    Path('.specify/templates/plan-template.md'),
    Path('.specify/templates/tasks-template.md'),
    Path('.agents/commands/speckit.specify.md'),
)


def load_lock(root: Path) -> dict[str, Any]:
    data = json.loads((root / 'tools/speckit.lock.json').read_text(encoding='utf-8'))
    sha = data.get('commit', '')
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('O commit do Spec Kit deve ser um SHA completo.')
    if data.get('source') != f'git+https://github.com/github/spec-kit.git@{sha}':
        raise ValueError('A origem não corresponde ao upstream oficial e ao commit fixado.')
    if data.get('integration') != 'generic' or data.get('commands_directory') != '.agents/commands':
        raise ValueError('Integração/diretório diferente do contrato revisado.')
    return data


def command(lock: dict[str, Any], staging: Path, variant: str) -> list[str]:
    if variant not in {'sh', 'ps', 'py'}:
        raise ValueError('Variante de script inválida.')
    return ['uvx', '--from', lock['source'], 'specify', 'init', str(staging),
            '--integration', 'generic',
            '--integration-options=--commands-dir .agents/commands',
            '--script', variant, '--non-interactive', '--ignore-agent-tools']


def check_destination(root: Path, relative: Path) -> None:
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError(f'Caminho inválido: {relative}')
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Destino contém link simbólico: {relative}')
    if not (root / relative).resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Destino fora do projeto: {relative}')


def inspect_generated(root: Path, staging: Path) -> list[tuple[Path, Path]]:
    for relative in REQUIRED:
        if not (staging / relative).is_file():
            raise ValueError(f'A CLI não gerou o arquivo esperado: {relative}; revisar a versão.')
    pending: list[tuple[Path, Path]] = []
    conflicts: list[str] = []
    for top in ('.specify', '.agents'):
        directory = staging / top
        if directory.is_symlink():
            raise ValueError(f'A origem contém link simbólico: {directory}')
        for source in sorted(directory.rglob('*')):
            if source.is_symlink():
                raise ValueError(f'A origem contém link simbólico: {source}')
            if not source.is_file():
                continue
            relative = source.relative_to(staging)
            check_destination(root, relative)
            destination = root / relative
            if relative == PRESERVED and destination.is_file():
                continue
            if destination.exists():
                if not destination.is_file() or destination.read_bytes() != source.read_bytes():
                    conflicts.append(str(relative))
            else:
                pending.append((source, destination))
    if conflicts:
        raise ValueError('Conflitos detectados; nenhum arquivo copiado:\n' + '\n'.join(conflicts))
    return pending


def copy_generated(root: Path, staging: Path) -> list[str]:
    pending = inspect_generated(root, staging)
    created: list[Path] = []
    try:
        for source, destination in pending:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as handle:
                created.append(destination)
                handle.write(source.read_bytes())
            shutil.copymode(source, destination)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return [p.relative_to(root).as_posix() for p in created]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--script', choices=('sh', 'ps', 'py'), default='ps' if os.name == 'nt' else 'sh')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        lock = load_lock(root)
        print(f"Spec Kit {lock['release']} — commit {lock['commit']}")
        if not args.apply:
            print('SIMULAÇÃO: nenhuma instalação, conexão ou alteração foi realizada.')
            print(subprocess.list2cmdline(command(lock, Path('<TEMP>/project'), args.script)))
            return 0
        if sys.version_info < (3, 11):
            raise ValueError('Use Python 3.11 ou superior.')
        if not shutil.which('uvx') or not shutil.which('git'):
            raise ValueError('São necessários uv/uvx e Git no PATH.')
        with tempfile.TemporaryDirectory(prefix='robocopa-speckit-') as temporary:
            staging = Path(temporary) / 'project'
            subprocess.run(command(lock, staging, args.script), cwd=temporary, check=True)
            created = copy_generated(root, staging)
            print(f'Arquivos novos copiados: {len(created)}')
            for relative in created:
                print(relative)
        print('Bootstrap concluído neste ambiente; não comprova instalação na máquina alvo ou conexão MCP.')
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'BLOQUEADO: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
