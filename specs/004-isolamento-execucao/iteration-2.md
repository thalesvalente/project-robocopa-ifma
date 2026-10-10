# S04-T04 — Incremento I2: árbitro e bots separados

**Data:** 2026-10-10. **Base:** I1, commit 668d82b034cf5e0fab909e13552399c2de7213d5. **Estado inicial:** PLANEJADO, antes da implementação. Continuação autorizada pelo responsável: implementar tarefas planejadas; registrar novas necessidades primeiro. G-EXP permanece autorizado em GitHub-hosted efêmero; G-PROD bloqueado. Não alterar o Windows nem instalar VM.

## Objetivo e limite

Realizar duas batalhas reais com Tank Royale 1.4.0: árbitro/controlador em um contêiner; cada bot oficial conhecido em seu próprio contêiner, com filesystem, PIDs e namespace de rede distintos. Não usar BattleRunner.externalServer como falsa externalização dos bots: controlar explicitamente o protocolo WebSocket oficial e iniciar JVMs somente nos contêineres dos bots. Usar Walls e Spin Bot fixados; não adicionar linguagem nem receber código de estudantes.

## Necessidades novas identificadas e planejadas antes do código

**N1 — Transporte independente do booter:** cliente controlador/observador usando o protocolo oficial, dependência WebSocket fixada com hash; preserva a versão do motor. Server JAR poderá ser extraído do runner.jar já verificado, se a estrutura oficial confirmar isso. Não implementar física ou pontuação própria.

**N2 — Rede com comunicação permitida:** network=none não permite bots em namespaces distintos. Criar bridge Docker internal exclusiva da rodada e, antes de executar Java, aplicar regras INPUT/OUTPUT/FORWARD no namespace de cada contêiner. O supervisor confiável do runner usa nsenter apenas em PID/namespace de contêiner confirmado por ID, label e inode distinto do host. Não tocar nas tabelas do namespace do host. Runtime do bot continua sem NET_ADMIN/NET_RAW, sem host mounts/socket/dispositivos e sem portas publicadas. Destino permitido: IP numérico do árbitro e porta TCP de jogo. IPv6 negado; DNS e gateway/LAN/pares não permitidos. Se regra não puder ser instalada ou inspecionada, abortar sem iniciar batalha. Remoção dos contêineres elimina seus namespaces/regras; apagar somente bridge com ownership da rodada.

**N3 — Papéis e segredos:** credencial do controlador/observador distinta de credenciais de bots, efêmeras por batalha, nunca no build/imagem ou artefato. Credenciais entram por stdin, não por docker environment/CLI pública. Bots não recebem o segredo administrativo. Validar handshake errado, bot tentando controlador/observador e comando administrativo em sessão de bot. Tokens por papel não equivalem a autenticação multiusuário nem binding criptográfico de identidade; registrar limites do upstream.

**N4 — Evidência e subprocesso:** estender captura limitada para stdin pequeno sem bloquear o watchdog, com testes. Capturar eventos oficiais/replay em canal do árbitro, esquema/identidades/rounds, hash e limpeza. Bytes de stdin/segredos não entram em erro/log. Limitar saída enquanto lida. Dados sintéticos apenas.

## Tasks do incremento (subconjuntos das 39 tarefas amplas)

