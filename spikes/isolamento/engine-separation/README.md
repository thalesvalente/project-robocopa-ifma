# I2 — Tank Royale com bots, filtro e árbitro separados

**Escopo:** prova técnica somente em GitHub-hosted runner descartável, com bots oficiais fixados. **Não executar no Windows/WSL/Docker Desktop pessoal e não expor para estudantes.** A VM real ainda não foi instalada; nenhum recurso de linguagem foi ampliado.

## O que foi construído

```
Walls (contêiner próprio) -- rede A -- [gateway confiável] -- rede backend -- árbitro
Spin Bot (contêiner próprio) -- rede B -- [mesmo gateway]
```

Quatro contêineres e três redes bridge `--internal` com `gateway_mode_ipv4=isolated`. Cada bot possui apenas sua rede com o gateway; não compartilha rede com o outro bot nem com o árbitro. O gateway possui três interfaces, mas não encaminha IP, não escuta na interface backend e só aceita protocolo de jogo em suas interfaces frontend. Nenhuma porta é publicada. As redes usam faixas privadas pequenas explícitas somente no runner: conflito de subnet bloqueia a execução, sem limpar recursos de terceiros.

O árbitro contém o servidor oficial e clientes de controle/observação. Ele **não inicia os processos dos bots**. O `BattleRunner.externalServer()` não foi usado como falsa prova de separação, porque seu BooterManager ainda inicia bots localmente na versão fixada. O novo adaptador usa o protocolo oficial e o `GameRecorder` oficial para gravar os eventos reais.

## Por que existe um gateway

A revisão do servidor 1.4.0 encontrou dois pontos: observador e controlador usam a mesma autoridade nativa (`controllerSecrets`), e não se deve presumir autorização por mensagem apenas porque um handshake foi verificado. O gateway compensa esse risco na fronteira do bot: permite exatamente um `BotHandshake` autorizado, seguido somente de `BotReady` e `BotIntent` com campos/valores limitados. Mensagens administrativas são negadas inclusive depois de autenticação de bot.

Há uma credencial frontend por participante e uma credencial backend. A credencial administrativa fica somente no árbitro. O gateway reescreve identidade e segredo para campos fixos autorizados; não publica tokens em resultados ou replays. Ele é parte da base confiável e também precisará de revisão de segurança. Esta prova não demonstra resistência ao comprometimento do gateway/árbitro/kernel.

Planejamento anterior ao código: [iteration-2.md](../../../specs/004-isolamento-execucao/iteration-2.md), [adendo do protocolo](../../../specs/004-isolamento-execucao/i2-protocol-clarification.md) e [timeout/limpeza](../../../specs/004-isolamento-execucao/i2-cleanup-scenarios.md).

## Arquivos

- `Wire.java`: JSON com limites e sem chaves duplicadas, transporte WebSocket limitado.
- `ProtocolGate.java`: máquina de estados, mensagens permitidas, credenciais e estatísticas sem dados sensíveis.
- `Judge.java`: servidor oficial e controle/observação sem booter de processos locais.
- `Probe.java`: inicialização de bots oficiais e provas sintéticas internas; mapeia para `SERVER_URL`/`SERVER_SECRET` exigidos pela API 1.4.0.
- `ContractTest.java`: 40 casos de contrato JVM, incluindo comunicação legítima e negação de comandos administrativos.
- `prepare.py`/`Dockerfile`: artefatos já fixados por SHA-256 no lock da feature 002 e bases Docker fixadas por digest.
- `Dockerfile.dockerignore`: limita o contexto de build; não envia `.env`, `.local`, `.git` nem outros arquivos pessoais ao build.
- `services/worker_agent/game_policy.py`: perfil I2 e 26 invariantes antes do start para cada contêiner.
- `scripts/run_engine_separation.py`: executa somente em CI permitido, coleta resultados e remove apenas recursos próprios.

## Executar apenas no CI autorizado

O workflow `.github/workflows/engine-separation.yml` roda automaticamente no PR. Primeiro executa regressões e Spec Kit, depois dois cenários independentes:

```bash
python3 scripts/run_engine_separation.py
python3 scripts/run_engine_separation.py --timeout-cleanup-check
```

Esses comandos **não são instruções para a máquina pessoal**. A guarda recusa ambiente local/WSL/Desktop; isso evita uso acidental, mas não é atestado criptográfico. Não desabilitar a guarda nem definir variáveis para contorná-la.

O primeiro cenário conclui três rounds de Walls × Spin Bot. O segundo provoca um timeout externo de 0,5 s sobre uma fixture finita de 5 s, sem jogar; `battle_completed=false` distingue o teste negativo de uma batalha. Ambos verificam limpeza de seus quatro contêineres e três redes. Sem `prune`, `down -v`, modificação de daemon, firewall ou redes de terceiros.

## Evidência confirmada

[Run 38026424513](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38026424513), fonte `b003e599ce17ade1af15cf3b8e50123b4b34dfae`: **208 testes Python, 40 casos JVM, batalha real e timeout/limpeza passaram**. Placar observado: **Spin Bot 253 × Walls 154**, três rounds e 3515 ticks. As nove tentativas proibidas de protocolo foram repetidas em cada bot (18 por cenário). Controles positivos, rede/namespace e limpeza também foram verificados.

Artefatos baixados e conferidos: hash/CRC ZIP, JSON, gzip, eventos e placar final. [Relatório](../../../docs/qualidade/evidencias/S04-T04-I2.md) e [manifesto resumido](../../../docs/qualidade/evidencias/S04-T04-I2.json). Pontuações variam; não existe seed fixa nem benchmark de capacidade.

## Limites

O teste usa somente Walls/Spin Bot oficiais. Não integra a RoboDSL ao novo executor, não inclui contas, broker/fila/ledger de produção, não instala Hyper-V/VM e não habilita acesso público. A separação por namespaces no runner **não comprova a fronteira de hipervisor do host**. Vinte ciclos, recuperação durável, autenticação de usuários, cobertura completa de ameaças e revisão independente continuam nos incrementos posteriores.

**Próximo incremento:** I3, com planejamento detalhado antes do código de broker, autorização, fila e registro idempotente de resultados. O protótipo local 18081 permanece apenas laboratório do responsável, inalterado por este I2.

## Fontes primárias

- [Docker: gateway modes](https://docs.docker.com/engine/network/port-publishing/).
- [Upstream fixado: tratamento de conexões e mensagens](https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/server/src/main/kotlin/dev/robocode/tankroyale/server/connection/ClientWebSocketsHandler.kt).
- [Bot API: variáveis de conexão oficiais](https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/bot-api/java/src/main/java/dev/robocode/tankroyale/botapi/internal/EnvVars.java).
- [Java-WebSocket 1.6.0: construtores de Draft_6455](https://github.com/TooTallNate/Java-WebSocket/blob/v1.6.0/src/main/java/org/java_websocket/drafts/Draft_6455.java).
- [Origem/licença do motor e exemplos](../../tank-royale/NOTICE.md). As bibliotecas e imagens preservam suas licenças próprias.
