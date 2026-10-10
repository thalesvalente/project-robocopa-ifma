# Tasks: Segurança e isolamento da execução (S04-T04)

**Input:** [spec.md](spec.md), [plan.md](plan.md), [clarifications.md](clarifications.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/job-protocol.md](contracts/job-protocol.md).
**Status:** catálogo de 39 entregas amplas. I1/I2 e recortes I3 possuem provas, mas as caixas amplas permanecem `[ ]` até todo o aceite. Detalhes dos incrementos e evidências abaixo.
**Macro:** S04-T04 `EM_EXECUCAO`; estado histórico `A_FAZER` preservado no Git, sem fechamento de S03/S04.
**Regra:** G-EXP autoriza implementação/testes sintéticos delimitados, G-PROD continua bloqueado. Mudanças na VM/host precisam de plano e autorização específicos. Não executar cargas adversariais no computador pessoal.

Formato: `- [ ] T### [P?] [US#] objetivo, caminho(s), requisitos (FR/SC), ameaças (TH)`. `[P]` indica independência de escrita, não autorização para burlar gates. Linhas das 39 tarefas macro preservadas; caminhos candidatos com hífen não implicam módulos Python publicados nesses caminhos.

## Phase 1 — Governança e preparação (gate G0)

- [ ] T001 [US1] Revisar ratificação S00-T06 e baseline S03-T06 antes de tornar os requisitos de isolamento vinculantes; registrar aceite/ressalvas em `docs/planejamento/decisoes/D-004-aprovacao-sandbox.md`. FR-020; SC-008; TH-01.
- [ ] T002 [P] [US1] Submeter D1–D5 de `specs/004-isolamento-execucao/clarifications.md` ao responsável; registrar decisões, donos e limites sem pressupor aprovação. FR-001, FR-020; SC-008; TH-01.
- [ ] T003 [P] [US2] Revisar riscos e fronteiras em `docs/arquitetura/ameacas-sandbox.md`, incluindo ativo pessoal, bot/árbitro, segredos e replay. FR-003, FR-005, FR-007; SC-002; TH-02, TH-03, TH-05, TH-15.
- [ ] T004 [P] [US3] Definir cenário estritamente sintético, ambiente descartável, plano de limpeza e inventário *antes/depois* para `tests/security/fixtures/` e `docs/qualidade/evidencias/S04-T04-testplan.md`. FR-019; SC-004, SC-007; TH-07, TH-08.

**Checkpoint G0:** decisões aprovadas, riscos avaliados e proibição de testes adversariais no PC pessoal. Gate bloqueado não autoriza implantação.

## Phase 2 — Provas de viabilidade de fronteira (gate G1)

- [ ] T005 [US2] Avaliar Linux/VM exclusiva, runtime, user namespace/rootless/gVisor e compatibilidade de recursos; documentar medição e alternativas em `spikes/isolamento/runtime-compat.md`. FR-005, FR-007, FR-018; SC-002; TH-02.
- [ ] T006 [US2] Demonstrar ausência de drives/volumes pessoais e fronteira de administração independente em VM/runner efêmero; evidenciar em `spikes/isolamento/host-boundary.md`. FR-005, FR-007, FR-019; SC-002; TH-02, TH-03.
- [ ] T007 [US2] Prototipar **apenas com bots oficiais confiáveis** a comunicação árbitro↔bot sem internet/LAN, avaliando external server/booter do Tank Royale; registrar em `spikes/isolamento/engine-separation.md`. FR-005, FR-006, FR-012; SC-002; TH-04, TH-15.

**Checkpoint G1:** evidência real de separação e compatibilidade; não usar Docker Desktop compartilhado como fallback.

## Phase 3 — Fundações do plano de controle (gate G2)

