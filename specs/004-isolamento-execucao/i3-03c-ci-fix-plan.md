# I3-03C F01 — correção da fixture SQL antes do patch

**Data:** 2026-10-10. **Run observado:** 38086557984, fonte 84af638d. **Resultado:** FAIL, zero testes de integração; não reinterpretar como sucesso. Deno2.5.6, driver e typecheck instalaram/passaram; 12 testes do handler e 12 do cliente passaram. Banco ficou pronto, mas setUpClass falhou em SHOW server_version com SQLSTATE42601 antes de aplicar migrations. Cleanup de recursos criados foi confirmado.

## Causa e correção planejada

O helper herdado test_control.sql concatena o corpo e COMMIT sem inserir ponto-e-vírgula final; seus testes anteriores fornecem o terminador. A nova fixture I3-03C chamou SHOW sem esse terminador e repete essa omissão em consultas curtas. Criar **wrapper somente na nova fixture** que acrescente terminador se wrap=True; preservar migrations e helper históricos. Acrescentar prova unitária explícita da construção do corpo ou validar todos os call sites sem invocar banco. Não alterar a semântica de produção por defeito do harness.

O relatório emitido durante falha de setUpClass deve diferenciar etapas atingidas: real_https/real_deno não podem vir hardcoded true antes do servidor iniciar; preencher conforme prontidão observada e registrar FAIL/0. Hashes de migrations não são prova de execução. Fixar em deno.lock a resolução obtida do primeiro CI após conferir artifact/versão/integridade, depois exigir resolução congelada.

## Aceite

Reexecutar fixture real Python HTTPS -> Deno -> PostgreSQL; somente contar integração após testes efetivamente executados com sucesso. Conferir versões, fonte/run, contagens e cleanup. Nenhum Supabase, VM, estudante ou I3-04 habilitado. Qualquer próxima falha de runtime será tratada separadamente, com novo adendo antes do patch.
