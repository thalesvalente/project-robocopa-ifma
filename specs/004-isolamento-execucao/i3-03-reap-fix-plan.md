# I3-03 / F02 — Correção da rotina de recolhimento, antes do patch

**Data:** 2026-10-10. Complementa PG-03/04/06 e a auditoria F01.

## Evidência

Depois do reforço de prontidão, o run `38073977886`, fonte `2f6c2e2`, aplicou a migration e executou **29 testes: 25 passaram e quatro retornaram erro ao chamar rc_control.reap()** (expiração de lease, deadline/tentativas e revogação). A falha inicial de setUpClass não voltou nesse lote. Cleanup de contêiner/volume foi confirmado. O lote permanece FAIL, não aprovado.

## Análise e patch planejado

O código usa `reason=reap.reason` para uma variável local declarada no corpo não rotulado. O bloco oculto com nome da função contém parâmetros/variáveis especiais, não essa declaração local. Remover a qualificação incorreta usando uma variável local inequívoca `v_reason`, sem alterar estados, limites, condições de lease ou privilégios. A hipótese de causa é consistente com a estrutura documentada pelo PostgreSQL; a correção só será aceita se os quatro casos reais passarem novamente.

Aprimorar o diagnóstico sanitizado de psql: habilitar VERBOSITY verbose para capturar SQLSTATE, mas retornar SOMENTE código de erro permitido/SQLSTATE e exit code — nunca ecoar SQL, payload ou credenciais. Incluir teste da gravação de reason=LEASE_EXPIRED e da idempotência de reap. Manter os testes existentes, não removê-los nem flexibilizar seus asserts. Após restart do banco, repetir prontidão TCP interna antes da consulta real.

Fonte oficial: https://www.postgresql.org/docs/current/plpgsql-structure.html e https://www.postgresql.org/docs/current/plpgsql-implementation.html . Não mudar plpgsql.variable_conflict globalmente para esconder erro.

**Estado:** correção/testes pendentes. PG-03/04/06 não podem ser encerradas até CI PostgreSQL e regressões aprovados.
