# I2 — Decisão de reconciliação e adendo de implementação

**Data:** 2026-10-10. **Plano anterior:** `4bb7a5b85dcbf86b667dde07500476d40e510d8e`, [i2-reconciliation-plan.md](i2-reconciliation-plan.md). Este adendo antecede patches de runtime/testes.

## R01/R02 — Inventário e decisão

Fontes congeladas dos PRs #19 (`3f1b495`), #21 (`583fe58`) e #18 (`e94ac97`) foram exportadas pelo run `38058103430`, artifact `11672039425`, ZIP SHA-256 `d3ce75dd22a43093699705b3996cd4ed370ef6822c94644a8c13cdb9d0c10018`. CRC e TODOS os blobs foram conferidos contra `git ls-tree`: respectivamente 226, 208 e 217 arquivos. A comparação inclui código, testes, cenários de limpeza, protocolos, planos e evidências, não apenas descrições dos PRs.

**Decisão:** manter PR #19 / `feat/s04-i2-separated-arena` como única base executável do I2, incorporando critérios/testes úteis das alternativas. Não combinar topologias nem instalar três gateways. A quantidade de testes não é o fundamento da decisão.

| Aspecto | #19 | #21 | #18 | Decisão verificável |
|---|---|---|---|---|
| Fronteira | árbitro/controlador/gateway confiáveis; cada bot em namespace separado | árbitro, controlador e gateway em contêineres confiáveis distintos | gate Java, árbitro e redes por bot | #19 já satisfaz a separação bot/árbitro; separar processos igualmente confiáveis não substitui os controles faltantes |
| Rede efetiva | bridge internal owned + INPUT/OUTPUT/FORWARD deny nos namespaces, IPv4/IPv6, IP bruto, host/peer canários, DNS e contadores | redes game/trusted + gateway dual-homed, prova DNS/IP direto | redes isolated e políticas por papel | preservar #19 e testes de anexação exata; não enfraquecer ACLs por mera segregação de bridges |
| BotHandshake | token efêmero, sessão real, nome/versão, identidade única; reescreve segredo upstream | checagem de tipo/nome/versão; credencial encaminhada ao engine | filtro e identidade cruzada | preservar #19; ampliar negativos de transporte e reconexão |
| Pós-handshake | campos/tipos/valores de BotReady/BotIntent; JSON sem chaves repetidas; TeamMessage negado | filtro de tipo incluindo TeamMessage, sem schema detalhado do intent | filtro Java | preservar lista menor do #19; TeamMessage não pertence ao recorte básico e não será portado |
| Recursos de canal | mensagens/bytes de entrada/saída, inatividade/vida, conexões/filas | conexão e tamanho/filas | tamanho/contratos Java | preservar #19; testar esgotamento, liberação de identidade e encerramento determinístico |
| Evidências | auditor somente leitura, esquema/rounds/identidades/hashes/flags | validação de eventos menos estrita | validação própria | preservar #19 e fortalecer vínculo explícito fonte/run/imagens/arquivos e unicidade das execuções |
| Falhas e cleanup | dois abortos parciais, imagens/daemon, duas batalhas | cleanup do caso normal | cenário adicional deadline-cleanup com TIMEOUT real | portar o ACEITE do timeout para a arquitetura #19, não seu executor concorrente |
| Dependência | websockets 15.0.1 por URL/hash | websockets 16.0 por lock | Java | preservar dependência fixada #19; testes locais com 16.0 são compatibilidade suplementar, CI usa versão fixada |

As 13 funções de teste de #21 têm equivalentes em `test_arena_protocol.py`, `test_arena_policy.py`, `test_arena_evidence.py`, `test_arena_manifest.py` e `tests/arena/test_gateway.py`; os casos de comandos de controle, roster duplicado/endereço e limites explícitos serão complementados onde necessário. O teste que admite TeamMessage será conscientemente rejeitado, não marcado como regressão. De #18 preservar deadline/cleanup, reconexão, identidade cruzada e tamanho; seleção manual de sub-rede não será copiada para a topologia com alocação pelo Docker e ACL por IP inspecionado.

Baseline #19 reexecutada fora do CI: 41 planejamento + 13 infra + 23 motor + 35 autoria + 164 segurança + 11 transportes com engine FALSO = 287 testes aprovados. Python local com websockets 16.0; não é nova batalha nem validação Docker. Artifact histórico #19 `11669245424` teve hash/CRC confirmados; relatórios históricos não serão reescritos.

## Achados e correções planejadas ANTES do código

### C01 — Aceite de timeout/cleanup de #18 ausente na base escolhida (médio, bloqueia I2)

Adicionar cenário fixo `timeout-cleanup` em `run_separated_arena.py`: após controles/árbitro prontos, fixture Python conhecida no bot escreve canário de início e espera cinco segundos; deadline externo de 0,5 segundo deve levantar especificamente `ProcessBoundError(TIMEOUT)`. Conferir canário antes de aceitar a observação. Falha genérica, fixture não iniciada ou retorno normal NÃO é aprovação. Sem batalha nesse cenário; limpeza owned de todos os contêineres/redes e tags e inventário vazio obrigatórios. Manter os dois abortos e as duas batalhas anteriores. Cobrir oráculo em testes puros e executar caso real no CI.

