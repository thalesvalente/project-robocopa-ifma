# Tasks: Segurança e isolamento da execução (S04-T04)

**Input:** [spec.md](spec.md), [plan.md](plan.md), [clarifications.md](clarifications.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/job-protocol.md](contracts/job-protocol.md).  
**Status:** catálogo de 39 entregas amplas. O incremento I1 já implementa subconjuntos de contratos/política/limites, com provas reais no CI; as caixas amplas permanecem `[ ]` até atender todo seu aceite. Progresso/evidência: [iteration-1.md](iteration-1.md).  
**Macro:** S04-T04 em `EM_EXECUCAO` após D-005 e I1; estado histórico `A_FAZER` preservado no Git, sem fechamento dos gates S03/S04.  
**Regra de execução:** G-EXP autoriza o incremento I1 em CI descartável; G-PROD continua bloqueado. Antes de alterações/VM no host é necessário plano e autorização próprios. Não executar cargas adversariais no computador pessoal.

Formato: `- [ ] T### [P?] [US#] objetivo, caminho(s), requisitos (FR/SC), ameaças (TH)`. `[P]` indica independência de escrita, **não** autorização para burlar gates.

## Phase 1 — Governança e preparação (gate G0)

- [ ] T001 [US1] Revisar ratificação S00-T06 e baseline S03-T06 antes de tornar os requisitos de isolamento vinculantes; registrar aceite/ressalvas em `docs/planejamento/decisoes/D-004-aprovacao-sandbox.md`. FR-020; SC-008; TH-01.
- [ ] T002 [P] [US1] Submeter D1–D5 de `specs/004-isolamento-execucao/clarifications.md` ao responsável; registrar decisões, donos e limites sem pressupor aprovação. FR-001, FR-020; SC-008; TH-01.
- [ ] T003 [P] [US2] Revisar riscos e fronteiras em `docs/arquitetura/ameacas-sandbox.md`, incluindo ativo pessoal, bot/árbitro, segredos e replay. FR-003, FR-005, FR-007; SC-002; TH-02, TH-03, TH-05, TH-15.
- [ ] T004 [P] [US3] Definir cenário estritamente sintético, ambiente descartável, plano de limpeza e inventário *antes/depois* para `tests/security/fixtures/` e `docs/qualidade/evidencias/S04-T04-testplan.md`. FR-019; SC-004, SC-007; TH-07, TH-08.
  
**Checkpoint G0:** decisões aprovadas, riscos avaliados e *proibição de executar testes adversariais no computador pessoal* respeitada. Se bloqueado, não seguir.

## Phase 2 — Provas de viabilidade de fronteira (gate G1)

- [ ] T005 [US2] Avaliar Linux/VM exclusiva, runtime, user namespace/rootless/gVisor e compatibilidade de recursos; documentar medição e alternativas em `spikes/isolamento/runtime-compat.md`. FR-005, FR-007, FR-018; SC-002; TH-02.
- [ ] T006 [US2] Demonstrar ausência de drives/volumes pessoais e fronteira de administração independente em VM/runner efêmero; evidenciar em `spikes/isolamento/host-boundary.md`. FR-005, FR-007, FR-019; SC-002; TH-02, TH-03.
- [ ] T007 [US2] Prototipar **apenas com bots oficiais confiáveis** a comunicação árbitro↔bot sem internet/LAN, avaliando external server/booter do Tank Royale; registrar em `spikes/isolamento/engine-separation.md`. FR-005, FR-006, FR-012; SC-002; TH-04, TH-15.

**Checkpoint G1:** evidência real de separação e compatibilidade. Se falhar, estudar worker externo; não fazer fallback ao Docker Desktop compartilhado.

## Phase 3 — Fundações do plano de controle (gate G2)

- [ ] T008 [P] [US1] Escrever testes negativos de contrato para pedido direto ao daemon, campos inesperados e falta de permissão em `tests/security/test_job_contract.py`. FR-003, FR-004; SC-001; TH-01, TH-05.
- [ ] T009 [P] [US4] Versionar parser estrito e validações do contrato interno de `packages/job-contracts/`, sem admitir shell, paths ou Docker flags recebidos de usuários. FR-011, FR-012; SC-005; TH-10.
- [ ] T010 [US1] Implementar broker tipado em `services/execution-control/` sem acesso às credenciais do worker nem socket Docker na API pública. FR-003, FR-004, FR-019; SC-001; TH-01, TH-05.
- [ ] T011 [US2] Implementar agente de worker com credencial escopada, canal controlado e política de rede efetiva em `services/worker-agent/`, após a prova T007. FR-005, FR-006, FR-014; SC-002, SC-007; TH-04, TH-05.
- [ ] T012 [US1] Estabelecer controle de habilitação **desligado por padrão** e recusa segura de jobs se política/worker indisponível em `services/execution-control/`. FR-016, FR-020; SC-008; TH-14.

