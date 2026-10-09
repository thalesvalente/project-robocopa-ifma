#!/usr/bin/env python3
"""Validate planning structure, not product implementation or human acceptance."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
from typing import Any

VALID_STATES = {'A_FAZER', 'EM_EXECUCAO', 'EM_REVISAO', 'CONCLUIDA', 'BLOQUEADA'}


def validate(data: dict[str, Any]) -> tuple[int, int]:
    sprints = data.get('sprints', [])
    if len(sprints) != 10:
        raise ValueError('Esperadas 10 sprints.')
    tasks: dict[str, dict[str, Any]] = {}
    for index, sprint in enumerate(sprints):
        sid = f'S{index:02}'
        if sprint.get('id') != sid:
            raise ValueError('Ordem/ID de sprint inválido.')
        if not sprint.get('gate') or not sprint.get('objective'):
            raise ValueError(f'Sprint sem objetivo/gate: {sid}')
        if len(sprint.get('tasks', [])) != 6:
            raise ValueError(f'Esperadas seis tarefas em {sid}.')
        for task in sprint['tasks']:
            tid = task.get('id', '')
            if tid in tasks:
                raise ValueError(f'ID duplicado: {tid}')
            if not re.fullmatch(rf'{sid}-T0[1-6]', tid):
                raise ValueError(f'ID inválido: {tid}')
            for key in ('title', 'description', 'artifact', 'acceptance', 'executor', 'complexity'):
                if not task.get(key):
                    raise ValueError(f'{tid}: campo vazio {key}')
            if task.get('status') not in VALID_STATES:
                raise ValueError(f'{tid}: estado inválido')
            if task['status'] == 'CONCLUIDA' and not task.get('evidence'):
                raise ValueError(f'{tid}: conclusão sem evidência')
            tasks[tid] = task
    if len(tasks) != 60:
        raise ValueError('Esperadas 60 tarefas macro.')
    for tid, task in tasks.items():
        for dep in task.get('dependencies', []):
            if dep not in tasks:
                raise ValueError(f'{tid}: dependência inexistente {dep}')
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(tid: str) -> None:
        if tid in visiting:
            raise ValueError(f'Ciclo de dependências em {tid}')
        if tid in visited:
            return
        visiting.add(tid)
        for dep in tasks[tid].get('dependencies', []):
            visit(dep)
        visiting.remove(tid)
        visited.add(tid)
    for tid in tasks:
        visit(tid)
    return len(sprints), len(tasks)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        data = json.loads((root / 'docs/planejamento/backlog.json').read_text(encoding='utf-8'))
        ns, nt = validate(data)
        required = ('README.md', 'AGENTS.md', '.specify/memory/constitution.md',
                    'docs/planejamento/PLANO-MESTRE.md', 'docs/planejamento/ESTADO-ATUAL.md',
                    'docs/processo/SPECKIT.md', 'tools/speckit.lock.json')
        for relative in required:
            if not (root / relative).is_file():
                raise ValueError(f'Arquivo obrigatório ausente: {relative}')
        text = (root / 'docs/planejamento/PLANO-MESTRE.md').read_text(encoding='utf-8')
        for sprint in data['sprints']:
            for task in sprint['tasks']:
                if f"| {task['id']} |" not in text:
                    raise ValueError(f"Tarefa ausente da visão Markdown: {task['id']}")
        print(f'PASS: {ns} sprints, {nt} tarefas únicas, dependências válidas e sem ciclos.')
        print('PASS: campos de aceite, artefatos e arquivos obrigatórios presentes.')
        print('Escopo: planejamento; não comprova motor, piloto ou hospedagem.')
        return 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