- [ ] T008 [P] [US1] Escrever testes negativos de contrato para pedido direto ao daemon, campos inesperados e falta de permissão em `tests/security/test_job_contract.py`. FR-003, FR-004; SC-001; TH-01, TH-05.
- [ ] T009 [P] [US4] Versionar parser estrito e validações do contrato interno de `packages/job-contracts/`, sem admitir shell, paths ou Docker flags recebidos de usuários. FR-011, FR-012; SC-005; TH-10.
- [ ] T010 [US1] Implementar broker tipado em `services/execution-control/` sem acesso às credenciais do worker nem socket Docker na API pública. FR-003, FR-004, FR-019; SC-001; TH-01, TH-05.
- [ ] T011 [US2] Implementar agente de worker com credencial escopada, canal controlado e política de rede efetiva em `services/worker-agent/`, após a prova T007. FR-005, FR-006, FR-014; SC-002, SC-007; TH-04, TH-05.
- [ ] T012 [US1] Estabelecer controle de habilitação **desligado por padrão** e recusa segura de jobs se política/worker indisponível em `services/execution-control/`. FR-016, FR-020; SC-008; TH-14.

**Checkpoint G2:** tentativas públicas negadas até validar política; broker não administra Docker do host.

## Phase 4 — User Story 1 / autorização e linguagem (P0)

- [ ] T013 [P] [US1] Cobrir classes T0/T1/T2, entradas excessivas, AST inválida, caminho/Unicode e código geral em `tests/security/test_submission_admission.py`. FR-001, FR-002; SC-001; TH-06.
- [ ] T014 [US1] Implementar admissão somente de versão RoboDSL T1 ratificada e política disponível em `services/execution-control/admission/`. FR-001, FR-002, FR-004; SC-001, SC-008; TH-01, TH-06.
- [ ] T015 [US1] Provar, em runner descartável, que requisição recusada não cria job nem chama Docker no host em `tests/security/test_no_host_daemon.py`. FR-003, FR-004, FR-019; SC-001; TH-01, TH-14.
- [ ] T016 [US1] Verificar invariantes fail-closed na fronteira HTTP e broker por testes de contrato em `tests/security/test_fail_closed.py`. FR-016, FR-020; SC-008; TH-01, TH-14.

**Checkpoint US1:** negativos recusados antes da execução; nenhum endpoint público ativado por este catálogo.

## Phase 5 — User Story 2 / sandbox por job (P1)

- [ ] T017 [P] [US2] Fixar imagens aprovadas, digests e fonte de dependências do worker em `services/execution-sandbox/allowlist.json`; proibir download dinâmico durante job. FR-015; SC-007; TH-13.
- [ ] T018 [US2] Construir ciclo de sandbox efêmero por tentativa em `services/execution-sandbox/`, UID não-root, sem socket/mount/privileged/host namespace/GPU. FR-005, FR-007; SC-002; TH-02, TH-03.
- [ ] T019 [US2] Implementar isolamento de egress e canal do árbitro aprovado em `services/execution-sandbox/network-policy/`, com testes de rede internos ao laboratório. FR-006; SC-002; TH-04.
- [ ] T020 [US2] Separar bot do árbitro e validar origem dos resultados/replay em `services/engine-adapter/`, demonstrando que stdout do bot não define placar. FR-005, FR-006, FR-012; SC-002, SC-005; TH-10, TH-15.
- [ ] T021 [US2] Rodar testes negativos de filesystem, socket, segredos e isolamento entre jobs **somente na VM/runner descartável** em `tests/security/test_boundary.py`. FR-005, FR-007, FR-018; SC-002; TH-02, TH-03, TH-05, TH-09.
- [ ] T022 [US2] Inspecionar política **efetiva**, kernel/runtime e recursos na VM, falhando se divergirem do contrato, em `tests/security/test_runtime_attestation.py`. FR-007, FR-018; SC-002, SC-003; TH-02, TH-04.

**Checkpoint US2:** negar acessos indevidos observáveis; resultado inconclusivo bloqueia release.

## Phase 6 — User Story 3 / recursos, falhas e limpeza (P1)