**Checkpoint G2:** toda tentativa pública é negada enquanto a política não estiver validada; broker não invoca diretamente host Docker.

## Phase 4 — User Story 1 / autorização e linguagem (P0)

- [ ] T013 [P] [US1] Cobrir classes T0/T1/T2, entradas excessivas, AST inválida, caminho/Unicode e código geral em `tests/security/test_submission_admission.py`. FR-001, FR-002; SC-001; TH-06.
- [ ] T014 [US1] Implementar admissão somente de versão RoboDSL T1 ratificada e política disponível em `services/execution-control/admission/`. FR-001, FR-002, FR-004; SC-001, SC-008; TH-01, TH-06.
- [ ] T015 [US1] Provar, em runner descartável, que requisição recusada não cria job nem chama Docker no host em `tests/security/test_no_host_daemon.py`. FR-003, FR-004, FR-019; SC-001; TH-01, TH-14.
- [ ] T016 [US1] Verificar invariantes fail-closed na fronteira HTTP e broker por testes de contrato em `tests/security/test_fail_closed.py`. FR-016, FR-020; SC-008; TH-01, TH-14.

**Checkpoint US1:** todos os negativos rejeitados antes de execução; não há endpoint público ativado.

## Phase 5 — User Story 2 / sandbox por job (P1)

- [ ] T017 [P] [US2] Fixar imagens aprovadas, digests e fonte de dependências do worker em `services/execution-sandbox/allowlist.json`; proibir download dinâmico durante job. FR-015; SC-007; TH-13.
- [ ] T018 [US2] Construir ciclo de sandbox efêmero por tentativa em `services/execution-sandbox/`, UID não-root, sem socket/mount/privileged/host namespace/GPU. FR-005, FR-007; SC-002; TH-02, TH-03.
- [ ] T019 [US2] Implementar isolamento de egress e canal do árbitro aprovado em `services/execution-sandbox/network-policy/`, com testes de rede internos ao laboratório. FR-006; SC-002; TH-04.
- [ ] T020 [US2] Separar bot do árbitro e validar origem dos resultados/replay em `services/engine-adapter/`, demonstrando que stdout do bot não define placar. FR-005, FR-006, FR-012; SC-002, SC-005; TH-10, TH-15.
- [ ] T021 [US2] Rodar testes negativos de filesystem, socket, segredos e isolamento entre jobs **somente na VM/runner descartável** em `tests/security/test_boundary.py`. FR-005, FR-007, FR-018; SC-002; TH-02, TH-03, TH-05, TH-09.
- [ ] T022 [US2] Inspecionar política **efetiva**, kernel/runtime e recursos na VM, falhando se divergirem do contrato, em `tests/security/test_runtime_attestation.py`. FR-007, FR-018; SC-002, SC-003; TH-02, TH-04.

**Checkpoint US2:** negar todos os acessos indevidos observáveis; resultado inconclusivo bloqueia release.

## Phase 6 — User Story 3 / recursos, falhas e limpeza (P1)

- [ ] T023 [P] [US3] Implementar admissão com quotas de CPU, RAM, PIDs, disco/stdout, concorrência e fila em `services/execution-sandbox/quotas/`. FR-008, FR-017; SC-003; TH-07, TH-16.
- [ ] T024 [US3] Implementar watchdog, deadline e cancelamento da árvore de processos em `services/worker-agent/watchdog/`. FR-009; SC-003; TH-07, TH-08.
- [ ] T025 [US3] Implementar convergência de tentativas abandonadas e cleanup específico por job em `services/worker-agent/recovery/`. FR-009, FR-010, FR-016; SC-004, SC-006; TH-08, TH-14.
- [ ] T026 [US3] Executar 20 ciclos sintéticos com timeout/crash/cancelamento, coletando quotas efetivas e zero órfãos em `tests/security/test_resource_recovery.py`. FR-008, FR-009, FR-010, FR-018; SC-003, SC-004; TH-07, TH-08.
- [ ] T027 [US3] Exercitar concorrência, idempotency key, rejeição de overflow de fila e rate-limit em `tests/security/test_queue_abuse.py`. FR-013, FR-017; SC-006; TH-11, TH-16.

