# Evidência de preparação — Feature 004 (planejamento, não implementação)

**Data:** 2026-10-09. **Origem:** revisão do repositório, constituição, ADR-001/002/003, resultados das features 002/003, documentação oficial de Docker/gVisor e instrução do responsável nesta conversa.

## Entregas documentais

- `specs/004-isolamento-execucao/spec.md` — cinco histórias, FR-001..FR-020, SC-001..SC-008, classes T0/T1/T2.
- `clarifications.md` — Q-01..Q-12, decisões D1–D5 e bloqueios explícitos.
- `research.md`, `docs/arquitetura/ameacas-sandbox.md` e `ADR-004-isolamento-execucao.md` — alternativas, 16 ameaças e fronteiras de confiança.
- `plan.md`, `data-model.md`, `contracts/job-protocol.md`, `quickstart.md` — sequência e contratos candidatos.
- `tasks.md` — 39 tarefas de implementação futura, organizadas por fase, US, IDs FR/SC/TH; **todas permanecem desmarcadas**.
- `checklists/requirements.md`, `checklists/security-gates.md` — qualidade de texto e gates de segurança **todos bloqueados**.
- `analysis.md` — revisão cruzada com achados e pendências; não equivale à execução interativa dos comandos slash.
- `scripts/verify_security_spec.py` e testes de planejamento — verificador **somente de documentação**, sem Docker, VM ou rede.

## Evidência da ferramenta e do repositório

Integração Spec Kit previamente instalada/versionada na fundação: `tools/speckit.lock.json`. Esta feature utiliza sua organização e seus artefatos. O workflow `.github/workflows/security-spec.yml` foi definido para executar:

- `python3 scripts/verify_security_spec.py`;
- `python3 -m unittest discover -s tests/planning -v`;
- `python3 .specify/scripts/python/check_prerequisites.py --json --require-spec --require-tasks --include-tasks`;
- `python3 scripts/verify_planning.py` e verificação de projeções do backlog.

**Validação efetivamente conferida (GitHub-hosted Ubuntu 24.04):** [GitHub Actions 38019520410](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38019520410), commit `b59d47cad4f4b41db3f9916c6e2a615d506ea46a`, `completed/success`.

- 20 FR, 8 SC, 16 TH, 12 Q, 5 user stories, 39 tarefas **não iniciadas**, 18 gates **não aprovados**.
- Cobertura estrutural de FR/SC/TH nos textos das tarefas: **100%**; exclusão deliberada da tarefa transversal T036 para não mascarar lacunas.
- **38 testes unitários de planejamento/preservação/verificador** executados, todos OK.
- `check_prerequisites.py` nativo do Spec Kit concluiu com feature 004 reconhecida e documentos research, data-model, contracts, quickstart e tasks disponíveis.
- Projeções do backlog canônico permaneceram idênticas após regeneração.
- **Escopo:** testes de documentação e rastreabilidade, sem VM, contêiner ou ataque. Nenhum gate de segurança operacional foi marcado como concluído.

O primeiro ensaio do workflow encontrou um problema **de formatação da tabela STRIDE** (ID TH e descrição na mesma célula) e foi corretamente reprovado. Os IDs foram separados em coluna própria; o run acima verifica a correção. Isso não foi falha de sandbox, pois nenhuma sandbox foi executada.

## Limitações

Esta rodada **não** executou tentativas de fuga, CPU/RAM/PIDs estressados, ataques de rede, montagem de discos, VM, worker, script adversarial ou instalação no computador pessoal. A arquitetura recomendada é hipótese; o endereço local do laboratório continua proibido para estudantes. Não há segurança homologada, nem decisão humana D1–D5, nem publicação de serviço.

A tarefa macro S04-T04 mantém `A_FAZER` até que dependências, implementação e testes reais sejam formalmente aprovados.

**Referência principal:** `docs/planejamento/decisoes/D-003-preparacao-isolamento.md`.
