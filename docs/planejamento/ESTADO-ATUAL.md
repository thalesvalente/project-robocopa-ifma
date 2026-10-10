# Estado atual — I3-03C: integração autenticada do worker em preparação

**Data:** 2026-10-10. **Branch:** feat/s04-i3-03-postgres-leases, PR #26. **Macro S04-T04/I3 integral:** EM_EXECUCAO. **Demonstração/G-PROD:** não aprovados.

## Prioridade e reconciliação

D-012/PR #31 restabeleceu I3-03 antes de I3-04. Multiescola e Google OAuth de estudantes ficam no piloto; D-011 de permitir Google acadêmico OU Gmail pessoal continua válida. O classificador ID-010 tem 20 testes sintéticos, não autenticação real. A main até o merge 29b3493 é incorporada à cadeia do PR #26 preservando os avanços I3 e os pais Git de #23/#24. Não integrar esses PRs técnicos à main por consequência desta reconciliação.

MVP: Vercel Hobby preferida no contexto voluntário da D-009, Supabase PostgreSQL/Auth/Storage para dados canônicos, VM Linux dedicada no PC apenas para computação. SQLite é laboratório. Nenhum serviço público, VM ou conta cloud real implantado nesta rodada. Constituição e baseline S03 conservam ratificação pendente; backlog de60tarefas,39tarefas de isolamento e18gates não fechados por CI.

## Recortes já validados e evidências

- I1: contratos e contenção em CI; [evidência](../qualidade/evidencias/S04-T04-I1.md).
- I2: separação árbitro/bots e testes reais de batalha/abortos/timeout; [reconciliação](../qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md).
- I3-01: fila SQLite experimental; [relatório](../qualidade/evidencias/S04-T04-I3-01.md).
- I3-02: mTLS real em loopback CI, não integração cloud; [relatório](../qualidade/evidencias/S04-T04-I3-02.md).
- I3-03/PG: migration001,30 testes PostgreSQL reais; [relatório](../qualidade/evidencias/S04-T04-I3-03.md).
- I3-03B/AD: migration002 e I1 -> Psycopg -> PostgreSQL,22 integrações e25 unidades incluídas nas407 regressões do lote38c6e276; [relatório](../qualidade/evidencias/S04-T04-I3-03B.md). rc_admission é entrada restrita e rc_broker não conserva enqueue bruto.
- ID-010: apenas classificador de identidade sintética; [relatório](../qualidade/evidencias/S03-ID-010.md).

Lotes históricos de CI/host, placares, falhas e hashes permanecem nos respectivos relatórios, sem reclassificação. Ver também [trilha histórica de integração](INTEGRACAO-PRs-2026-10-10.md).

## Implementação seguinte: I3-03C

[Plano CW-01..06](../../specs/004-isolamento-execucao/i3-03c-worker-api-plan.md) e [contrato](../../specs/004-isolamento-execucao/contracts/worker-api.md) publicados ANTES do código. Prova delimitada: Python worker -> HTTPS Deno -> SQL privado, credencial curta por worker/escopo revogável, comandos idempotentes e sem segredos Supabase no worker. Não chamar mTLS de CI de implantação; não usar uma chave administrativa para representar todos os workers.

Faltam runtime/tests do novo recorte, Supabase Edge/pooler/TLS reais, configuração/renovação operacional de credenciais, admissão DEMO cloud, fonte do robô e integração do supervisor. I3-04 resultado/ledger/replay NÃO iniciado. Depois I3-05/06/07, VM I4, PWA/Supabase e ensaio/backup/restauração I5, conforme [trilha DEMO](../../specs/004-isolamento-execucao/demo-diretoria-mvp.md).

**Restrições:** sem Google de aluno, OAuth real, RLS estudantil/multiescola, endpoint público, pagamentos, host Windows/WSL/Docker Desktop, firewall/roteador ou banco pessoal. A autorização do usuário é para implementar/testar o recorte planejado, não para homologar o demonstrador ou pilotar com alunos.