- [ ] T023 [P] [US3] Implementar admissão com quotas de CPU, RAM, PIDs, disco/stdout, concorrência e fila em `services/execution-sandbox/quotas/`. FR-008, FR-017; SC-003; TH-07, TH-16.
- [ ] T024 [US3] Implementar watchdog, deadline e cancelamento da árvore de processos em `services/worker-agent/watchdog/`. FR-009; SC-003; TH-07, TH-08.
- [ ] T025 [US3] Implementar convergência de tentativas abandonadas e cleanup específico por job em `services/worker-agent/recovery/`. FR-009, FR-010, FR-016; SC-004, SC-006; TH-08, TH-14.
- [ ] T026 [US3] Executar 20 ciclos sintéticos com timeout/crash/cancelamento, coletando quotas efetivas e zero órfãos em `tests/security/test_resource_recovery.py`. FR-008, FR-009, FR-010, FR-018; SC-003, SC-004; TH-07, TH-08.
- [ ] T027 [US3] Exercitar concorrência, idempotency key, rejeição de overflow de fila e rate-limit em `tests/security/test_queue_abuse.py`. FR-013, FR-017; SC-006; TH-11, TH-16.

**Checkpoint US3:** recursos medidos/limpos; sem modificar contêineres alheios.

## Phase 7 — User Story 4 / integridade e evidências (P1)

- [ ] T028 [P] [US4] Criar envelope imutável de `SubmissionVersion`, `ExecutionRequest` e `EvidenceManifest` em `packages/job-contracts/`. FR-011; SC-005; TH-10.
- [ ] T029 [US4] Validar replay oficial, hashes, rounds, identidades e formatos na fronteira em `packages/result-validation/`, rejeitando fixtures adversariais. FR-011, FR-012; SC-005; TH-10, TH-15.
- [ ] T030 [US4] Implementar deduplicação transacional de resultados/retries em `services/execution-control/result-ledger/`; registrar transições terminais sem pontuação duplicada. FR-010, FR-013; SC-006; TH-11.
- [ ] T031 [US4] Implementar manifesto/logs sanitizados e varredura de dados sintéticos sensíveis em `packages/result-validation/redaction/`. FR-014; SC-007; TH-12.
- [ ] T032 [US4] Validar hashes/digests de motor e política em cada artefato e em `tests/security/test_supply_chain.py`. FR-011, FR-015, FR-018; SC-005, SC-007; TH-10, TH-13.

**Checkpoint US4:** somente resultados únicos, consistentes e não adulterados integram ledger.

## Phase 8 — User Story 5 / suspensão e operação (P2)

- [ ] T033 [US5] Implementar chave segura de suspensão e rejeição de novos jobs em `services/execution-control/safety-gate/`, com política versionada. FR-016, FR-020; SC-008; TH-14.
- [ ] T034 [US5] Testar worker indisponível, hash/política inválida, timeout de canal e ausência de fallback em `tests/security/test_emergency_stop.py`. FR-016, FR-019; SC-001, SC-008; TH-01, TH-14.
- [ ] T035 [US5] Elaborar runbook de rollback, aprovação e isolamento no host em `docs/operacao/isolamento-runbook.md`; proibir `prune` global ou mudança implícita do VHDX. FR-019, FR-020; SC-007; TH-14.

## Phase 9 — Fechamento e análise final

- [ ] T036 [US1] Executar matriz TH-01..TH-16 em ambiente efêmero com logs sanitizados, estado observado versus esperado e razões de bloqueio em `docs/qualidade/evidencias/S04-T04-MATRIZ.md`. FR-018, FR-020; SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008; TH-01, TH-02, TH-03, TH-04, TH-05, TH-06, TH-07, TH-08, TH-09, TH-10, TH-11, TH-12, TH-13, TH-14, TH-15, TH-16.
- [ ] T037 [P] [US4] Executar regressão e contratos do motor, DSL e segurança no CI em `tests/security/`, sem dados ou credenciais de estudantes. FR-012, FR-015; SC-005, SC-007; TH-10, TH-13.
- [ ] T038 [US5] Com autorização **separada**, reproduzir smoke estritamente controlado da VM, snapshots e rollback no host, documentando evidência real e sem alterar outros serviços em `docs/qualidade/evidencias/S04-T04-HOST.md`. FR-005, FR-019, FR-020; SC-002, SC-008; TH-02, TH-14.
- [ ] T039 [US5] Solicitar revisão independente, resolver achados críticos/altos, ratificar/recusar ADR-004 e atualizar backlog/issue somente com evidência em `docs/planejamento/decisoes/D-004-aprovacao-sandbox.md`. FR-018, FR-020; SC-001, SC-008; TH-01, TH-15.

