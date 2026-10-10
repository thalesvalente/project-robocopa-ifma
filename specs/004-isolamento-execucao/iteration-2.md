# S04-T04 — Incremento I2: jogo com árbitro e robôs separados

**Data:** 2026-10-10 · **Branch:** `feat/s04-i2-referee-isolation` · **Base:** I1 `668d82b`.  
**Estado do incremento:** PASS TÉCNICO em CI descartável (referência 38051902244); revisão de segurança e VM real pendentes. **Autorização:** continuidade técnica do usuário, limitado a runners efêmeros do GitHub; **não instala nem modifica VM/Windows/Docker Desktop pessoal**.

## Objetivo e critério

Comprovar, usando **Tank Royale oficial v1.4.0 fixado**, que um servidor árbitro separado e dois bots **confiáveis de referência** em contêineres distintos executam batalha verdadeira (>=3 rounds), com resultado originado do árbitro, segredos por papel, rede de jogo mínima e impossibilidade de bot alcançar a rede exclusiva do controlador no cenário testado.

Isso não significa homologar código hostil de alunos: isolamento entre Linux containers do mesmo daemon não substitui a VM dedicada no host. D1 continua RoboDSL básica; T2 linguagens livres não entram no MVP.

**Mapeamento canônico:** T007, T011, T019, T020, T021, T029, T032 e T037 da feature 004; FR-003, FR-005, FR-006, FR-007, FR-012, FR-015, FR-018; TH-01, TH-04, TH-05, TH-10, TH-13, TH-15. Os checkboxes amplos continuam abertos até aceite integral.

## Decisões e pesquisa verificada

- O `BattleRunner.startBattleAsync` 1.4.0 aciona `BooterManager.boot` local mesmo com `externalServer()`, logo **não** usar esse método como falsa separação. Fontes: `runner/internal/ServerConnection.kt` e `BattleRunner.kt` do upstream v1.4.0.
- Usar **servidor standalone oficial** `robocode-tankroyale-server-1.4.0.jar` com SHA-256 do asset da release; clientes WebSocket oficiais por papel: observador, controlador e bot, com `bot-secret` distinto do `controller-secret`.
- Implementar **controlador independente e restrito** via WebSocket (mensagens `ServerHandshake`, `ControllerHandshake`, `ObserverHandshake`, `BotListUpdate`, `StartGame` e `GameEndedEventForObserver`), sem executar Booter no controlador.
- **Achado de análise de código:** em `ClientWebSocketsHandler.kt` 1.4.0, o despacho de `StartGame` e outros comandos administrativos não verifica explicitamente `controllerSockets` antes de acionar o listener. **Risco TH-15 e TH-01:** um cliente bot conectado não deve alcançar diretamente o servidor. Regra fail-closed obrigatória: gateway de protocolo valida o tipo de mensagem e encaminha somente `BotHandshake`, `BotReady`, `BotIntent` e `TeamMessage`. Bloquear `ControllerHandshake`, `ObserverHandshake`, `StartGame`, `StopGame`, `ChangeTps`, `PauseGame` e quaisquer tipos não explicitamente permitidos.
- Rede de teste: dois segmentos Docker descartáveis **`bot` (2 bots + gateway)** e **`trusted` (gateway + servidor árbitro + controlador)**, sem publicar portas no host, sem socket, bind mount nem acesso a segredos do banco. Somente o gateway tem duas interfaces; **bots não compartilham rede com o servidor/árbitro**. Esse modelo ainda é um experimento no mesmo daemon Docker de CI, não uma VM isolada do host.
- Autenticação por segredo no servidor ativa **explicitamente**; sem isso, o protocolo não comprova autorização.
- O servidor é árbitro confiável do experimento e recebe segredos transitórios de teste. Registro `BattleResults` será obtido pela mensagem de árbitro `GameEndedEventForObserver`; logs de bots **não definem pontuação**.
- Prova negativa: `bot-secret` não autoriza iniciar partida pelo papel `ControllerHandshake` e rede `trusted` não é acessível ao bot. Não afirmar robustez contra comprometimento do kernel/host.
- Pinar assets upstream por `size` e `sha256`, e base Docker por digest quando disponível. Fazer download somente durante `docker build`, nunca durante o jogo.

## Subtarefas I2

