# I2 — revisão, consolidação e endurecimento do incremento

**Data:** 2026-10-10. **Base revisada:** PR #19, head 0044c5b13cdf835d55821597f041b5ef204e305d. **Status:** PLANEJADO antes das mudanças abaixo. Vínculo: iteration-2.md (I2-01..I2-09), i2-protocol-guard.md (N5), feature 004 / S04-T04. G-EXP continua autorizado; G-PROD bloqueado.

## Consolidação

Na revisão completa foram encontrados rascunhos I2 em #18 e #19. #19 já contém implementação e artifact de CI no run 38027947992. Este código será reaproveitado, não substituído por terceira implementação. O rascunho #20 criado nesta rodada continha apenas plano/coleta de fonte e foi encerrado sem merge; branches e #18 preservados. A direção efetivamente testada em #19 é bridge internal com ACLs nos namespaces próprios dos contêineres, e não a hipótese gateway isolated descrita em #20.

## Achados concretos e tarefas necessárias (planejadas primeiro)

| ID | Lacuna observada / mudança requerida | Critério verificável | Vínculo |
|---|---|---|---|
| I2-H01 | Validação existente confere round/nomes/score mas não todos os tipos, sequência de eventos ou flags obrigatórias do manifesto. Criar validador de evidência estrito, separado do supervisor Docker, e CLI de auditoria somente leitura. | Fixtures com bool no lugar de número, rank inválido, evento fora de ordem, campo ausente, flag falsa/truthy, digest divergente, symlink ou arquivo excessivo são rejeitados; artifact real passa. | I2-07/09; T029/T031; FR-011/012/014 |
| I2-H02 | Política precisa conferir também redes efetivamente anexadas, não apenas HostConfig.NetworkMode. Conferir namespace distinto do host, rede interna/owned e conjunto permitido de endpoints. | Mutações de rede extra, IPv6 inesperado ou estado de contêiner não owned são bloqueadas. Testar com fixtures e inspecionar runtime. | I2-02/04/06; T019/T022; FR-005/006/007/018 |
| I2-H03 | Gateway limita tamanho de frame e conexões, mas não orçamento acumulado/tempo de sessão por cliente. Limitar mensagens, bytes cumulativos, inatividade e vida útil no perfil experimental. | Validar limites nos testes puros e no transporte WebSocket com engine falso; fluxo do motor real preservado. Não é rate-limit de produção/I3. | I2-05/06; T023/T024; FR-008/009/017 |
| I2-H04 | Cleanup de sucesso já passou, mas falha parcial de build/provisionamento não tem prova suficiente. Registrar manifesto de lote e duas falhas sintéticas antes/depois de o árbitro iniciar; garantir liberação de recursos por ownership e registrar falha de cleanup sem falso PASS. | Duas batalhas normais e abortos deliberados after_containers/after_ready deixam zero containers/networks owned; tags temporárias removidas. Nenhum comando global de limpeza. | I2-03/04/08; T025/T026; FR-009/010/019 |
| I2-H05 | Negativos dinâmicos atuais partem de apenas um bot. Repetir em ambos os namespaces, com canários positivos reais e contagem efetiva de rejeições. | Cada bot acessa somente porta 7654; host sintético/peer/porta bruta7655/DNS/IPv6 são negados; nenhum scan real de LAN. Resultados por papel presentes no manifesto. | I2-06; T019/T021/T022; FR-006/018 |
| I2-H06 | Planejamento/estado/PR ainda dizem implementação inicial mesmo com CI anterior concluído. Auditar fontes, artefatos e licenças, repetir CI após correções e registrar resultado sem exagerar alcance. | Fonte/commit/run/hash, placares, rounds, controles, abortos/cleanup e limitações registrados; I2 técnico pode concluir apenas após prova, tarefas macro/gates públicos continuam abertas. | I2-01/09; T036/T037/T039; FR-015/018/020 |

## Escopo conservado

Três rounds por batalha e duas batalhas com Walls/Spin Bot oficiais, não cinco rounds de outro rascunho. Protocolo continua limitado a BotHandshake, BotReady e BotIntent; identidade/token/estado conferidos. N5 documentou antes do gateway o achado no servidor fixado 1.4.0: handshake não bastava para todos os comandos posteriores. Conferir novamente a fonte e a prova benigna em ambiente owned; não anunciar CVE nem generalizar a outras versões.

As ACLs são aplicadas por supervisor confiável com nsenter somente em namespace de container owned, cujo inode difere do host; o código do bot nunca recebe NET_ADMIN. Não há mudança manual de regras do host; regras de bridge geridas pelo próprio Docker existem apenas no runner descartável. O processo da API final não terá esses privilégios.

## Ordem e arquivos

H01/H02/H03: testes negativos antes das correções. H04/H05 após revisão das fronteiras. H06 após baixar e auditar CI real. Caminhos previstos: services/worker_agent/arena_evidence.py, arena_policy.py, arena_protocol.py; scripts/verify_arena_evidence.py e run_separated_arena.py; spikes/isolamento/arena/gateway.py/role.py/NOTICE.md; tests/security/test_arena_evidence.py e testes correlatos; tests/arena/test_gateway.py; .github/workflows/separated-arena.yml; docs/qualidade/evidencias/S04-T04-I2.*.

A revisão de evidências é inspeção de bytes/contratos, não autenticação criptográfica do árbitro nem prova de inexistência de escape. Quotas são de experimento. Nenhuma VM pessoal, firewall doméstico, .env, Compose, VHDX, código de aluno ou gate de produção será alterado. Novas lacunas fora desta lista requerem outro adendo antes do código.
