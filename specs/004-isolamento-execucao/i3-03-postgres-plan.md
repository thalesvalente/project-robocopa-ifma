# I3-03 — Núcleo PostgreSQL de jobs, leases e fencing

**Data:** 2026-10-10. **Estado inicial:** PLANEJADO antes do código. **Base:** PR #24 fbdf207 + main 64863ec (D-006/ADR-005); D-007/ADR-006 registram a nova aprovação. **Macro:** S04-T04 EM_EXECUCAO. **G-EXP:** dados sintéticos em GitHub-hosted descartável; G-PROD bloqueado.

## Contexto e Constituição

Reutilizar requisitos FR-003/004/008/009/010/011/013/014/016/017/018/019/020; TH-01/05/08/09/10/11/14/16; T008..T016/T023..T025/T027/T028/T030/T033..T037. Nenhuma das 39 caixas amplas muda por esse recorte. Sem linguagem nova, dados de menores, exposição de host ou autenticação fingida. SQLite I3-01 e mTLS I3-02 continuam provas históricas separadas.

## Pesquisa e decisão antes do código

ADR-006 compara pgmq e tabela de jobs: usar uma tabela PostgreSQL transacional canônica para esta etapa, sem Redis/pgmq paralelo, sem alegar exactly-once de processos. PostgreSQL 17 em CI (major já usado no laboratório), nenhuma dependência PostgreSQL instalada no PC do usuário. SQL versionado é independente de Node/Python/Deno/HTTP. O broker cloud de chamadas curtas será integrado em subentrega posterior; não ligar o probe mTLS de laboratório a jobs por mera reutilização.

## Entidades e contrato interno

Schema privado `rc_control`. `settings` guarda gate OFF/capacidade/lease/limite de tentativas; `workers` guarda identidade sintética, escopo, ativo; `jobs` guarda chave idempotente por owner, descriptor imutável admitido, escopo, deadline, estado, geração e tentativa corrente; `attempts` guarda a história por job/geração/worker. Não guardar código-fonte ou credenciais. Descriptor contém apenas version_id, hashes de fonte/programa/política, engine_ref fixo e rounds 1..3. Chamador é um serviço confiável que já passou por I1, não navegador/worker nem endpoint público.

Funções SQL: enqueue, claim, start/heartbeat, fail_attempt, cancel e reap. Reserva usa FOR UPDATE SKIP LOCKED. IDs de job/attempt gerados pelo banco. Chave repetida com mesmos dados devolve o mesmo job, mesmo com fila cheia; payload diferente conflita. Capacidade é contada e reservada sob trava de settings. Clock do banco, deadline máximo 240 s e lease curta limitada por deadline; configuração experimental não é quota de produção.

Uma lease expirada não pode ser renovada ou usada. Reap terminaliza a tentativa e reencaminha o job se ainda houver tempo/tentativas; senão FAILED/EXPIRED. A próxima reserva incrementa fencing. CANCELLED é idempotente e não volta à fila. Worker revogado não recebe/renova reserva. Suspensão bloqueia novas admissões/reservas, permitindo cancelar/recolher. Só I3-04 poderá criar COMPLETED/score; esta migration deliberadamente não inclui publicação de resultados.

## Plano executável e aceites

- [ ] PG-01 [US1/US5] Reconciliar ADR-005/#23/#24, publicar D-007/ADR-006, este plano e contrato antes da migration.
- [ ] PG-02 [US1/US4] Criar migration privada em `services/execution_control/postgres/001_control.sql`: roles NOLOGIN sem superuser, schema privado, RLS, grants por função e gate OFF. Colisão/migration já aplicada não deve apagar ou substituir tabelas silenciosamente.
- [ ] PG-03 [US3] Implementar funções atômicas de enfileiramento/reserva, relógio de banco, timeout, tentativas/fencing, start/heartbeat, falha/retry limitado, cancelamento e recolhimento. SQL sem chamadas a Docker ou rede.
- [ ] PG-04 [US1/US3/US4] Integração em PostgreSQL REAL no CI: concorrência de reservas, idempotência sob repetição/capacidade, scopes/worker revogado, token/attempt antigo negados, deadline/lease vencida, cancelamento concorrente, rollback e restart do processo do banco. Usar psql por stdin com processos/volumes owned no runner; não tratar fixture SQLite como prova.
- [ ] PG-05 [US1/US4] Provas de acesso: anon/authenticated/worker sem tabelas/funções; rc_broker somente funções, sem DML direto nem capacidade de habilitar gate; RLS continua negando mesmo se for acrescentado grant de SELECT numa fixture. Não confundir isso com RLS da futura aplicação de alunos.
- [ ] PG-06 [US5] Registrar evidência JSON sanitizada por teste, versão real PostgreSQL, fonte/checkout/run, hashes da migration e cleanup; executar Spec Kit e regressões I1/I2/I3/autoria. Reportar falhas antes de corrigir, adendo antes de escopo novo.

## Procedimento de teste e autorização

Workflow próprio GitHub-hosted Ubuntu. Contêiner postgres:17-alpine só no runner, `--network none`, sem portas publicadas e volume nomeado/rotulado owned. Python stdlib invoca psql por docker exec, sem driver/DB remoto; identidade do contêiner conferida antes de uso. O arquivo SQL chega via stdin, sem binds de host. Recursos finitos e cleanup exclusivo em always, inclusive volume. Teste de restart usa o mesmo volume do CI, não tmpfs (que perderia dados). Senha apenas sintética/efêmera; não exportar banco ou credenciais. Sem execução local do harness fora de GitHub-hosted.

## Gate e próxima etapa

PG-01..06 só fecham com provas, nunca por contagem de testes/arquivo gerado. O núcleo transacional testado não fecha **I3-03 integral**: faltam ligação com admissão/autenticação do broker cloud, claim outbound pela VM, bootstrap/revogação operacional e teste fim a fim. Depois vêm I3-04 ledger/Storage, I3-05 quotas/polling, I3-06 recovery ampliado, I3-07 integração, I4 VM, I5 backup e go/no-go. Apresentação à diretoria permanece NO-GO enquanto não houver jornada demonstrável e ensaiada; não habilitar alunos com este código.

Rollback desta rodada: não mesclar/reverter somente o commit da branch. Não rodar DROP SCHEMA/roles em banco real. PostgreSQL de CI é novo/descartável; migration existente ou conflito falha fechado. PR permanecerá draft, sem merge automático nesta rodada.
