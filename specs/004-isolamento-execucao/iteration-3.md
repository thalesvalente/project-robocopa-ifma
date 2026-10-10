# S04-T04 / I3 — Plano de execução do plano de controle seguro (antes do código)

**Data:** 2026-10-10 · **Origem:** `main` em `69c624dfc2862fd53ea21a1cef316b861cb97c9b` após I1/I2 integrados.  
**Situação:** PLANEJADO; este documento deve ser commitado **antes** do runtime. **G-EXP** autoriza testes finitos com dados fictícios no runner descartável; **G-PROD bloqueado**.  
**Dependências:** [spec.md](spec.md), [plan.md](plan.md), [tasks.md](tasks.md), [data-model.md](data-model.md), [job-protocol.md](contracts/job-protocol.md), [decisões I3](i3-design-decisions.md). Tarefas amplas T008–T016, T023–T025, T027–T030, T033–T035, T037 permanecem abertas.

## Revisão da preparação

O catálogo macro define objetivos de broker, credenciais, fila, idempotência e recuperação, mas **não** escolhe transporte/identidade nem define concorrência e transições concretas; Q-07 permanece ABERTO. O contrato lógico não é endpoint e o `admit` do I1 só entrega descritor validado. Assim, não havia plano de implementação integral do I3. Preencher estas lacunas aqui sem fingir aprovação institucional/segurança de produção. Na documentação do contrato, incluir `source_sha256`, já exigido pela implementação I1.

## Objetivo e limites invariantes

- Primeira entrega: broker e fila persistente **internos/offline e desligados por padrão**, sem HTTP, WebSocket, mTLS fictício, API pública, worker/Docker/VM, estudantes, código hostil ou execução de partidas.
- Usar somente RoboDSL básica T1 previamente registrada; pedidos T0/T2, idioma novo, competição, shell e Docker flags continuam negados.
- Identidade `owner_ref` é injetada por chamador interno confiável na fixture, **não é autenticação**. Nunca aceitar identidade/flag de habilitação do JSON de participante.
- Banco SQLite isolado em caminho temporário do teste, sem credenciais de produção e **não migrado para o PostgreSQL real**. A durabilidade testada em arquivo SQLite não prova o comportamento em Postgres; adaptador e migração são subentregas posteriores.
- Falha de admissão, indisponibilidade e capacidade excedida resultam em recusa antes de criar job. Sem fallback para máquina do responsável. Evidências mostram apenas resultados sintéticos e contagens; nunca gravar fonte, nome de aluno, senha, IP, payload integral ou segredos.

## Subentregas e critérios para o recorte I3-01

- [ ] **I3-01a** [US1/US4] Definir contrato persistente mínimo, limites e modelo de ameaças/decisões em `i3-design-decisions.md`; publicar este plano antes do código. T008–T012, T028; FR-003/004/011/013/016/017/020, TH-01/05/11/14/16.
- [ ] **I3-01b** [US1/US4] Construir `services/execution_control/store.py`, SQLite estrito somente para laboratório; transações `BEGIN IMMEDIATE`, unicidade `job_id`, `attempt_id`, `(owner_ref,idempotency_key)`, constraints de estado/limites, persistência pós-reinício; sem worker consumidor. Nunca usar SQLite `:memory:` como evidência de durabilidade. T009/T010/T028/T030 recortes.
- [ ] **I3-01c** [US1/US5] `broker.py`: integrar `services.worker_agent.contracts.admit` com gate desligado por padrão, atestado de worker **fictício apenas em testes**, janela temporal e autorização de versão preexistente; nenhuma escrita quando gate/worker/validação/capacidade falhar. Mesmo idempotency key + envelope idêntico = mesmo job; mesma chave + pedido diferente = erro; colisões de IDs = erro. T010/T012/T014/T016/T027 recortes.
- [ ] **I3-01d** [US3/US4] Testes em `tests/security/test_i3_control_plane.py`: desligado, worker indisponível, T2, JSON inválido, hash/tokens, idempotência repetida/conflitante, donos independentes, capacidade, concorrência, reinício do processo e nenhuma invocação a Docker/rede. Nenhuma afirmação de autenticação real. T008/T015/T027/T037 recortes.
- [ ] **I3-01e** [US5] Executar regressão do I1/I2 e planejamentos/Spec Kit; registrar SHA/runs, número de testes, limitações em `docs/qualidade/evidencias/S04-T04-I3-01.md`; reter o status das 39 tarefas amplas e G-PROD BLOQUEADO.

