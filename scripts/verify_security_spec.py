#!/usr/bin/env python3
"""Verificação documental da Feature 004, offline e sem execução de sandbox.

PASS neste script NÃO equivale a segurança comprovada nem autorização de deploy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

FEATURE = "specs/004-isolamento-execucao"
REQUIRED = (
    "spec.md", "clarifications.md", "research.md", "plan.md",
    "data-model.md", "contracts/job-protocol.md", "quickstart.md",
    "tasks.md", "analysis.md", "checklists/requirements.md",
    "checklists/security-gates.md",
)
THREATS = "docs/arquitetura/ameacas-sandbox.md"
ADR = "docs/arquitetura/ADR-004-isolamento-execucao.md"
DECISION = "docs/planejamento/decisoes/D-003-preparacao-isolamento.md"
TASK_RE = re.compile(r"^- \[ \] T(?P<id>\d{3}) (?:\[P\] )?\[(?P<story>US[1-5])\] (?P<text>.+)$", re.M)
FR_RE = re.compile(r"^- \*\*FR-(\d{3})\*\*:", re.M)
SC_RE = re.compile(r"^- \*\*SC-(\d{3})\*\*:", re.M)
TH_RE = re.compile(r"^\| TH-(\d{2}) \|", re.M)
Q_RE = re.compile(r"^\| Q-(\d{2}) \|", re.M)
SG_RE = re.compile(r"^- \[ \] SG(\d{3})\b", re.M)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")


class PlanningError(ValueError):
    pass


def expect_sequence(actual: list[str], number: int, width: int, label: str) -> None:
    expected = [f"{i:0{width}d}" for i in range(1, number + 1)]
    if actual != expected:
        raise PlanningError(f"{label}: esperados IDs únicos e sequenciais de 1 a {number}")


def read_sources(root: Path) -> dict[str, str]:
    names = [f"{FEATURE}/{part}" for part in REQUIRED] + [THREATS, ADR, DECISION]
    sources = {}
    for name in names:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise PlanningError(f"Documento ausente ou link simbólico: {name}")
        sources[name] = path.read_text(encoding="utf-8")
    return sources


def validate_texts(sources: dict[str, str]) -> dict[str, int | str]:
    spec = sources[f"{FEATURE}/spec.md"]
    tasks = sources[f"{FEATURE}/tasks.md"]
    clarifications = sources[f"{FEATURE}/clarifications.md"]
    plan = sources[f"{FEATURE}/plan.md"]
    gates = sources[f"{FEATURE}/checklists/security-gates.md"]
    analysis = sources[f"{FEATURE}/analysis.md"]
    threats = sources[THREATS]

    fr = FR_RE.findall(spec)
    sc = SC_RE.findall(spec)
    th = TH_RE.findall(threats)
    q = Q_RE.findall(clarifications)
    sg = SG_RE.findall(gates)
    expect_sequence(fr, 20, 3, "FR")
    expect_sequence(sc, 8, 3, "SC")
    expect_sequence(th, 16, 2, "TH")
    expect_sequence(q, 12, 2, "Q")
    expect_sequence(sg, 18, 3, "SG")
    stories = re.findall(r"^### User Story ([1-5]) ", spec, flags=re.M)
    if stories != list("12345"):
        raise PlanningError("User stories não estão completas ou ordenadas")

    matches = list(TASK_RE.finditer(tasks))
    expect_sequence([m.group("id") for m in matches], 39, 3, "Tasks")
    if re.search(r"^- \[[xX]\] T\d{3}\b", tasks, re.M):
        raise PlanningError("Tarefa de implementação marcada concluída sem evidência")
    if re.search(r"^- \[[xX]\] SG\d{3}\b", gates, re.M):
        raise PlanningError("Gate de segurança marcado como aprovado")
    if "NÃO IMPLEMENTAR" not in plan or "GATE BLOQUEADO" not in plan:
        raise PlanningError("Plano não bloqueia implementação antecipada")
    if "S04-T04" not in spec or "S04-T04" not in tasks:
        raise PlanningError("Rastreabilidade macro ausente")
    if "A_FAZER" not in tasks or "sem implementação" not in spec.lower():
        raise PlanningError("Estado do planejamento apresentado como implementação")
    if "BLOQUEADO" not in gates:
        raise PlanningError("Gates sem indicação do bloqueio")
    if "ABERTO" not in clarifications or "CANDIDATO" not in clarifications:
        raise PlanningError("Decisões em aberto/pendentes não identificadas")
    if "A-001" not in analysis or "A-009" not in analysis:
        raise PlanningError("Análise de consistência incompleta")

    specific_text = " ".join(m.group("text") for m in matches if m.group("id") != "036")
    all_task_text = " ".join(m.group("text") for m in matches)
    ids = {
        "FR": {f"FR-{i}" for i in fr},
        "SC": {f"SC-{i}" for i in sc},
        "TH": {f"TH-{i}" for i in th},
    }
    for prefix, known in ids.items():
        width = 2 if prefix == "TH" else 3
        pattern = rf"\b{prefix}-\d{{{width}}}\b"
        used = set(re.findall(pattern, all_task_text))
        missing = known - set(re.findall(pattern, specific_text))
        unknown = used - known
        if missing:
            raise PlanningError(f"{prefix}: requisitos sem tarefa específica {sorted(missing)}")
        if unknown:
            raise PlanningError(f"{prefix}: tarefa referencia ID inexistente {sorted(unknown)}")
    for match in matches:
        line = match.group("text")
        if not re.search(r"\bFR-\d{3}\b", line):
            raise PlanningError(f"T{match.group('id')}: requisito FR ausente")
        if not re.search(r"\bTH-\d{2}\b", line):
            raise PlanningError(f"T{match.group('id')}: ameaça TH ausente")

    return {
        "functional_requirements": len(fr),
        "success_criteria": len(sc),
        "threats": len(th),
        "clarifications": len(q),
        "security_gates_unapproved": len(sg),
        "user_stories": len(stories),
        "tasks_pending": len(matches),
        "coverage_fr_sc_th_percent": 100,
        "scope": "SOMENTE DOCUMENTACAO; NAO E TESTE DE SANDBOX",
    }


def validate_links(root: Path, sources: dict[str, str]) -> None:
    for name, text in sources.items():
        parent = (root / name).parent
        for link in LINK_RE.findall(text):
            if "://" in link or link.startswith("#"):
                continue
            path = (parent / link).resolve()
            if not path.is_relative_to(root.resolve()):
                raise PlanningError(f"Link sai da raiz: {name}")
            if not path.is_file():
                raise PlanningError(f"Link não encontrado: {name} -> {link}")


def validate(root: Path) -> dict[str, int | str]:
    sources = read_sources(root)
    result = validate_texts(sources)
    validate_links(root, sources)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        summary = validate(Path(__file__).resolve().parents[1])
    except (PlanningError, OSError, UnicodeError, KeyError) as exc:
        print("FAIL documentação: " + str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("PASS planejamento: 20 FR, 8 SC, 16 TH, 12 Q, 5 US, 39 tarefas abertas, 18 gates bloqueados.")
        print("NENHUM teste adversarial ou implantação foi executado por este verificador.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