- [ ] I2-01 [US2] Conferir fontes oficiais versionadas (server CLI, handshakes, tipos de eventos/controle, inicialização de bots), dependência WebSocket e hashes; documentar pesquisa e NOTICE em spikes/isolamento/arena/. T007/T017/T020; FR-006/012/015; TH-10/13/15.
- [ ] I2-02 [US2] Definir política de contêiner/namespace/rede por papel em services/worker_agent/arena_policy.py e testes de mutações negativas. T018/T019/T022; FR-005/006/007/018; TH-02/03/04/05/15.
- [ ] I2-03 [US3] Acrescentar stdin limitado ao coletor POSIX em bounded.py, sem shell e sem bloqueio fora do timeout; testar saída, erro, stdin cheio, timeout e limpeza. T024/T025; FR-009/010/014; TH-07/08/12.
- [ ] I2-04 [US2] Construir imagens por papel, servidor e bots com entrypoints fixos; iniciar em espera e instalar ACLs antes do primeiro payload. Supervisor só em CI descartável, sem Docker remoto/Desktop/WSL/local. scripts/run_separated_arena.py; T005/T006/T007/T011; FR-005/006/007/019; TH-01/02/03/04/05.
- [ ] I2-05 [US2] Implementar cliente controlador/observador e partidas usando bot IDs oficialmente listados, sem processos bot no árbitro. T007/T020; FR-005/006/012; TH-09/10/15.
- [ ] I2-06 [US2] Executar controles positivos/negativos: handshake válido; token errado; credencial de bot em controlador/observador; comando de controle por bot; TCP permitido ao árbitro; host gateway, peer, porta indevida, DNS/IPv6/TEST-NET negados; arquivos canário do árbitro invisíveis e PIDs distintos. T019/T021/T022; FR-005/006/007/018; TH-03/04/05/09/15. Não varrer LAN nem explorar kernel.
- [ ] I2-07 [US4] Validar e exportar eventos oficiais, resultados, fim dos três rounds, identidades e hashes; corrupção e divergência rejeitadas; não usar stdout do bot como placar. T020/T029/T031/T032; FR-011/012/014/015; TH-10/12/13/15.
- [ ] I2-08 [US3] Rodar duas batalhas e provar cleanup somente de contêineres/bridge da rodada, sem credenciais em artefatos; executar regressões I1, motor, editor e Spec Kit. T025/T026/T036/T037; FR-009/010/018/019; TH-07/08/12/14.
- [ ] I2-09 [US5] Inspecionar artifact baixado, registrar resultados e limitações, atualizar tasks/estado/PR sem encerrar gates amplos e sem habilitar alunos. T035/T039; FR-018/019/020; TH-01/14/15.

## Critérios de aceite do experimento

1. Cada batalha conclui 3 rounds reais, com duas identidades oficiais e resultado oficial preservado. Duas execuções no CI, sem exigir placar constante.
2. Contêineres possuem roots e PID/network namespaces diferentes; nenhum bot recebe segredo controlador, mount de host, socket Docker, NET_ADMIN ou porta publicada.
3. Políticas de rede efetivas conferidas, com teste positivo que evita falso PASS por indisponibilidade geral. Negativos de rede/protocolo precisam observar rejeição; timeout isolado não é prova suficiente de autenticação.
4. Fonte de resultados é o canal observador do motor. Hash demonstra integridade dos bytes, não honestidade de um árbitro comprometido.
5. Zero órfãos/bridge próprios após execução ou falha; nenhuma limpeza global. Logs/artefatos verificados contra segredos efêmeros antes de upload.
6. Não há implantação da VM doméstica, cliente público, fila durável, identidade de alunos, liberação de Java livre, benchmark de capacidade ou prova formal de inexistência de escape.

## Sequência e dependências

I2-01 → I2-02/I2-03 → I2-04 → I2-05 → I2-06/I2-07 → I2-08 → I2-09. O plano do I1/39 tarefas permanece fonte de rastreabilidade; esta iteração não substitui backlog macro. Se o upstream não garantir uma permissão esperada, registrar achado, planejar mitigação (proxy/filtro/gate) antes de alterar código e não enfraquecer silenciosamente o aceite.

## Fontes externas iniciais

- Docker networking e container namespaces: https://docs.docker.com/engine/network/
- Tank Royale WebSocket: https://robocode.dev/articles/tank-royale.html
- Papéis: https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/docs/decisions/0007-client-role-separation.md
- Server CLI 1.4.0: https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/server/src/main/kotlin/dev/robocode/tankroyale/server/cli/ServerCli.kt

Sem implementação ou teste operacional comprovado no momento inicial de publicação deste plano.
