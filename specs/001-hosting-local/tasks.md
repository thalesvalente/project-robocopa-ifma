# Tarefas técnicas — Feature 001

**Situação inicial:** execução preparatória. Atualizar os checkboxes de acordo com evidências reais. Nenhuma tarefa deste arquivo substitui o backlog canônico.

- [x] INF-001 [US1] Registrar topologia candidata e ADRs sem homologar arquitetura. Referência: S04-T01/S04-T05; documentos em `docs/arquitetura/`.
- [x] INF-002 [US1] Criar Compose de banco e sonda com nome exclusivo, redes internas e porta de loopback. Referência: S04-T05; arquivo `compose.local.yaml`.
- [x] INF-003 [US1] Criar script idempotente por recusa de sobrescrita para credencial local. Referência: S04-T05.
- [x] INF-004 [US2] Declarar volume e healthcheck PostgreSQL com limites; não realizar migração de dados do host. Referência: S04-T05.
- [x] INF-005 [US3] Escrever testes de contrato e workflow CI para exercício do Compose. Referência: S04-T05.
- [x] INF-006 [US3] Escrever instruções PowerShell e política de parada sem `down -v`. Referência: S04-T05.
- [x] INF-007 [US1/US2] CI real verificado: 13 testes de infraestrutura OK, Compose config e validador PASS, preflight PASS, serviços saudáveis, HTTP 200/404 e persistência PostgreSQL após recriação. Evidência: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38001273168 e `docs/qualidade/evidencias/INFRA-LOCAL-CI.md`. Executado em GitHub-hosted runner, não no host pessoal.
- [ ] INF-008 [US1/US3] Validar no computador hospedeiro: `docker compose ... up --wait`, health e `ps`. Usuário precisa executar explicitamente.
- [ ] INF-009 [US3] Ratificar a topologia final após os gates S03/S04, backup e avaliações de acesso externo; **não** declarar concluída por uma sonda.

**Nota:** checkboxes INF-001–006 registram apenas elaboração de arquivos. As tarefas macro de S04 exigem especificação aprovada, spikes, execução local e decisão humana antes da conclusão.
