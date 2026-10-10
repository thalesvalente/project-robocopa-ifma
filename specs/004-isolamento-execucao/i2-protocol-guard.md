# I2 / adendo N5 — autorização por mensagem no canal do bot

**Data:** 2026-10-10. **Estado:** planejado antes do código. Vínculos: I2-05/06; T019/T020/T029; FR-006/012/018; TH-10/15. Não muda o escopo RoboDSL básica nem habilita alunos.

## Achado de revisão de fonte

No commit upstream c8ad3a8d19a843f6258d6f6f9db7f29229963903 (1.4.0), ClientWebSocketsHandler.processMessage despacha certos comandos administrativos para handlers sem passar clientSocket. Os handshakes verificam segredo, porém a leitura não demonstra verificação de papel em todos os comandos posteriores. É necessário teste dinâmico com comando benigno de TPS em ambiente descartável antes de classificar comportamento. Não criar issue upstream nem anunciar CVE automaticamente.

Fonte: server/src/main/kotlin/dev/robocode/tankroyale/server/connection/ClientWebSocketsHandler.kt, métodos processMessage/handleChangeTps/handleStopGame. Evidência primária de fonte extraída de archive versionado, obtido no run 38025278846. Não generalizar a outras versões.

## Alteração de desenho para I2

- Motor bruto escuta porta privada 7655, inacessível aos namespaces de bots (ACL de origem/destino/porta).
- Gateway de protocolo fica no lado confiável do árbitro, porta de jogo 7654. Bot só pode alcançar essa porta via rede.
- Primeira mensagem: apenas BotHandshake, sessionId exato, token efêmero vinculado à identidade/name/version configurada para aquela execução. Credencial é substituída pelo segredo upstream do bot; bots não conhecem segredo bruto nem administrativo do árbitro.
- Mensagens posteriores: apenas BotIntent e BotReady, validação de campos/tipos/tamanho finitos e negação de mensagens extras (inclusive outro handshake). Nada de StartGame/StopGame/ChangeTps, ObserverHandshake ou ControllerHandshake no caminho do bot.
- Canal do controlador/observador é local ao árbitro; usa segredo independente, não exposto ao gateway do bot. Gateway não define física ou pontuação, só media mensagens permitidas.
- Limites de mensagem, conexão, handshake e saída; sem compressão WebSocket; destinos fixos, nenhum destino indicado por cliente. Um token/name/version por sessão ativa.
- O componente é uma fronteira confiável adicional com custo/risco próprios; registrar testes e limitações, não declarar sandbox de produção.

## Tarefas suplementares detalhadas

- [ ] I2-05A Implementar parser estrito/allowlist por fase em services/worker_agent/arena_protocol.py; testes negativos para todos os tipos administrativos, tipos desconhecidos, JSON duplicado/NaN, binário, rehandshake, identidade divergente, token incorreto e limite de bytes.
- [ ] I2-05B Implementar gateway com upstream fixo, max_size/max_queue/timeout/conexões finitos em spikes/isolamento/arena/gateway.py; nenhum log de credencial ou frame bruto não autorizado.
- [ ] I2-06A Teste controlado interno ao árbitro: comparar comportamento do protocolo bruto e do gateway com comando benigno ChangeTps. Documentar observado sem extrapolar para exploração externa.
- [ ] I2-06B Provar negativamente do contêiner do bot: acesso direto a 7655 negado; gateway fecha com política ao receber ControllerHandshake/ObserverHandshake/ChangeTps; o estado observado do motor não muda pela mensagem bloqueada. Controle positivo BotHandshake/BotReady/Intent preserva a batalha.
- [ ] I2-08A Reexecutar duas partidas reais usando somente o gateway; repetir regressão e conferir vazamento de segredos antes de upload.

Estes itens detalham I2-05/I2-06/I2-08, não aumentam as 60 tarefas macro nem fecham a segurança global. Implementar somente após este plano publicado, em G-EXP; G-PROD permanece bloqueado.