### C02 — Vínculo de evidências insuficiente para encerrar a reconciliação (alto documental/integridade, bloqueia I2)

O auditor histórico não exige `project_commit`, imagens, unicidade de run IDs nem um índice de hash de todos os relatórios, e aceita campos de escopo ausentes em abortos. Adicionar contrato de reconciliação estrito, separado da leitura retrocompatível dos lotes históricos: `reconciliation.json` com source SHA, checkout SHA, workflow run/attempt, imagens por papel, todos os hashes de arquivos e IDs distintos das cinco invocações. Conferir fonte esperada com head do PR no workflow, não apenas SHA autoafirmado; comparar imagem de cada papel nos relatórios. Abortos/timeout exigem schema/flags falsos e ausência de resultados de batalha. Negativos para campos ausentes, bool no lugar de inteiro, digest/run duplicado/mismatch e arquivo adulterado. O contrato NÃO autentica árbitro comprometido nem equivale a atestado criptográfico. Workflow de aceite usará obrigatoriamente o contrato novo; histórico continua legível sem receber aceite de reconciliação.

### C03 — Contrato e ciclo de vida do gateway merecem fechamento explícito (médio, bloqueia I2)

Normalizar falhas de JSON profundo/int excessivo/float infinito em código estável sem refletir entrada. Validar saudação upstream (tipo, versão 1.4.0, sessão válida) antes de enviá-la. Encerrar gateway impedindo novas admissões, fechando sockets e aguardando drenagem limitada; falha de drenagem bloqueia o experimento. Testar todos os tipos de controle antes/depois, binário/excesso/duplicidade/campos, capacidade, vida máxima, reconexão/identidade liberada, fechamento ativo e falha upstream. Preservar limites, segredo reescrito e tráfego legítimo; não implementar serviço público ou rate-limit multiusuário I3.

### C04 — Roster/setup e verificação de bots (médio, bloqueia I2)

Portar o rigor do roster de #21: duas identidades oficiais únicas, versões exatas, hosts IPv4 e portas válidas/distintas; setup clássico com máximo explícito de dois participantes. Conferir futures de bots sem descartar erros de limite/saída prematura antes do resultado oficial. Um bot oficial que permanece conectado após GameEnded deve ser encerrado de forma controlada pelo experimento; não tratar a permanência normal do SDK como falha. Testes de fixtures e batalha real definirão o comportamento observado antes de qualquer aceite.

### C05 — Estado/rastreabilidade/PRs concorrentes (médio, bloqueia I2)

Atualizar os pontos canônicos existentes e um registro estruturado de achados/critério/resultado. Preservar S04-T04 EM_EXECUCAO e os 39 itens amplos/18 gates de produção. Registrar recorte de cada pendência I3/I4/I5 SEM transferir C01–C04. Após CI/artefatos aprovados, encerrar #18 e #21 como superados (branches/commits preservados), atualizar #19 e impedir novas baselines divergentes. Remover coletor temporário. Registrar autoria da auditoria corretamente: conferência própria fora do runner não é revisão independente por terceiro.

## Verificação e fontes primárias

Toda correção precisa de teste que falhe sem a proteção e passe com ela, além das regressões do I1/editor/motor/Spec Kit e duas batalhas reais, dois abortos e um timeout real. Resultado final documentará fonte, versão, ambiente, comandos, runs, artifacts e limitações. I3 permanece NÃO INICIADO nesta rodada.

Fontes consultadas para conferir semântica, sem adotar APIs de versões diferentes: https://docs.docker.com/engine/network/ ; https://docs.docker.com/engine/network/drivers/bridge/ ; https://websockets.readthedocs.io/en/15.0.1/reference/sync/server.html ; código upstream fixado citado em `i2-protocol-guard.md`. Bridge interna sozinha não significa inacessibilidade do host/pares; a implementação escolhida conserva ACLs e provas efetivas.

## R03–R10 — Resultado e encerramento de achados (2026-10-10)

| Achado | Correção e prova | Estado do recorte |
|---|---|---|
| C01 timeout/cleanup de #18 | Fixture iniciada, deadline externo real de 0,5s, motivo TIMEOUT específico e limpeza owned; negativos impedem aprovação por erro genérico | FECHADO |
| C02 integridade/vínculo | Perfil `I2_RECONCILED_CI_V1`, hashes de 12 arquivos, fonte `e7afd8a2ac7cb1ab45eeec2146ae828e56f93e0a`, run 38059207968, imagens e cinco IDs únicos; análise reproduzida fora do runner | FECHADO |
| C03 protocolo/ciclo de vida | Mensagens administrativas/inesperadas negadas antes e depois do handshake, limites cumulativos, validação upstream, drenagem e negativas em testes; partida legítima passou | FECHADO |
| C04 roster/bots | Nomes e versões oficiais, pares endereço/porta, futures e terminação controlada de bots preservados; duas partidas reais passaram | FECHADO |
| C05 rastreabilidade/alternativas | #18 e #21 fechados como superados sem merge, #19 canônico; plano, iteração, estado e evidências vinculados; coletor temporário retirado | FECHADO |

**R10:** zero achados I2 pendentes no escopo delimitado. Ver [relatório de reconciliação](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md). A verificação própria fora do runner não constitui auditoria externa independente, nem valida segurança de código de estudantes, VM real, filas, quotas operacionais, recuperação durável ou liberação ao público.