| ID | Entrega e localização | Evidência objetiva | Dependências |
|---|---|---|---|
| I2-01 | Confirmar release 1.4.0, CLI, schema WebSocket, hashes e autenticação; `spikes/isolamento/i2/upstream.lock.json` e fontes | Fonte e digest fixados | I1 |
| I2-02 | Build verificado de imagem standalone servidor e bots oficiais; `spikes/isolamento/i2/Dockerfile` e `prepare.py` | CI constrói imagem sem `latest` | I2-01 |
| I2-03 | Controlador WebSocket restrito independente do Booter; `spikes/isolamento/i2/controller.py` | handshake, start-game, três rounds, resultado íntegro | I2-01 |
| I2-04 | **Gateway WebSocket de mensagens por papel** em `spikes/isolamento/i2/gateway.py`; topologia `bot`/`trusted`, negar comandos do controlador antes do servidor | testes unitários e prova negativa de `StartGame` encaminhado pelo lado bot; ausência de controller secret no gateway/bots | I2-02/03 |
| I2-04b | Orquestração Docker com dois segmentos efêmeros e limpeza por ownership; `scripts/run_isolation_i2.py` | inspecionar topologia e política efetiva, sem portas/mount/segredos de terceiros | I2-04 |
| I2-05 | Testes de casos negativos e falha fechada; `tests/security/test_i2_*.py` | comando `StartGame` vindo do bot bloqueado **antes de chegar ao servidor**; papéis, portas, timeout, hash, rede e limpeza | I2-03/04b |
| I2-06 | Executar batalha real oficial com **servidor e bots em contêineres/rede distintos**, passando apenas pelo gateway, em GitHub-hosted Ubuntu | Resultado do árbitro, rounds e vencedores documentados; não fixture | I2-04b/05 |
| I2-07 | Regressão I1/Spec Kit/planejamento, logs/evidências sintetizados | CI PASS; nenhum recurso residual do experimento | I2-06 |
| I2-08 | Atualizar documentação de segurança, `iteration-2.md`, PR e issue mantendo gates | S04-T04 continua EM_EXECUCAO | I2-07 |

## Guardrails/Gates

**G-EXP:** somente Ubuntu GitHub-hosted efêmero, credenciais fictícias geradas por execução, contêineres referenciados exclusivamente por IDs criados pelo harness; nenhum `docker system prune`, alterações de firewall, mounts do host, `.env`, VM do responsável, runner self-hosted, publicação web ou contato com alunos.

**G-I2:** só aprovar experimento se o servidor e bots executarem em **contêineres e redes diferentes**, com gateway que **nega mensagens administrativas** antes de chegar ao servidor, os segredos forem distintos, e o resultado oficial registrar todos os rounds. O servidor 1.4.0 não é tratado como um gateway de autorização por tipo de mensagem. Falhas reais ficam como FAIL/inconclusivas, não substituir por mocks.

**G-PROD:** continua BLOQUEADO, independentemente do êxito do I2. Ainda faltam broker, segurança de API, árbitro/protocolo sob abuso, isolamento em VM própria, recuperação/backup, 20 ciclos e avaliação independente.

**Dúvidas técnicas abertas que exigem teste (não alegar resposta):** identificadores de BotAddress no servidor 1.4.0; path/variáveis da Bot API Java na release; capacidade de bloquear tráfego entre segmentos Docker sem gateway para host; integridade de replay oficial quando observer externo; recursos reais de JVM do novo arranjo.

## Resultado efetivamente executado (referência imutável)

[Lote com negativa de IP 38051902244](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38051902244): dois jobs PASS, **três rounds reais** Walls 330 × Spin Bot 1, **2.734 ticks** de eventos do árbitro. Gateway bloqueou ControllerHandshake, StartGame e StopGame enviados pelo lado bot; a sonda validou também que bot não acessa diretamente o árbitro por DNS ou IP neste ambiente. O artifact de 269.735 bytes foi baixado e conferido (SHA-256/CRC/gzip/JSON/eventos finais), com limpeza e invariantes de runtime verificadas. [Evidência detalhada](../../docs/qualidade/evidencias/S04-T04-I2.md).

**Situação das subtarefas experimentais:** I2-01, I2-02, I2-03, I2-04, I2-04b, I2-05, I2-06, I2-07 e I2-08 **executadas no escopo delimitado do spike e desta documentação**. Os checkboxes amplos T007/T011/T019/T020/T021/T029/T032/T037 continuam abertos na feature 004, pois abrangem produção, código de estudantes e/ou VM que não foram validados. **Nenhuma execução no host pessoal.**

**Próximo incremento autorizado a planejar antes de codificar:** I3 — contrato autenticado de broker/worker, fila durável, idempotência e recuperação, sem conectar a UI pública ou habilitar estudantes até os gates. G-PROD permanece bloqueado.
