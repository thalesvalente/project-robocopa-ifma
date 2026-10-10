# Arena separada — S04-T04 / I2

**Apenas experimento em runner GitHub-hosted descartável. Não executar a bateria no Windows, WSL ou Docker Desktop pessoal.** A trava de ambiente evita acidentes; não é atestado criptográfico. G-PROD e acesso de alunos permanecem bloqueados.

## O que foi demonstrado

Duas batalhas de três rounds, Walls contra Spin Bot, com três contêineres distintos: árbitro/controlador, Walls e Spin Bot. Cada papel tem filesystem, namespace de processos e rede próprios, sem host mounts, socket Docker, dispositivos ou portas publicadas. Não há bot executando no processo do árbitro.

```text
Bot Walls  --> porta 7654 / gateway restrito --> motor 7655 no árbitro
Bot Spin   --> porta 7654 / gateway restrito --> controlador/observador local
```

A bridge interna é exclusiva da rodada; não é considerada segura por seu nome. Antes das JVMs iniciarem, o supervisor confiável instala e verifica ACLs **nos namespaces dos contêineres owned**, nunca no namespace de rede do host. INPUT/OUTPUT/FORWARD são fechados por padrão; somente comunicação de jogo necessária e retorno de conexões permitidas. O próprio Docker administra regras para sua bridge no runner. Nada disso altera firewall/rede da máquina pessoal.

## Por que existe um gateway

A versão fixada do motor rejeita segredo incorreto nos handshakes, mas o teste benigno no protocolo bruto mostrou alteração de TPS sem handshake administrativo. O adendo [N5](../../../specs/004-isolamento-execucao/i2-protocol-guard.md) foi publicado antes da mitigação.

O gateway aceita apenas BotHandshake válido seguido de BotReady/BotIntent. Vincula token, sessão, nome e versão, rejeita mensagens administrativas/rehandshakes e impede acesso direto do bot a 7655. Controller e Observer compartilham o segredo administrativo conforme upstream; bots não recebem esse segredo. Os limites de mensagens, bytes, inatividade e duração são do experimento, não política de produção.

## Verificações e resultados

[Relatório e referência imutável](../../../docs/qualidade/evidencias/S04-T04-I2.md). A revisão confere positivamente o caminho permitido e nega acesso ao host sintético, bot vizinho, porta bruta do motor, DNS, IPv6 e destinos documentais. Cada bot é testado separadamente. Duas falhas deliberadas comprovam descarte de recursos após provisionamento e após início do árbitro.

Arquivos por lote: `batch.json`; `battle-1/` e `battle-2/` com `results.json`, `report.json`, `referee-report.json`, `recordings.battle.gz`; duas pastas `abort-*` e logs de construção limitados. Credenciais efêmeras não são exportadas. A fonte da pontuação é `GameEndedEventForObserver`, não stdout do bot nem pontuação fabricada.

## Auditoria local sem executar jogos

Depois de extrair um artifact em diretório privado e revisado, a auditoria é somente leitura:

```powershell
python scripts/verify_arena_evidence.py '<pasta-do-lote-que-contem-batch.json>'
```

Esse comando não inicia Docker, processos de bots, conexão de rede ou VM. Recusa caminhos de evidências com links simbólicos, arquivos excessivos, JSON ambíguo, tipos incorretos, eventos fora de ordem, resultados divergentes e manifestos incompletos. Um resultado PASS comprova coerência dos artefatos, não autenticidade de uma origem comprometida.

## Continuidade

I3: broker autenticado, fila durável, ledger/idempotência, cotas e recuperação. I4: instalação/patches/rede/discos da VM real, com autorização e ação do responsável. I5: vinte ciclos, cobertura integral das ameaças, backup/restauração e revisão de liberação. A autoria continua somente RoboDSL básica; nenhum recurso intermediário/avançado foi adicionado.
