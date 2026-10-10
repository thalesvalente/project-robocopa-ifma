# Estado atual — I3-03B: admissão I1 conectada ao PostgreSQL

**Atualizado:** 2026-10-10. **Branch vigente:** `feat/s04-i3-03-postgres-leases`, PR #26. **S04-T04 e I3-03 integral:** EM_EXECUCAO. **G-PROD:** BLOQUEADO. **Demonstração à diretoria:** depende de jornada integrada e ensaio; não está pronta apenas pela CI.

## Decisões vigentes

Somente RoboDSL básica, interface móvel para programar/salvar/testar/participar. Primeiro marco privado com identidades sintéticas e estratégias conhecidas; piloto com estudantes exige outros gates. Níveis intermediário/avançado e streaming contínuo ficam depois.

[D-006](decisoes/D-006-hospedagem-hibrida-e-persistencia-remota.md), [ADR-005](../arquitetura/ADR-005-hospedagem-hibrida-mvp.md) e [D-009](decisoes/D-009-carater-voluntario-vercel-hobby.md): **Vercel Hobby preferida** para a PWA no contexto voluntário/sem remuneração relacionada informado pelo responsável; Cloudflare é contingência, sem carta individual como bloqueio genérico. Conta/quotas/privacidade/representação aplicável ainda precisam de verificação operacional. **Supabase PostgreSQL/Auth/Storage privado** guardam dados definitivos; PC hospeda futuras VMs Linux dedicadas apenas para computação/staging limitado. SQLiteI3-01 e PostgreSQLCompose são laboratório.

[D-007](decisoes/D-007-execucao-pos-revisao-mvp.md)/[ADR-006](../arquitetura/ADR-006-demo-gratuita-plano-controle.md): API curta candidata em Edge Functions, sem motor/worker permanente, polling econômico e status/replay antes de streaming. Uma tabela PostgreSQL canônica para jobs/tentativas após comparar pgmq; resultado com efeito único ainda exige I3-04. Escolha de Python no adaptador de CI não significa que ele execute no Deno/Edge.

## Repositório e integridade do processo

A main de referência após PR #28 é `073c28f0c9e2b1536f11a914fd4e73aa814f3727`, com I1/I2, documentação/arquitetura híbrida e D-009. PRs técnicos #23/#24/#26 permanecem drafts empilhados; nesta rodada continuamos **o PR #26**, sem branch concorrente ou merge. Mudanças de documentos compartilhados anteriores foram preservadas. [Trilha de integração histórica](INTEGRACAO-PRs-2026-10-10.md).

Spec Kit v1.1.2 fixado em `959e866caa3618bf3dc290d5dca33394365af9c6`; scripts e verificador nativo usados, sem alegar slash commands/MCP inexistentes. Backlog JSON canônico de10sprints/60tarefas; 39 tarefas amplas e18 gates sujeitos a aceite integral. Constituição S00-T06, baselineS03 e homologação não ratificadas automaticamente; minutas não são pesquisa de campo.

## Entregas e evidências

| Recorte | Demonstrado | Referência |
|---|---|---|
| Compose/Tank Royale/autoria | CI e reproduções limitadas informadas no PC; telefone físico/revisão pedagógica pendentes | [Infra host](../qualidade/evidencias/INFRA-LOCAL-HOST.md), [motor](../qualidade/evidencias/TANK-ROYALE-HOST.md), [autoria](../qualidade/evidencias/AUTORIA-MOBILE-HOST.md) |
| I1 | Contratos/limites/sondas emCI, sem VM pessoal | [I1](../qualidade/evidencias/S04-T04-I1.md) |
| I2 | Arena separada, gateway, auditoria, batalhas/abortos/timeout e reconciliação | [ReconciliaçãoI2](../qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md) |
| I3-01 | SQLite/broker interno OFF de laboratório | [I3-01](../qualidade/evidencias/S04-T04-I3-01.md) |
| I3-02 | Probe TLS1.3 mútuo real em loopbackCI; não autenticação cloud de jobs | [I3-02](../qualidade/evidencias/S04-T04-I3-02.md) |
| I3-03 / PG | Migration001,30 testes PostgreSQL reais: jobs/leases/fencing/retry/reap/privilégios/restart | [NúcleoPG](../qualidade/evidencias/S04-T04-I3-03.md) |
| **I3-03B / AD** | Migration002; catálogo autorizado/hash/revisão; I1 -> Psycopg -> PostgreSQL -> fila;22 integrações reais e25 unidades novas | [PlanoAD](../../specs/004-isolamento-execucao/i3-03-admission-plan.md), [evidências](../qualidade/evidencias/S04-T04-I3-03B.md) |

