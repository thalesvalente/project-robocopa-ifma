# I2-08 — Cenários de encerramento e limpeza

**Planejamento anterior à implementação do modo de timeout:** 2026-10-10. Complementa I2-08, sem ampliar o MVP ou autorizar execução no host pessoal.

## Cenário normal

Quatro contêineres, três redes isoladas, controles positivos/negativos e três rounds oficiais. Resultado/replay conferidos; remoção específica de contêineres/redes e tags criados nessa chamada.

## Cenário de timeout controlado

Executar uma **segunda invocação independente** em runner descartável. Após criar/verificar as quatro fronteiras e as provas de rede/protocolo, lançar somente uma fixture Java fixa que aguarda cinco segundos no contêiner do bot. O controlador externo tem deadline de 0,5 segundo. Esperar `ProcessBoundError(TIMEOUT)`, não aceitar exit-code comum como prova de timeout.

O script deve registrar `scenario=deadline-cleanup`, `timeout_observed=true`, `battle_completed=false`, remover os quatro contêineres e as três redes **de sua própria invocação**, e verificar ausência de recursos com seu label. `status=PASS` significa **que o teste de timeout/limpeza passou**, não que uma batalha foi concluída nesse cenário. Qualquer falha de ownership/limpeza torna o teste FAILED.

A fixture não lê arquivos pessoais, não cria novas redes, não esgota CPU/RAM, não acessa serviços externos e não recebe comandos arbitrários. Não realizar vinte ciclos nem simular reinicialização do Windows/VM neste incremento: continuam I5/SC-004 e operação futura.

## Implementação/testes previstos

- `Probe.java`: modo fixo `deadline-fixture`, sem parâmetros de duração/comando enviados por usuário.
- `run_engine_separation.py`: flag explícita `--timeout-cleanup-check`, oracle de timeout e marcação de cenário; guardas de CI continuam obrigatórias.
- Workflow I2: caso normal seguido do caso de timeout em processos separados.
- `tests/security/test_i2_scenarios.py`: modo padrão é batalha; somente exceção TIMEOUT específica permite aprovação do negativo; falhas genéricas não viram PASS.

G-PROD, VM real, fila/ledger e alunos permanecem fora desta prova.