**Gate I3-01:** sem teste inconclusivo/falha; dados SQLite sintéticos persistem ao reabrir; concorrência não duplica jobs; fila não inicia bot; documentação e CI vinculados ao commit. **I3 permanece EM_EXECUCAO** mesmo que I3-01 passe.

## Entregas seguintes — não implementar sem planejar o contrato detalhado

- [ ] **I3-02** [US1/US2] Escolher e provar identidade confiável de broker/worker, rotação/revogação, canal autenticado e autorização por função/objeto, sem inventar criptografia ou aceitar `owner_ref` sem autenticação. Q-07 deve ser resolvida **antes** de qualquer claim remoto. T010/T011/T014/T015/T016.
- [ ] **I3-03** [US3] Implementar claim/lease curto por worker autorizado, fencing token monotônico, worker heartbeat, deduplicação por tentativa, estados atômicos, cancelamento e expiração. T011/T023–T025/T027.
- [ ] **I3-04** [US4] Validar resposta do árbitro, ligar identidade/programa/política à tentativa vigente e lançar evento de resultado e efeito de pontuação **exatamente uma vez** no ledger transacional. Não consumir stdout do bot como placar. T028–T032.
- [ ] **I3-05** [US3] Quotas por dono e global, concorrência, rate-limit e overflow; medição e limites progressivos do motor, sem tratar quota experimental como produção. T023/T027.
- [ ] **I3-06** [US5] Suspensão operacional, reinício/crash da fila, compensação/recovery, retenção mínima e runbook, com testes sintéticos finitos e limpeza apenas owned. T025/T033–T035.
- [ ] **I3-07** [US1..US5] Integração contra worker isolado em CI efêmero, testes de falha/reativação, matriz de ameaça do plano de controle, auditoria de regressão e aceite experimental; produção e VM ainda dependem de I4/I5 e de revisão humana.

## Invariantes de segurança e teste

1. Sem executor integrado, `QUEUED` não significa `RUNNING`; não há transição externa no I3-01.
2. Banco de teste é criado somente em diretório temporário do runner; transação de admissão/verificação de capacidade/escrita é indivisível. Conexões concorrentes não geram dois jobs para a mesma chave.
3. Duplicação idêntica é sem efeito; conflituosa é negada; erros retornam códigos sanitizados. Queda antes do `COMMIT` não deve criar job observável.
4. Dados enviados ao worker, credenciais, segredo do banco e Docker socket não são armazenados na fila experimental.
5. Arquivos persistentes do laboratório não migram implicitamente ao banco da plataforma. Escolha Postgres/SQLite definitiva, auth e semântica distribuída exigem novas decisões testáveis.
6. No CI, `unittest` e verificador nativo do Spec Kit; nenhuma conexão com o servidor pessoal. Revisar logs e capturas para dados não sanitizados.
7. Toda necessidade descoberta não coberta aqui gera adendo **antes** do patch.

## Referências de projeto e fontes externas

- [Decisões I3](i3-design-decisions.md) e [contrato lógico](contracts/job-protocol.md).
- [Python sqlite3 3.13 — transações explícitas](https://docs.python.org/3.13/library/sqlite3.html).
- [OWASP API5:2023 — negar privilégios por padrão](https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/).
- [OWASP API2:2023 — não improvisar autenticação](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/).
