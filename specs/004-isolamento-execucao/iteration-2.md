# S04-T04 — Incremento I2: árbitro e bots separados

**Data:** 2026-10-10. **Base:** I1, commit `668d82b034cf5e0fab909e13552399c2de7213d5`. **Plano original publicado antes do código:** `c24f34f8b9c17e169efa55bceb7501fe4486fd73`. **Estado atual:** implementação e prova técnica do recorte no CI concluídas; G-PROD e VM pessoal continuam pendentes.

Continuação autorizada pelo responsável: implementar tarefas planejadas e registrar novas necessidades primeiro. G-EXP permanece autorizado em GitHub-hosted efêmero. Nenhuma alteração no Windows, instalação de VM ou exposição para alunos.

## Objetivo e limite

Realizar duas batalhas reais com Tank Royale 1.4.0: árbitro/controlador em um contêiner; cada bot oficial conhecido em seu contêiner, com filesystem, PIDs e namespace de rede distintos. Não usar BattleRunner.externalServer como falsa externalização dos bots: controlar explicitamente o protocolo WebSocket oficial e iniciar JVMs somente nos contêineres dos bots. Usar Walls e Spin Bot fixados; não adicionar linguagem nem receber código de estudantes.

## Necessidades identificadas e planejadas antes do código

**N1 — Transporte independente do booter:** cliente controlador/observador usando o protocolo oficial e dependência WebSocket fixada com hash. Server JAR extraído do runner.jar previamente verificado. Não implementar física ou pontuação própria.

**N2 — Rede com comunicação permitida:** network=none não permite bots em namespaces distintos. Bridge Docker internal exclusiva, com regras INPUT/OUTPUT/FORWARD nos namespaces de cada contêiner antes das JVMs. O supervisor confiável usa nsenter apenas em PID/namespace confirmado por ID, label e inode distinto do host. Não instalar ACL manual no namespace do host; Docker administra as regras de sua bridge no runner. Bot permanece sem NET_ADMIN/NET_RAW, host mounts, socket, dispositivos ou portas publicadas. Destino permitido: IP numérico do árbitro e porta de jogo. IPv6/DNS/gateway/pares negados; falha de política aborta a batalha, sem fallback.

**N3 — Papéis e segredos:** segredo administrativo de Controller/Observer distinto dos tokens efêmeros dos bots. Observer e Controller compartilham a classe de segredo segundo o upstream, não três chaves independentes. Credenciais entram por stdin e não são gravadas em imagens ou artefatos. Validar identidade, handshake inválido e tentativa de comando administrativo na conexão do bot. Não é autenticação multiusuário.

**N4 — Evidência e subprocesso:** stdin pequeno e limitado sem bloquear watchdog; saída/tempo limitados durante leitura; resultado e replay originados no árbitro. Nenhum segredo em logs/erros. Limpeza exclusiva por execução.

**N5 — Filtro por mensagem:** [i2-protocol-guard.md](i2-protocol-guard.md) foi publicado antes do gateway após revisão do upstream. A checagem de segredo no handshake não demonstrava autorização de todos os comandos posteriores. A prova benigna e a mitigação estão registradas abaixo.

**H01–H06 — Revisão posterior:** [i2-audit-plan.md](i2-audit-plan.md), commit `69ee9c9`, detalhou auditoria estrita, redes efetivas, quotas por sessão, falhas/cleanup, provas nos dois bots e documentação antes das correções. [Resultados da revisão](i2-audit-results.md).

## Tasks do incremento — escopo concluído, tarefas amplas preservadas

