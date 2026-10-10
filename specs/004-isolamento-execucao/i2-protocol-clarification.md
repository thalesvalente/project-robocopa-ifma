# I2 — Esclarecimento do protocolo após leitura do upstream fixado

**Data:** 2026-10-10. Adendo anterior ao código do I2. Complementa I2-01/02/05/06; não amplia linguagens do MVP.

## Achados da fonte 1.4.0

No commit `c8ad3a8d19a843f6258d6f6f9db7f29229963903`, `ClientWebSocketsHandler.kt` usa `controllerSecrets` tanto para ControllerHandshake como para ObserverHandshake. Não existe CLI `--observer-secrets` nesta versão. Assim, não afirmar que há credenciais nativas independentes de observador/controlador: é uma autoridade administrativa compartilhada, distinta da autoridade dos bots.

A revisão de `processMessage` e handlers de controle mostra que alguns comandos de controle são encaminhados sem uma checagem de papel naquele caminho. Não presumir que a recusa de handshake basta para proteger cada mensagem. É um achado de revisão de código, não uma alegação de exploração de serviço externo.

## Decisão de projeto para o experimento

Não deixar bots conectarem diretamente ao socket do árbitro. Adicionar **gateway confiável de protocolo** entre as duas redes individuais de bots e a rede de backend do árbitro:

```
Bot Walls -- rede A isolada -- Gateway -- rede backend isolada -- Árbitro + controlador/observador
Bot Spin  -- rede B isolada -- Gateway
```

Quatro contêineres distintos e três redes exclusivas por execução. Os bots não têm interface/rota na rede backend nem rede compartilhada entre si. Gateway com IP forwarding desabilitado. Interfaces frontend do gateway escutam somente no endereço de sua rede; não escuta na interface backend. Nenhuma porta é publicada no host. Modos de rede/verificações devem falhar fechado.

O gateway mantém uma máquina de estados por conexão: ServerHandshake → um BotHandshake válido → somente BotReady e BotIntent. Nome/versão/sessão e segredo frontend vinculados a um único participante; encaminhar ao backend somente depois de validação, trocando o segredo pelo segredo do backend. Administrador e observador ficam no árbitro. Não registrar tokens nos eventos/logs/artefatos. Limitar bytes por mensagem, conexões e campos aceitos.

O gateway é controle adicional de defesa do MVP experimental; não elimina vulnerabilidades desconhecidas do servidor, kernel, implementação do próprio gateway ou necessidade da VM real. O observador público de alunos no futuro não receberá credencial nativa de controlador: precisará de API filtrada no plano de controle, fora do I2.

## Nova tarefa antes de implementar

- [ ] I2-11 [US2] Implementar gateway de protocolo com allowlist/máquina de estados, reescrita autorizada de identidade/segredo e limites; negar mensagens administrativas mesmo com handshake de bot válido. Arquivos planejados `spikes/isolamento/engine-separation/ProtocolGate.java` e testes `tests/security/test_game_separation.py` + teste JVM de contrato. T019/T020/T021; FR-003/004/006/007/012/014/018; TH-01/05/06/10/12/15.

Dependência: I2-01/02 -> I2-11 -> I2-05/06/07. Os aceites de I2-06 incluem agora: handshake controlador/observador recusado no gateway, mensagem administrativa recusada antes e depois de autenticação de bot, reconexão válida após recusa, identidade cruzada recusada, mensagem grande demais recusada; verificar também que a rota direta ao árbitro não é alcançável pelo bot.

Fonte: https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/server/src/main/kotlin/dev/robocode/tankroyale/server/connection/ClientWebSocketsHandler.kt . CLI em `server/cli/ServerCli.kt`. A pesquisa de fontes não executou comandos de controle contra servidores de terceiros.
