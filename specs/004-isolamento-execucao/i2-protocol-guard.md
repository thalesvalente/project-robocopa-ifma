# I2 / adendo N5 — autorização por mensagem no canal do bot

**Data:** 2026-10-10. **Origem:** planejado antes do gateway. **Estado atual:** mitigação implementada e verificada no recorte do CI. Vínculos I2-05/06, T019/T020/T029, FR-006/012/018, TH-10/15. Não muda RoboDSL básica nem habilita alunos.

## Achado na fonte e confirmação controlada

No commit upstream `c8ad3a8d19a843f6258d6f6f9db7f29229963903` (Tank Royale1.4.0), `ClientWebSocketsHandler.processMessage` despacha certos comandos administrativos para handlers sem passar clientSocket. Os handshakes verificam segredo, mas isso não demonstra autorização de todos os comandos posteriores.

No lote [38048459272](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38048459272), uma mensagem benigna ChangeTps enviada **no ambiente owned do árbitro, antes da batalha**, mudou TPS pela porta bruta sem handshake administrativo. Controller legítimo observou a mudança e restaurou o valor antes dos jogos. Não foi executado ataque externo, não há CVE atribuído e não se generaliza a outras versões.

Fonte primária: https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/server/src/main/kotlin/dev/robocode/tankroyale/server/connection/ClientWebSocketsHandler.kt, métodos processMessage/handleChangeTps/handleStopGame. Archive inicial obtido no run38025278846; código conferido novamente nesta revisão.

## Desenho implementado

- Motor bruto7655 protegido por ACL, inacessível aos namespaces de bots.
- Gateway no lado confiável do árbitro, porta7654, único destino de jogo permitido aos bots.
- Primeira mensagem apenas BotHandshake: sessionId exato, token efêmero vinculado ao nome/versão configurados. Substituição por segredo upstream do bot; segredo administrativo ausente do contêiner de bot.
- Mensagens seguintes apenas BotIntent/BotReady, campos/tipos/tamanho limitados; negar StartGame/StopGame/ChangeTps, ObserverHandshake, ControllerHandshake e novo handshake.
- Controller/Observer legítimos permanecem locais ao árbitro e usam a classe de segredo administrativo do upstream. Não são três chaves independentes por papel.
- Gateway possui limites de mensagem, conexão, bytes cumulativos, vida útil e inatividade; sem compressão ou destino indicado pelo cliente. Uma identidade por sessão ativa.
- O gateway é componente confiável adicional com riscos próprios. Não implementa física ou placar, não autentica contas de estudantes e não substitui revisão de segurança de produção.

## Tarefas suplementares e evidência

- [x] I2-05A Parser/allowlist em `services/worker_agent/arena_protocol.py`; negativos de comandos administrativos, desconhecidos, JSON duplicado/NaN, binário, identidade/token e limites.
- [x] I2-05B Gateway em `spikes/isolamento/arena/gateway.py`, destino fixo e limites; 11 testes de transporte WebSocket usam engine falso explicitamente. Limites adicionais foram planejados em H03 antes da implementação.
- [x] I2-06A Prova benigna no protocolo bruto confirmou mudança de TPS sem handshake; registrada nos dois manifestos, sem extrapolação para exploração externa.
- [x] I2-06B Nos dois bots, acesso direto7655 foi negado; gateway fechou mensagens administrativas/rehandshake com1008. `gateway_control_did_not_change_engine=true` nas duas batalhas.
- [x] I2-08A Duas partidas reais via gateway concluíram três rounds; tráfego de BotReady/BotIntent e pontuação do motor preservados; artifacts sem credenciais efêmeras.

Estes itens detalham I2-05/06/08, não aumentam as sessenta tarefas macro nem fecham a segurança global. [Evidência](../../docs/qualidade/evidencias/S04-T04-I2.md). G-PROD, VM real e submissões de estudantes continuam bloqueados.
