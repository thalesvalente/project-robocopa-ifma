# I3-03 / C02 — Limpeza: erro de consulta não é ausência de recurso

**Data:** 2026-10-10. Revisão de PG-06 após 30 testes PostgreSQL PASS no run 38074280822. Documento publicado antes do patch.

## Achado

O workflow consulta recursos antes de removê-los com atribuições shell que preservam o exit code. Entretanto, a confirmação final usa `test -z "$(docker ... )"`: uma falha no Docker dentro dessa substituição pode resultar em texto vazio, fazendo o teste de string passar. Não foi observada essa falha de daemon no lote aprovado; é uma lacuna estática de tratamento de erro, não evidência de vazamento real.

## Correção e regressão planejadas

Separar as consultas finais em atribuições executadas sob `set -euo pipefail`; só testar string vazia após sucesso das consultas. Nenhuma evidência pode receber cleanup=VERIFIED quando uma consulta ao daemon falhar. Preservar ownership de contêiner/volume e proibição de prune global.

Adicionar três testes do trecho shell real do workflow, em ambiente temporário com função Docker falsa: ausência confirmada retorna sucesso; falha ao consultar contêineres retorna erro e não grava a confirmação; falha ao consultar volumes faz o mesmo. Esses testes são explicitamente simulações de falha, não testes Docker reais. O CI PostgreSQL continua demonstrando limpeza verdadeira no runner. Reexecutar ambos e as regressões antes de fechar PG-06.
