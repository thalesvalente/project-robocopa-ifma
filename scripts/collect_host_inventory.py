#!/usr/bin/env python3
"""Read basic host facts locally. No network, installation or privileged action."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil


def collect(root: Path) -> dict:
    disk = shutil.disk_usage(root)
    return {
        'schema_version': 1,
        'collected_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Dados técnicos básicos; requer revisão humana antes de compartilhar.',
        'os': platform.system(),
        'os_release': platform.release(),
        'architecture': platform.machine(),
        'logical_cpu_count': os.cpu_count(),
        'python': platform.python_version(),
        'project_disk_total_bytes': disk.total,
        'project_disk_free_bytes': disk.free,
        'commands_available': {name: shutil.which(name) is not None for name in ('git', 'uv', 'docker', 'wsl')},
        'not_collected': ['hostname', 'username', 'IP', 'MAC', 'credentials', 'personal_files'],
        'pending_manual_checks': ['RAM disponível', 'virtualização', 'isolamento', 'upload', 'backup', 'disponibilidade'],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    directory = root / '.local'
    if directory.is_symlink():
        raise SystemExit('Recusado: .local é um link simbólico.')
    directory.mkdir(exist_ok=True)
    target = directory / 'inventory.json'
    if target.exists() or target.is_symlink():
        raise SystemExit('O inventário já existe; revise/mova o arquivo antes de coletar novamente.')
    with target.open('x', encoding='utf-8') as handle:
        json.dump(collect(root), handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print('Inventário básico salvo em .local/inventory.json. Revise antes de compartilhar; não faça commit.')


if __name__ == '__main__':
    main()