- [x] I2-01 [US2] Fontes fixadas, server CLI/protocolo, dependência WebSocket e hashes conferidos; [NOTICE](../../spikes/isolamento/arena/NOTICE.md) documenta origem e limitações. T007/T017/T020; FR-006/012/015; TH-10/13/15.
- [x] I2-02 [US2] Política `services/worker_agent/arena_policy.py`, mutações negativas e 24 invariantes efetivas por papel, incluindo redes anexadas. T018/T019/T022; FR-005/006/007/018; TH-02/03/04/05/15.
- [x] I2-03 [US3] Captura POSIX aceita stdin limitado sem shell; testes de saída, erro, buffer de stdin, timeout e grupo de processos. T024/T025; FR-009/010/014; TH-07/08/12.
- [x] I2-04 [US2] Imagens por papel, espera controlada e ACL antes do payload; supervisor somente em CI descartável. `scripts/run_separated_arena.py`. T005/T006/T007/T011; FR-005/006/007/019; TH-01/02/03/04/05.
- [x] I2-05 [US2] Cliente controlador/observador e três rounds oficiais, bot IDs oficiais e nenhum processo de bot no árbitro; gateway planejado em N5. T007/T020; FR-005/006/012; TH-09/10/15.
- [x] I2-06 [US2] Controles positivos/negativos nos dois bots: 19 verificações por bot, credencial inválida, troca de papel, controle, porta bruta, host/peer canários, DNS/IPv6/TEST-NET e arquivos protegidos. Políticas aplicadas e contadores de rejeição observados. Sem scan de LAN ou exploração de kernel. T019/T021/T022; FR-005/006/007/018; TH-03/04/05/09/15.
- [x] I2-07 [US4] Eventos oficiais, três fins de round, tipos, identidades, hashes e resultado final conferidos; negativos de corrupção; nova CLI somente leitura. Fonte é GameEndedEventForObserver, não stdout dos bots. T020/T029/T031/T032; FR-011/012/014/015; TH-10/12/13/15.
- [x] I2-08 [US3] Duas batalhas reais e duas falhas parciais controladas, limpeza owned sem órfãos; regressões de contratos, motor, autoria, I1 e Spec Kit aprovadas no lote de referência. Falha de daemon na limpeza de imagem tem regressão adicional própria. T025/T026/T036/T037; FR-009/010/018/019; TH-07/08/12/14.
- [x] I2-09 [US5] Artifact baixado, ZIP/gzip/eventos e manifestos relidos; [relatório](../../docs/qualidade/evidencias/S04-T04-I2.md), estado e limites registrados. Não encerra os gates amplos nem habilita alunos. T035/T039; FR-018/019/020; TH-01/14/15.

## Evidência de referência

[Run 38048459272](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38048459272), fonte `9dd75a8`, completed/success. **Walls 223 × Spin Bot 193** e **Walls 159 × Spin Bot 186**, três rounds cada. 286 testes automatizados (275 unitários/contratos/regressão e 11 transportes WebSocket com engine falso), distintos das batalhas reais. A correção posterior de consulta de imagem acrescenta um teste, sem alterar os resultados históricos.

24 invariantes por contêiner; 19 verificações em cada bot; abortos after_containers/after_ready descartaram os recursos. Manifestos não autorizam alunos/VM. Resultado do último commit e regressões seguintes devem ser consultados no PR #19; os placares deste lote não são reescritos.

## Critérios e alcance

1. Cada batalha concluiu três rounds com identidades oficiais, saída e registro de eventos do motor.
2. Contêineres possuem roots e PID/net/mnt namespaces distintos do host e entre si; sem segredo administrativo no bot, montagens de host ou portas publicadas.
3. Os testes de negação possuem controles positivos; timeout isolado não é tratado como autorização recusada. Captura dos contadores reforça a aplicação efetiva da ACL.
4. Hash demonstra integridade dos bytes, não honestidade de árbitro comprometido. Gravação dos eventos oficiais feita pelo controlador não significa compatibilidade testada com visualizador oficial.
5. Duas falhas parciais e duas batalhas demonstram cleanup nesse recorte; não equivalem a vinte ciclos, recuperação durável ou reboot da VM.
6. Não houve implantação da VM doméstica, cliente público, fila durável, identidade de alunos, Java livre, benchmark de capacidade ou prova formal de inexistência de escape.

A ordem permanece planejamento → implementação/testes → evidências. Qualquer nova lacuna exige adendo antes do código. Próxima etapa: detalhar I3 (broker/autorização/fila/ledger) a partir do catálogo amplo, mantendo a camada já comprovada e a regressão.

## Reconciliação #18/#19/#21 e fechamento experimental antes de I3

O [plano R01–R10](i2-reconciliation-plan.md) e a [decisão C01–C05](i2-reconciliation-decision.md) foram publicados antes das correções. PR #19 é a implementação canônica; PRs #18/#21 foram encerrados sem merge, preservando seus commits. Adicionados timeout real/cleanup, vínculos de fonte e eventos e negativos de protocolo/roster/processos. A implementação `e7afd8a2ac7cb1ab45eeec2146ae828e56f93e0a` passou quatro workflows; 320 testes de regressão reproduzidos fora do runner. Duas batalhas de três rounds, dois abortos e um timeout real concluídos; 12 arquivos e sua semântica auditados externamente ao runner. Zero pendências abertas do recorte I2; macro S04-T04 e G-PROD continuam pendentes.

[Relatório final de I2](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md) · [Manifesto](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.json). Não alterar os placares dos lotes históricos acima.
