# I3 — Decisões do desenho experimental e decisões pendentes

**Data:** 2026-10-10. **Status:** decisões de implementação G-EXP, não ratificação G-PROD. Planejamento anterior ao código: [iteration-3.md](iteration-3.md). A arquitetura completa do worker/VM não foi instalada nem autenticada.

| ID | Questão e decisão limitada | Estado |
|---|---|---|
| I3-D01 | Decompor I3 em etapas com gates; iniciar apenas persistência e broker interno sem consumidores ou rede; `services/execution_control` é pacote Python, não diretório com hífen do rascunho macro. | DECIDIDO_G_EXP |
| I3-D02 | SQLite em **arquivo temporário do CI** como protótipo de transações de fila; `BEGIN IMMEDIATE`, `foreign_keys=ON`, `busy_timeout`, constraints e únicos. Sem alegar equivalência a Postgres em escala ou multiworker. | DECIDIDO_G_EXP |
| I3-D03 | `owner_ref` só é parâmetro de componente interno confiável; **não** vem de JSON/browser. Nenhum mecanismo de autenticação pronto. Tentativas remotas de enfileirar ou reclamar jobs ficam fora do incremento. | DECIDIDO_G_EXP |
| I3-D04 | Gate desligado por padrão e exigência explícita de simulação de worker pronto em teste; em qualquer outra configuração negar antes de escrever. Simulação nunca pode virar alegação de worker autenticado. | DECIDIDO_G_EXP |
| I3-D05 | Idempotência transacional escopada por dono sintético + chave; payload diferente com mesma chave = conflito. `job_id` e `attempt_id` exclusivos globalmente; dados brutos da DSL não são persistidos. | DECIDIDO_G_EXP |
| I3-D06 | Leases/retries, resultado assinado pelo canal, recuperação e exatamente-uma-vez ficam para I3-03/I3-04; não transicionar `QUEUED` a `RUNNING` neste recorte. | DECIDIDO_G_EXP |
| I3-D07 | Identidade mútua broker↔worker, provisionamento, rotação, revogação e autorização por papel/objeto devem ser definidos e testados antes de uma interface real. mTLS pode ser avaliado; não construir criptografia própria nem usar simples `owner_ref` como prova. | ABERTO_Q07 |
| I3-D08 | Destino final dos registros de jobs na solução com PostgreSQL e separação de credenciais depende de migração e testes contra banco de CI isolado, nunca do Compose pessoal. | ABERTO_G_PROD |
| I3-D09 | Sem endpoints públicos, VM pessoal ou execução de estudante; isolamento I1/I2 continua experimental. | BLOQUEIO_MANTIDO |

## Contrato transitório I3-01 — persistência interna

A função de admissão I1 validará o envelope (incluindo `source_sha256`), fonte e registro de versão. A nova camada de controle receberá somente o descritor imutável e `owner_ref` pseudoaleatório do ator confiável interno. O protótipo grava `job_id`, `attempt_id`, `version_id`, hash do programa/fonte, versão do motor, digest de política, chave de idempotência, deadline UTC e status `QUEUED`. Nenhuma linha de código de usuário, token, Docker flag ou certificado é gravado.

Concorrência de escritores deve bloquear até obter lock ou falhar fechado; não retornar sucesso caso a transação falhe. Quota de fila é global e apenas para laboratório. Mesma chave e conteúdo vinculante devolve o mesmo job sem nova escrita; divergência recusa, incluindo diferença de versão/ID/deadline/fonte. Falha atômica não deixa registro parcial. Em I3-01 não existe claim nem ack, portanto **nenhuma pontuação**.

Erros devem ser estáveis e sem interpolação de conteúdo. O isolamento de canais ainda será avaliado em I3-02. Como a aplicação atual ainda não tem identidade da API, nenhum componente público deve instanciar o broker com gate de laboratório habilitado.

## Critério para alteração dessas decisões

Mudanças nos estados, armazenamento, formato de fingerprint e autorização exigem registrar ADR/adendo, teste de regressão e evidências antes de tocar a interface real. Q-07 continua formalmente aberta: as decisões de experimentação acima não a resolvem para produção.
