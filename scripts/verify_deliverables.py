#!/usr/bin/env python3
"""Check draft inventory and local Markdown link targets; no network or approvals."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


def verify(root: Path) -> tuple[int, int]:
    root = root.resolve()
    data = json.loads((root / 'docs/planejamento/entregas-preparatorias.json').read_text(encoding='utf-8'))
    rows = data.get('deliverables', [])
    expected = {f'S{s:02}-T{t:02}' for s in (1, 2) for t in range(1, 7)}
    if len(rows) != 12 or {row['task'] for row in rows} != expected:
        raise ValueError('Inventário deve conter as 12 tarefas S01/S02, sem duplicação.')
    backlog = json.loads((root / 'docs/planejamento/backlog.json').read_text(encoding='utf-8'))
    task_ids = {t['id'] for s in backlog['sprints'] for t in s['tasks']}
    pages = []
    for row in rows:
        if row['task'] not in task_ids or row.get('state') != 'MINUTA_PARA_REVISAO':
            raise ValueError('Tarefa ausente ou estado de preparação inválido.')
        path = (root / row['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Caminho ausente/inválido: {row['path']}")
        text = path.read_text(encoding='utf-8')
        if row['task'] not in text or len(text.split()) < 150:
            raise ValueError(f"Documento sem ID ou conteúdo mínimo: {row['path']}")
        pages.append(path)
    pages += [root / 'README.md', root / 'docs/descoberta/README.md', root / 'THIRD-PARTY-NOTICES.md']
    links = 0
    for path in pages:
        text = path.read_text(encoding='utf-8')
        for match in re.finditer(r'\]\(([^)\s]+)\)', text):
            value = match.group(1)
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root) or not target.exists():
                raise ValueError(f'Link local inválido em {path.relative_to(root)}: {value}')
            links += 1
    return len(rows), links


if __name__ == '__main__':
    try:
        count, links = verify(Path(__file__).resolve().parents[1])
        print(f'PASS: {count} minutas com IDs e conteúdo mínimo; {links} links locais resolvidos.')
        print('Escopo: integridade documental, não validação de campo ou homologação.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
