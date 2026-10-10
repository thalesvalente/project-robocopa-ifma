# I3-03 — Núcleo PostgreSQL de jobs, leases e fencing

**Data:** 2026-10-10. **Plano inicial:** publicado em `afd8bd6`, antes da migration. **Estado atual do núcleo PG-01..06:** VALIDADO_NO_CI. **I3-03 integral:** EM_EXECUCAO, pois falta integração do serviço cloud com worker autenticado. **Base:** PR #24 fbdf207 + main 64863ec (D-006/ADR-005); D-007/ADR-006 registram a aprovação posterior à revisão. **Macro:** S04-T04 EM_EXECUCAO. **G-EXP:** dados sintéticos em GitHub-hosted descartável; G-PROD bloqueado.

## Contexto e Constituição

Reutilizar requisitos FR-003/004/008/009/010/011/013/014/016/017/018/019/020; TH-01/05/08/09/10/11/14/16; T008..T016/T023..T025/T027/T028/T030/T033..T037. Nenhuma das 39 caixas amplas muda por esse recorte. Sem linguagem nova, dados de menores, exposição de host ou autenticação fingida. SQLite I3-01 e mTLS I3-02 continuam provas históricas separadas.

## Pesquisa e decisão antes do código

ADR-006 compara pgmq e tabela de jobs: usar uma tabela PostgreSQL transacional canônica para esta etapa, sem Redis/pgmq paralelo, sem alegar exactly-once de processos. PostgreSQL 17 em CI (major já usado no laboratório), nenhuma dependência PostgreSQL instalada no PC do usuário. SQL versionado é independente de Node/Python/Deno/HTTP. O broker cloud de chamadas curtas será integrado em subentrega posterior; não ligar o probe mTLS de laboratório a jobs por mera reutilização.

## Entidades e contrato interno

Schema privado `rc_control`. `settings` guarda gate OFF/capacidade/lease/limite de tentativas; `workers` guarda identidade sintética, escopo, ativo; `jobs` guarda chave idempotente por owner, descriptor imutável admitido, escopo, deadline, estado, geração e tentativa corrente; `attempts` guarda a história por job/geração/worker. Não guardar código-fonte ou credenciais. Descriptor contém apenas version_id, hashes de fonte/programa/política, engine_ref fixo e rounds 1..3. Chamador é um serviço confiável que já passou por I1, não navegador/worker nem endpoint público.

Funções SQL: enqueue, claim, start/heartbeat, fail_attempt, cancel e reap. Reserva usa FOR UPDATE SKIP LOCKED. IDs de job/attempt gerados pelo banco. Chave repetida com mesmos dados devolve o mesmo job, mesmo com fila cheia; payload diferente conflita. Capacidade é contada e reservada sob trava de settings. Clock do banco, deadline máximo 240 s e lease curta limitada por deadline; configuração experimental não é quota de produção.

Uma lease expirada não pode ser renovada ou usada. Reap terminaliza a tentativa e reencaminha o job se ainda houver tempo/tentativas; senão FAILED/EXPIRED. A próxima reserva incrementa fencing. CANCELLED é idempotente e não volta à fila. Worker revogado não recebe/renova reserva. Suspensão bloqueia novas admissões/reservas, permitindo cancelar/recolher. Só I3-04 poderá criar COMPLETED/score; esta migration deliberadamente não inclui publicação de resultados. [Contrato SQL](contracts/postgres-control.md).

## Plano executável e aceites do núcleo de persistência