## Dependencies & Execution Order

G0 (T001–T004) depende de ratificação e limites de autorização; G1 (T005–T007) de G0; G2 (T008–T012) de G1 e baselineS03 para comunicação/autorização. US1 depende de G2, US2 de G1/G2, US3 de G2/US2, US4 de G2 e motor/árbitro; preparar esquema não homologa segurança. US5 depende de G2 e suspensão antes da habilitação. T036–T039 exigem US1..US5 e aceites formais, sem autorização automática de S08.

**Caminho crítico:** T001 → T002 → T005 → T007 → T010 → T011 → T018 → T020 → T021 → T026 → T029 → T033 → T036 → T039.

## Implementation Strategy & Codex handoff

ChatGPT Pro prepara/revisa/executa mudanças delimitadas. Codex somente para implementação pesada justificada após gates, com branch/commit, arquivos permitidos, sandbox descartável, limites, riscos e testes explícitos. Nenhum item amplo vira [x] só por haver design, mock, checklist ou subconjunto experimental aprovado.

## Controle consolidado dos recortes e evidências (2026-10-10)

| Recorte | Resultado no limite definido | Planejamento/evidência |
|---|---|---|
| I1 | Contratos/limites/sondas CI | [Plano](iteration-1.md), [relatório](../../docs/qualidade/evidencias/S04-T04-I1.md) |
| I2 | Separação/arena/limpeza e reconciliação | [R01–R10](i2-reconciliation-plan.md), [C01–C05](i2-reconciliation-decision.md), [relatório](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md) |
| I3-01 | SQLite/broker interno experimental | [Iteração](iteration-3.md), [evidências](../../docs/qualidade/evidencias/S04-T04-I3-01.md) |
| I3-02 | Probe mTLS real de laboratório, não serviço cloud | [Plano](i3-02-auth-plan.md), [evidências](../../docs/qualidade/evidencias/S04-T04-I3-02.md) |
| I3-03 PG | Migration001 e30 testes PostgreSQL reais | [PG-01..06](i3-03-postgres-plan.md), [evidências](../../docs/qualidade/evidencias/S04-T04-I3-03.md) |
| I3-03B AD | Migration002, I1 ligado por driver ao banco;22 integrações reais/25 unidades novas | [AD-01..06](i3-03-admission-plan.md), [contrato](contracts/admission-postgres.md), [relatório](../../docs/qualidade/evidencias/S04-T04-I3-03B.md) |

**I3-03 integral continua EM_EXECUCAO.** AD-01..06 fecham apenas a ponte de serviço interno/CI, mapeada a T008..T016/T028/T030/T037 e HYB-01..03. `ServiceActor` não valida JWT; SCRAM do banco não autentica participante/worker por HTTP. Após002, rc_admission enfileira, rc_broker não usa enqueue bruto. Faltam cliente/API cloud, papéis/identidades operacionais, catálogo/RLS da aplicação, Supabase real e worker outbound; I3-04..07/I4/I5 permanecem abertos.

A revisão de [CI AD](i3-03-admission-ci-fix.md) precedeu a correção do workflow. O estado e os contratos acompanham o código, mas **todas as 39 caixas amplas acima continuam abertas**, assim como os18 gates e G-PROD. Os relatórios históricos conservam seus lotes; os marcos experimentais não liberam estudantes.
