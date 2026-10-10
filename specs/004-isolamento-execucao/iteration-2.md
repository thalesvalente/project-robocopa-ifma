# Incremento I2 — Batalha real com bots e árbitro separados

**Data:** 2026-10-10. **Status:** PLANEJADO; nenhuma implementação/prova deste incremento concluída neste commit.
**Branch:** `feat/s04-judge-bot-isolation`, base PR #17 / `668d82b034cf5e0fab909e13552399c2de7213d5`.
**Autorização:** o responsável pediu continuidade das implementações planejadas e planejamento prévio de qualquer necessidade nova. Mantêm-se D-005/G-EXP e G-PROD bloqueado. Sem instalação da VM ou alteração do computador pessoal.

## Objetivo e rastreabilidade

Provar T007/T019/T020/T021/T022/T029: Tank Royale 1.4.0 oficial com árbitro/controlador e **dois bots oficiais confiáveis em contêineres distintos**, canal de jogo restrito, segregação de credenciais por papel, resultado/replay verificados e limpeza específica. Este incremento não é broker, autenticação de alunos, proteção formal contra comprometimento do kernel ou implantação final da VM.

O BattleRunner `externalServer()` inicia bots por BooterManager local; logo, não o usar como prova de separação. Investigar API/protocolo de controlador/observador e iniciar bots fora do processo/contêiner do árbitro.

## Novas necessidades detectadas e planejadas antes do código

1. Ler os esquemas, cliente, servidor e exemplos do **commit upstream fixado**; arquivo de fonte de CI pode apoiar revisão offline, sem executar código dessa fonte durante a pesquisa.
2. Verificar opção Docker `--internal` + `com.docker.network.bridge.gateway_mode_ipv4=isolated`, que evita endereço no bridge. Não aceitar bridge/internal comum como equivalente; falhar fechado se modo não suportado.
3. Avaliar uma rede exclusiva por bot, com o árbitro conectado a ambas, sem comunicação direta entre bots nem roteamento pelo árbitro. IPv6/desvios de rota precisam estar negados.
4. Separar segredo de bot, controlador e observador. Testar que credencial de bot não permite controle/observação privilegiada; nunca publicar esses segredos em artifacts.
5. Controle **positivo** de comunicação com o motor e controles **negativos** usando destinos/canários sintéticos do runner, sem scans de internet/LAN pessoal.
6. Preservar eventos oficiais para replay/verificação mesmo sem o booter integrado e sem montagem de diretórios do host.

## Tarefas I2 (escopo verificável)

- [ ] I2-01 Revisar upstream 1.4.0 e documentação Docker primária, registrar protocolo, portas, autenticação e limitações em `spikes/isolamento/engine-separation/README.md`. T007/T020; FR-005/006/012/015; TH-04/10/13/15.
- [ ] I2-02 Especificar topologia e contratos de runtime/rede/ownership; testar mutações inválidas antes de integrar, em `tests/security/test_game_separation.py`. T019/T021/T022; FR-005/006/007/018; TH-02/03/04/05/09.
- [ ] I2-03 Implementar adaptador de controlador/observador e exportação verificável, sem iniciar bots localmente no árbitro, em `spikes/isolamento/engine-separation/`. T007/T020/T029; FR-011/012/015; TH-10/13/15.
- [ ] I2-04 Construir imagem(s) fixadas e iniciar cada bot oficial em contêiner próprio; sem mounts, socket, portas publicadas, credenciais de DB ou privilégio. T018/T020/T022 (subconjunto); FR-005/007/015/018; TH-02/03/05/09/13.
- [ ] I2-05 Implementar redes exclusivas por bot e checar efetividade do modo isolated, ausência de rota/bridge-host e comunicação permitida com árbitro; sem fallback. T019/T021/T022; FR-006/007/016/018; TH-04/14/15.
- [ ] I2-06 Exercitar controle/observação sem segredo ou com segredo de bot e comprovar recusa; nenhum segredo nos logs/replays exportados. T020/T031; FR-003/006/012/014; TH-01/05/10/12/15.
- [ ] I2-07 Executar batalha de referência real (mínimo três rounds), associar identidades, versão do motor, hash da política, resultado e replay; validar contagens e placar. T007/T020/T029; FR-011/012/018; TH-10/15.
- [ ] I2-08 Exercitar limites externos e limpeza de todos os contêineres/redes criados pela invocação, verificando ownership e zero órfãos; nenhum prune ou operação global. T009/T010/T022/T026 (subconjunto); FR-009/010/019; TH-07/08/14.
- [ ] I2-09 Executar regressões I1, planejamento, motor/autoria; baixar e conferir artifact de integração, runtime e replay no CI. T036/T037 (subconjunto); FR-012/014/018; TH-10/12/13.
- [ ] I2-10 Atualizar spec/plan/tasks/ADR, relatório I2 e issue da sprint com evidências, resultados e pendências reais. Não encerrar S04-T04/VM/produção por este spike. T039 (subconjunto); FR-018/019/020; TH-01/14/15.

## Aceite técnico limitado

- Três identidades de contêiner distintas, processos e mounts separados; não basta atribuir nomes diferentes a processos na mesma sandbox.
- Motor recebe conexões legítimas dos dois bots e conclui rounds oficiais; inválidos não obtêm papel administrativo.
- Cada bot só está conectado à sua rede com árbitro; negativos de outro bot, serviço-canário do runner e rota externa observados, não apenas inferidos.
- Resultados e replay concordam para as identidades/versionamento/rounds. Eventos recebidos do árbitro não são substituídos por placares calculados pela UI.
- Travas operacionais recusam máquina local/WSL/Docker Desktop; são prevenção de uso acidental, não atestado criptográfico.
- Contêineres/redes próprios removidos; source/env/segredos do runner não montados nem serializados.

## Dependências e limites

I2-01 -> I2-02 -> I2-03/04 -> I2-05/06 -> I2-07/08 -> I2-09 -> I2-10. Critério incompatível com o upstream ou modo de rede indisponível deve bloquear e gerar revisão do plano antes de substituição.

Somente runners GitHub-hosted descartáveis, fixtures fixas e bots oficiais. A futura VM Hyper-V, camada gVisor/rootless, isolamento entre alunos, broker/fila/ledger/recuperação durável, auditoria independente e abertura pública continuam fora do aceite I2. Recursos do jogo serão perfil explícito de laboratório, não SLA ou dimensionamento aprovado do piloto.

## Fonte primária de rede

Docker, Port publishing and mapping, seção Gateway modes: https://docs.docker.com/engine/network/port-publishing/ . `isolated` exige `internal` e remove endereço do bridge; o modo sozinho não autentica jogadores nem comprova resistência a escape. Verificar no runtime efetivo.