- [x] PG-01 [US1/US5] Reconciliar ADR-005/#23/#24, publicar D-007/ADR-006, plano e contrato antes da migration. Evidência: commits afd8bd6/8cdeaa5 anteriores a 78cdd43; ancestralidade preservada, sem merge na main.
- [x] PG-02 [US1/US4] Migration privada `services/execution_control/postgres/001_control.sql`: roles NOLOGIN sem superuser, schema privado, RLS, grants por função e gate OFF. Reaplicação recusa sem apagar tabelas. Provas reais de privilégios no CI 38074491846.
- [x] PG-03 [US3] Funções atômicas de enfileiramento/reserva, clock de banco, timeout, tentativas/fencing, start/heartbeat, falha/retry limitado, cancelamento e recolhimento. Sem Docker/rede em SQL. F02 corrigido e retestado.
- [x] PG-04 [US1/US3/US4] PostgreSQL REAL no CI: 30 testes com concorrência, idempotência/capacidade, scopes/worker revogado, token/attempt antigos negados, expiração real, cancelamento concorrente, rollback e restart do banco em volume persistente owned. Não é teste SQLite nem Supabase implantado.
- [x] PG-05 [US1/US4] anon/authenticated/worker sem tabelas/funções; rc_broker somente funções, sem DML direto nem habilitação de gate; RLS nega leitura mesmo após grant SELECT acrescentado na fixture. Não é RLS da futura aplicação de alunos.
- [x] PG-06 [US5] Evidência JSON sanitizada, versão PostgreSQL 17.11, fonte/checkout/run/hash da migration e cleanup; seis workflows PASS, 382 regressões reproduzidas na sessão; I2 real auditado fora do runner. Três testes de erro de cleanup, explicitamente com Docker falso, detectam a falha antiga. [Relatório](../../docs/qualidade/evidencias/S04-T04-I3-03.md).

## Procedimento de teste e autorização

Workflow próprio GitHub-hosted Ubuntu. Imagem postgres:17-alpine fixada no digest observado `sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`, `--network none`, sem portas publicadas e volume nomeado/rotulado owned. Python stdlib invoca psql por docker exec, sem driver/DB remoto; identidade do contêiner conferida antes de uso. SQL chega via stdin, sem binds de host. Recursos finitos e cleanup exclusivo em always, inclusive volume; consultas de cleanup devem ter sucesso antes da confirmação. Senha apenas sintética/efêmera, sem exportação de banco/credenciais.

Prontidão agora exige TCP loopback **dentro** do contêiner e SELECT 1 no banco correto. O primeiro run falhou antes dos testes; F01 não foi contabilizado como PASS. O teste de restart usa o mesmo volume do CI, não tmpfs. As 382 regressões locais não executaram PostgreSQL/Docker; transportes herdados usam loopback. A execução real de PostgreSQL ocorreu exclusivamente no CI.

## Revisões e trilha de correções

- [F01/C01 — prontidão e cobertura de CI](i3-03-ci-audit-plan.md): primeiro lote 38073651799 executou zero testes; correção exigiu consulta real e incluiu a arena I2 nos paths do CI.
- [F02 — escopo da variável de reap](i3-03-reap-fix-plan.md): lote 38073977886 teve 25/29 PASS e quatro erros em reap. Variável v_reason sem qualificação inválida corrigiu o trecho; regressão de motivo/idempotência adicionada.
- [C02 — erro de cleanup](i3-03-cleanup-plan.md): revisão detectou possibilidade de erro do daemon virar string vazia. Atribuições shell com exit code obrigatório e três testes negativos/positivos corrigiram o tratamento. Não se observou daemon falho no lote real; a injeção é uma fixture declarada.

Todos esses adendos precederam os respectivos patches. O relatório registra o resultado posterior; os documentos de planejamento preservam seu contexto inicial.

## Gate e próxima etapa

**Fonte validada do núcleo:** 0b97ee6d7e69bc06806f498ee29278a97c2fa8a6. PG-01..06 concluídos apenas no escopo de persistência do CI. Não fecha I3-03 integral: faltam ligação com admissão/autenticação do broker cloud, claim outbound pela VM, bootstrap/revogação operacional e teste fim a fim. Depois vêm I3-04 ledger/Storage, I3-05 quotas/polling, I3-06 recovery ampliado, I3-07 integração, I4 VM, I5 backup e go/no-go. A demonstração à diretoria permanece NO-GO enquanto não houver jornada completa ensaiada; não habilitar alunos com este código.

Rollback desta rodada: não mesclar/reverter somente o commit da branch. Não rodar DROP SCHEMA/roles em banco real. PR #26 permanece draft, sem merge automático; a main e o PC pessoal não foram alterados.