**Checkpoint US3:** recursos medidos e limpos; nenhuma modificação em contêineres fora do worker.

## Phase 7 — User Story 4 / integridade e evidências (P1)

- [ ] T028 [P] [US4] Criar envelope imutável de `SubmissionVersion`, `ExecutionRequest` e `EvidenceManifest` em `packages/job-contracts/`. FR-011; SC-005; TH-10.
- [ ] T029 [US4] Validar replay oficial, hashes, rounds, identidades e formatos na fronteira em `packages/result-validation/`, rejeitando fixtures adversariais. FR-011, FR-012; SC-005; TH-10, TH-15.
- [ ] T030 [US4] Implementar deduplicação transacional de resultados/retries em `services/execution-control/result-ledger/`; registrar transições terminais sem pontuação duplicada. FR-010, FR-013; SC-006; TH-11.
- [ ] T031 [US4] Implementar manifesto/logs sanitizados e varredura de dados sintéticos sensíveis em `packages/result-validation/redaction/`. FR-014; SC-007; TH-12.
- [ ] T032 [US4] Validar hashes/digests de motor e política em cada artefato e em `tests/security/test_supply_chain.py`. FR-011, FR-015, FR-018; SC-005, SC-007; TH-10, TH-13.

**Checkpoint US4:** somente resultados consistentes, únicos e não adulterados podem integrar o ledger.

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

- **G0** (T001–T004) depende da ratificação e dos limites de autorização.
- **G1** (T005–T007) depende de G0. Se compatibilidade e separação do árbitro falharem, parar.
- **G2** (T008–T012) depende de G1 e da baseline S03 para comunicação/autorização.
- **US1** (T013–T016) depende de G2; valida a admissão antes de aceitar qualquer bot de estudante.
- **US2** (T017–T022) depende de G1/G2 e do canal do árbitro; somente testes descartáveis.
- **US3** (T023–T027) depende de G2/US2 para métricas reais.
- **US4** (T028–T032) depende de G2 e do motor/árbitro; pode preparar esquemas enquanto US2/US3 são testados.
- **US5** (T033–T035) depende de G2; a suspensão deve existir antes de habilitar qualquer ambiente.
- **Fechamento** (T036–T039) depende de US1..US5 e de aceites formais; não autoriza automaticamente S08.

**Caminho crítico:** T001 → T002 → T005 → T007 → T010 → T011 → T018 → T020 → T021 → T026 → T029 → T033 → T036 → T039.

## Implementation Strategy & Codex handoff

ChatGPT Pro prepara, revisa e executa mudanças delimitadas. **Codex apenas para implementação pesada**, por exemplo separação de booter/árbitro, worker, testes intensivos e operações de concorrência, e somente após G0/G1. O handoff deve registrar branch/commit, arquivos permitidos, sandbox estritamente descartável, limites de recursos, testes esperados, riscos e como não afetar Docker Desktop existente.

**Regra irrevogável para este documento:** nenhum item marcado [x] apenas por existir um design, mock ou checklist; status de implementação inicia totalmente pendente.

## Controle da reconciliação do recorte I2

Subtarefas [R01–R10 concluídas](i2-reconciliation-plan.md), com decisão [C01–C05 fechada](i2-reconciliation-decision.md), [evidências técnicas](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md) e [manifesto legível por máquina](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.json). O encerramento é **somente experimental**; as 39 caixas amplas permanecem abertas até seus critérios integrais, inclusive I3/I4/I5 e revisão independente. Não liberar submissões de estudantes.

## Subtarefas do I3 — refinamento antes do código

[Plano I3 por entregas](iteration-3.md) e [decisões](i3-design-decisions.md) são a decomposição autorizada experimental para subconjuntos de T008–T016/T023–T025/T027–T030/T033–T035/T037. O check de cada I3-01a..I3-01e só muda com evidência; **as caixas T001–T039 acima seguem abertas** até o aceite macro. I3-01 não implementa API, worker ou autenticação, nem satisfaz o gate G2 em produção. Os próximos I3-02..I3-07 dependem de decisões/testes próprios antes de execução de código de estudantes.

**Estado do recorte I3-01 (2026-10-10):** [I3-01a..e concluídos experimentalmente](iteration-3.md), [relatório CI/negativos](../../docs/qualidade/evidencias/S04-T04-I3-01.md). Permanecem **todas as 39 T001–T039 amplas como abertas**: o protótipo offline NÃO entrega broker de produção, autenticação worker, fila Postgres, ledger, VM nem liberação. I3-02..I3-07 [ ] exigem desenho e implementação próprios.