**Fonte do novo lote:** `4179e5b6a001a5ed6471caa5d9f70d1d2f5df15c`, sete workflows completed/success, incluindo driver/banco real, núcleoPG original, I1/I2/autoria e SpecKit. **22 integrações** PostgreSQL17.11/Psycopg3.3.6, **407 regressões locais**, já incluindo os25 testes unitários novos. Artefato de admissão11679761808 (563bytes) conferido por hash/CRC/fonte/run, counts e cleanup=VERIFIED. Runtime local da fonte7e8f014 é idêntico ao do4179e5; diferenças somente emworkflow/adendo. Ver relatório para detalhes; conferência própria, não auditoria independente.

O primeiro workflow novo foi rejeitado antes dos jobs por runner.temp em jobs.env. [Plano corretivo](../../specs/004-isolamento-execucao/i3-03-admission-ci-fix.md) precedeu patch; execução posterior válida passou. Falha não foi reclassificada comoPASS. A CI final documental é registrada separadamente no PR, não altera o lote versionado.

## Contrato atual e limites

Depois da **migration002**, `rc_admission` só consulta versões autorizadas/enfileira; `rc_broker` perde EXECUTE no enqueue bruto, mas conserva claim/heartbeat/cancelamento/recuperação. [ContratoSQL](../../specs/004-isolamento-execucao/contracts/postgres-control.md). O serviço reconfere owner/escopo/revisão/hash/política depois de compilar, e só responde sucesso após commit. Hashes de versão são imutáveis; fonte/PII não entram no catálogo de controle.

`ServiceActor` é contexto interno confiável, **não JWT**. LoginSCRAM testado é autenticação do banco, **não usuário ou worker por HTTPS**. Revogação de versão bloqueia nova admissão, **não cancela automaticamente jobs já aceitos**; definir essa política no ciclo de vida operacional. Credenciais de serviço não vão à VM/bot/browser. Não tratar adaptadorPython como APIEdge já implantada.

## Próxima fronteira elegível, a planejar antes de implementar

I3-03 integral ainda precisa: API cloud/autenticação real de usuário e identidade do worker, catálogo de autoria/RLS por dono, cliente compatível com runtime de deploy, roles/pooler/TLS Supabase e conexão outbound do worker. Antes desse código, registrar o contrato concreto e testes; não repetir os experimentos existentes como se fossem novas camadas necessárias.

Depois: I3-04 resultado/replay e efeito único; I3-05/06/07 quotas/polling/recovery/integração; I4 provisionar/testar VM por procedimento autorizado; I5 vinte ciclos, backup de banco **e objetos**, restauração/revisão/ensaio. [HYB-01..10](../../specs/001-hosting-local/hybrid-mvp.md) permanece com aceites próprios. Auth/SMTP, privacidade/consentimento, dados de menores e disponibilidade/custos precisam de comprovação.

## Restrições

Nenhum deployVercel/Supabase/Cloudflare, serviço pago, dado real, aluno, VM pessoal ou main foi alterado nesta rodada. Não mexer emWindows/WSL/DockerDesktop/.env/Compose/banco/roteador/firewall/discos pessoais. O laboratório18081 com acesso à CLI Docker não deve ser exposto. Aprovação de recorte do CI não homologa esse servidor ou G-PROD.
