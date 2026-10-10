# D-003 — Preparação documental antecipada do isolamento S04-T04

**Data:** 2026-10-09 · **Natureza:** registro de autorização de planejamento, **não** decisão arquitetural aprovada.

## Solicitação e motivo

O responsável pediu que a tarefa de segurança e isolamento fosse **planejada primeiro usando o Spec Kit**, conforme recomendação após os testes locais de Sentinela e Explorador. Isso autoriza produzir `spec.md`, esclarecimentos, pesquisa, arquitetura candidata, `plan.md`, tarefas, checklists e análise de consistência **sem executar a sandbox e sem alterar o computador pessoal**.

## Exceção de sequência e limites

O backlog macro contém S04-T04 após S04-T02 e T03. Embora o motor real e o editor tenham sido exercitados, S04-T02 segue em revisão formal e S04-T03 ainda aguarda celular físico/ratificação. S00-T06 e a baseline S03 também estão pendentes. **Somente a preparação de documentos e validação estática é permitida em paralelo**, sem encerrar S04-T04 ou registrar testes de ataque fictícios.

## Pendências de aprovação

- D1: escopo de RoboDSL como única autoria T1 inicial e exclusão de código geral T2.
- D2: fronteira de execução (VM Linux dedicada versus worker externo).
- D3: separação bot/árbitro e canal WebSocket.
- D4: quotas, testes de abuso, política de dados e rollback.
- D5: gates de publicação de alunos e operação.

A constituição não foi ratificada por esta decisão. A arquitetura candidata ADR-004 e as tarefas de implementação permanecerão em rascunho até aceite e evidências.

## Rastreabilidade

[Feature 004](../../../specs/004-isolamento-execucao/spec.md) · [Ameaças](../../arquitetura/ameacas-sandbox.md) · [ADR-004](../../arquitetura/ADR-004-isolamento-execucao.md) · S04-T04 em `docs/planejamento/backlog.json`.

Nenhuma máquina/VM foi acessada ou configurada nesta decisão.
