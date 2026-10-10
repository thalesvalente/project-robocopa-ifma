# Tarefas técnicas — Feature 001

**Situação inicial:** execução preparatória. Atualizar os checkboxes de acordo com evidências reais. Nenhuma tarefa deste arquivo substitui o backlog canônico.

- [x] INF-001 [US1] Registrar topologia candidata e ADRs sem homologar arquitetura. Referência: S04-T01/S04-T05; documentos em `docs/arquitetura/`.
- [x] INF-002 [US1] Criar Compose de banco e sonda com nome exclusivo, redes internas e porta de loopback. Referência: S04-T05; arquivo `compose.local.yaml`.
- [x] INF-003 [US1] Criar script idempotente por recusa de sobrescrita para credencial local. Referência: S04-T05.
- [x] INF-004 [US2] Declarar volume e healthcheck PostgreSQL com limites; não realizar migração de dados do host. Referência: S04-T05.
- [x] INF-005 [US3] Escrever testes de contrato e workflow CI para exercício do Compose. Referência: S04-T05.
- [x] INF-006 [US3] Escrever instruções PowerShell e política de parada sem `down -v`. Referência: S04-T05.
- [x] INF-007 [US1/US2] CI real verificado: 13 testes de infraestrutura OK, Compose config e validador PASS, preflight PASS, serviços saudáveis, HTTP 200/404 e persistência PostgreSQL após recriação. Evidência: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38001273168 e `docs/qualidade/evidencias/INFRA-LOCAL-CI.md`. Executado em GitHub-hosted runner, não no host pessoal.
- [x] INF-008 [US1/US3] Validado pelo responsável no Windows: preflight 6/6 PASS, `docker compose ... up -d --wait` criou redes/volume, PostgreSQL e sonda ficaram `healthy`; `docker compose ps` confirmou só `127.0.0.1:18080` publicado; `/health` retornou `status=ok`. Evidência: `docs/qualidade/evidencias/INFRA-LOCAL-HOST.md`. Não comprova persistência após reinício/backup no host.
- [ ] INF-009 [US3] Ratificar a topologia final após os gates S03/S04, backup e avaliações de acesso externo; **não** declarar concluída por uma sonda.

**Nota:** checkboxes INF-001–006 registram apenas elaboração de arquivos. As tarefas macro de S04 exigem especificação aprovada, spikes, execução local e decisão humana antes da conclusão.

## Subentregas posteriores da Feature 001 — alvo híbrido (2026-10-10)

O experimento INF-001..INF-008 permanece concluído apenas para Compose local; INF-009 continua aberto. A implantação híbrida aprovada quanto à **direção** tem backlog técnico novo [HYB-01..HYB-10](hybrid-mvp.md), com todos os itens ainda **[ ]**. Não marcar infraestrutura pública, hospedagem Vercel, Supabase real, migrations/backup, VM pessoal ou conexão à internet como executadas. O SQLite I3-01 não deve ser promovido a banco principal; adotar PostgreSQL cloud após CI/migrações, e Storage privado para replays.
