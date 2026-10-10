#!/usr/bin/env python3
"""Reconcile only S04-T04 macro progress after verified experiment evidence.

Default is a dry run; writes require GitHub-hosted CI. Never closes a task,
changes other macro tasks or grants production approval.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from render_planning import render

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    'Incremento I1 autorizado: pesquisa oficial, contrato estrito, política e subprocessos limitados implementados. 55 testes novos e nove provas sintéticas de contenção passaram em runner descartável; não é VM do responsável nem liberação de alunos.',
    'https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38021817642',
    'docs/qualidade/evidencias/S04-T04-I1.md',
    'specs/004-isolamento-execucao/iteration-1.md',
    'docs/planejamento/decisoes/D-005-vm-e-experimentos-controlados.md',
)


def reconcile(data: dict) -> dict:
    result = deepcopy(data)
    tasks = [t for sprint in result['sprints'] for t in sprint['tasks']]
    target = [t for t in tasks if t['id'] == 'S04-T04']
    if len(target) != 1:
        raise ValueError('Expected one S04-T04')
    task = target[0]
    if task['status'] not in ('A_FAZER', 'EM_EXECUCAO'):
        raise ValueError('Status changed: human reconciliation required')
    task['status'] = 'EM_EXECUCAO'
    for item in EVIDENCE:
        if item not in task['evidence']:
            task['evidence'].append(item)
    return result


def reconcile_feature_documents(root: Path) -> None:
    updates = {
      'specs/004-isolamento-execucao/spec.md': [
        ('**Feature Branch**: `docs/s04-t04-isolamento-speckit`', '**Feature Branch**: `feat/s04-isolation-validation`'),
        ('**Status**: Draft — especificação técnica preparada; sem implementação, homologação ou teste de ataques', '**Status**: requisitos em revisão; I1 implementado/testado no CI. Sem implementação pública ou homologação da VM pessoal'),
        ('É hipótese a validar, não instalação.', 'Direção aprovada em D-005; configuração efetiva da VM continua a validar, não instalada.'),
        ('- Esta feature pode ter **documentação preparada em paralelo**, mas a execução de testes de abuso só será autorizada em ambiente descartável separado depois da revisão. S04-T04 continua **A_FAZER** até evidência técnica e aceites formais.', '- Após D-005, o incremento de engenharia e as provas sintéticas em CI descartável estão autorizados. S04-T04 passa de **A_FAZER** para **EM_EXECUCAO**, sem concluir os aceites de produção. G-EXP não equivale a G-PROD; ver iteration-1.md e plan.md.'),
      ],
      'specs/004-isolamento-execucao/tasks.md': [
        ('**Status:** backlog detalhado de **implementação futura** — todas as caixas abaixo permanecem `[ ]`. A produção deste arquivo não significa que os controles já existam.', '**Status:** catálogo de 39 entregas amplas. O incremento I1 já implementa subconjuntos de contratos/política/limites, com provas reais no CI; as caixas amplas permanecem `[ ]` até atender todo seu aceite. Progresso/evidência: [iteration-1.md](iteration-1.md).'),
        ('**Macro:** S04-T04 (`A_FAZER` no backlog, porque gates prévios e testes de isolamento ainda faltam).', '**Macro:** S04-T04 em `EM_EXECUCAO` após D-005 e I1; estado histórico `A_FAZER` preservado no Git, sem fechamento dos gates S03/S04.'),
        ('**Regra de execução:** fases de engenharia/teste somente após aprovação e em ambiente descartável autorizado. No host pessoal, não executar cargas adversariais.', '**Regra de execução:** G-EXP autoriza o incremento I1 em CI descartável; G-PROD continua bloqueado. Antes de alterações/VM no host é necessário plano e autorização próprios. Não executar cargas adversariais no computador pessoal.'),
      ],
      'docs/arquitetura/ADR-004-isolamento-execucao.md': [
        ('**Status:** PROPOSTA — aguarda ratificação humana, baseline de requisitos e spikes de isolamento.', '**Status:** direção de VM dedicada aprovada pelo responsável (D-005). Instalação, rede, árbitro e homologação permanecem pendentes; I1 testa controles em CI, não Hyper-V do host.'),
        ('- Ratificação da RoboDSL T1 e da rejeição de linguagens T2 no MVP.', '- D1 resolvida: RoboDSL básica no MVP, linguagens gerais pós-MVP. Detalhamento funcional/pedagógico e liberação de alunos ainda pendentes.'),
      ],
    }
    for filename, changes in updates.items():
        file = root / filename
        text = file.read_text(encoding='utf-8')
        for old, new in changes:
            if old in text:
                text = text.replace(old, new, 1)
            elif new not in text:
                raise ValueError('Documentation changed: review ' + filename)
        file.write_text(text, encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    file = ROOT / 'docs/planejamento/backlog.json'
    current = json.loads(file.read_text(encoding='utf-8'))
    updated = reconcile(current)
    if not args.apply:
        print('DRY RUN: only S04-T04 would become EM_EXECUCAO, no task closed')
        return 0
    if (os.getenv('GITHUB_ACTIONS') != 'true' or os.getenv('RUNNER_ENVIRONMENT') != 'github-hosted'
        or os.getenv('GITHUB_REPOSITORY') != 'thalesvalente/project-robocopa-ifma'):
        raise ValueError('Writes are restricted to the authorized disposable CI job')
    file.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    render(ROOT)
    reconcile_feature_documents(ROOT)
    print('Reconciled S04-T04 and generated Markdown; production gates remain blocked')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
