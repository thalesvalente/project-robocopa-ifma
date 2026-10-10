#!/usr/bin/env python3
"""Render deterministic Markdown views from the single macro backlog."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from verify_planning import validate


def cell(value: object) -> str:
    return str(value).replace('|', '\\|').replace('\n', '<br>')


def sprint_markdown(sprint: dict) -> str:
    lines = [f"## {sprint['id']} — {sprint['title']}", '',
             f"**Objetivo:** {sprint['objective']}", '',
             f"**Critério de saída:** {sprint['gate']}", '',
             '| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |',
             '|---|---|---|---|---|---|---|']
    for t in sprint['tasks']:
        fields = [t['id'], f"**{t['title']}**. {t['description']}", t['artifact'],
                  t['acceptance'], f"{t['executor']} / {t['complexity']}",
                  ', '.join(t['dependencies']) or '—', t['status']]
        lines.append('| ' + ' | '.join(cell(x) for x in fields) + ' |')
    lines += ['', '### Evidências e pendências', '']
    for t in sprint['tasks']:
        if t.get('evidence'):
            lines.append(f"**{t['id']}:** " + '; '.join(t['evidence']))
            lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def render(root: Path) -> list[str]:
    data = json.loads((root / 'docs/planejamento/backlog.json').read_text(encoding='utf-8'))
    validate(data)
    header = [
        '# Plano mestre de execução — RoboCopa IFMA', '',
        f"**Versão operacional:** {data['plan_version']} · **Data:** {data['date']}", '',
        '> Visão gerada de backlog.json. Os caminhos são saídas planejadas, não provas de entrega.', '',
        '## Direção e limites', '',
        'MVP hospedado na máquina do responsável; participação pelo computador e celular, incluindo autoria, treino e inscrição. ChatGPT Pro é o ambiente principal; Codex e R4 são exceções justificadas. Spec Kit apoia especificações e tarefas por funcionalidade.', '',
        'As sprints são ciclos por objetivo, não equivalem a semanas ou mensagens. Testar a cada incremento. A primeira fatia vertical real é a S06. A S08 concentra regressão e operação. A S09 exige piloto e homologação reais.', '',
        'Uma abordagem de autoria, um formato de competição, dados mínimos e acesso inicial controlado. Aplicativos nativos independentes, múltiplas linguagens, competição pública aberta e IA obrigatória ficam fora do primeiro MVP.', '',
        '## Uso do planejamento', '',
        '`A_FAZER → EM_EXECUCAO → EM_REVISAO → CONCLUIDA`, com `BLOQUEADA` quando necessário. Conclusão exige evidência. Minutas paralelas não encerram dependências. Issues espelham o backlog; tarefas técnicas vivem em specs/. Detalhes: docs/processo/EXECUCAO.md.', '',
        '## Sprints e tarefas', ''
    ]
    outputs = []
    folder = root / 'docs/planejamento/sprints'
    folder.mkdir(parents=True, exist_ok=True)
    parts = []
    for sprint in data['sprints']:
        text = sprint_markdown(sprint)
        p = folder / f"{sprint['id']}.md"
        p.write_text(text, encoding='utf-8')
        outputs.append(p.relative_to(root).as_posix())
        parts.append(text)
    p = root / 'docs/planejamento/PLANO-MESTRE.md'
    p.write_text('\n'.join(header) + '\n\n'.join(parts), encoding='utf-8')
    outputs.append(p.relative_to(root).as_posix())
    return outputs


if __name__ == '__main__':
    try:
        paths = render(Path(__file__).resolve().parents[1])
        print(f'PASS: {len(paths)} visões de planejamento geradas.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
