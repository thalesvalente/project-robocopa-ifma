# Estado atual — pesquisa, autoria e isolamento de robôs/árbitro

**Atualizado:** 2026-10-10, após integração dos PRs até o I2 na `main`. **Trabalho corrente:** S04-T04 em EM_EXECUCAO; I1 e o recorte I2 possuem código e provas em CI descartável. VM dedicada aprovada como direção, mas não instalada/testada no host. Sem liberação para alunos.

## Repositório e decisões

PRs **#11, #12, #13, #14, #16, #17 e #19 integrados em `main`** por merge commits, no estado final `dfd9148d`. A cadeia de branches empilhadas foi preservada no histórico; **#18, #20 e #21 encerrados sem merge** como alternativas I2. Ver [plano e trilha de integração](INTEGRACAO-PRs-2026-10-10.md) e [relatório de integração](../qualidade/evidencias/INTEGRACAO-PRs-2026-10-10.md).

A revisão de I2 comparou as fontes dos PRs #18/#19/#21, escolheu #19 e manteve a trilha de auditoria. #18/#20/#21 foram encerrados **sem merge**; suas branches não foram apagadas.

Spec Kit v1.1.2 permanece fixado em `959e866caa3618bf3dc290d5dca33394365af9c6`. Estrutura, comandos versionados e verificador nativo são usados; não há conexão MCP nativa ou invocação fictícia de slash commands.

O backlog JSON é canônico: dez sprints, sessenta tarefas. S04-T04 continua **EM_EXECUCAO**, sem fechamento de tarefa/sprint. S00-T01–T05 têm entregas técnicas; S00-T06, requisitos S03 e ratificação arquitetural integral continuam pendentes. Minutas S01/S02 não são pesquisa de campo nem aprovação institucional.

**D1:** somente RoboDSL básica no MVP; intermediário, avançado e blocos após MVP. **D2:** VM Linux independente com daemon/disco próprios e sem drives pessoais aprovada como direção. D3 tem prova técnica de separação no CI, não implantação na VM real; quotas e operação de D4 e liberação de D5 continuam condicionadas aos demais incrementos.

## Evidências anteriores preservadas

- Compose executado pelo responsável no Windows: Postgres/sonda saudáveis e loopback18080. `docs/qualidade/evidencias/INFRA-LOCAL-HOST.md`.
- Tank Royale1.4.0 de referência: CI38004097096; reprodução Windows Walls391 × Spin Bot364, cinco rounds,5255ticks,10718ms,PASS. `TANK-ROYALE-HOST.md`. Replay/manifesto local não anexados.
- Editor/RoboDSL: Chromium emulado e motor real no CI; capturas do PC Sentinela536 × Walls226 e Explorador188 × Walls188, movimento0%/94,3%. `AUTORIA-MOBILE-HOST.md`. Não é auditoria independente dos bytes locais nem telefone físico. Empate/ranks está na issue15.

## I1 — contenção inicial

Plano anterior ao código em `specs/004-isolamento-execucao/iteration-1.md`, oito subentregas mapeadas às39tarefas amplas. Contrato puro de admissão, política de diagnóstico e limites de subprocessos foram implementados; isso não é broker público/fila/ledger.

Referência [38021817642](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38021817642):164 testes unitários e9 provas reais de baseline, arquivos, rede, CPU, PIDs, tmpfs, memória, timeout e stdout.20 invariantes por contêiner e limpeza própria. Três testes de reconciliação posteriores levaram I1 a167. Relatório `docs/qualidade/evidencias/S04-T04-I1.md`. A bateria recusa Windows/WSL/Desktop; não comprova VM pessoal.

## I2 — canal de jogo e ambientes separados

Plano original `iteration-2.md` foi publicado antes do código; adendo N5 planejou filtro de mensagens antes do gateway. Nesta revisão, `i2-audit-plan.md` (commit69ee9c9) detalhou seis lacunas antes das correções: auditor estrito, redes efetivas, limites por sessão, falhas/cleanup, provas nos dois bots e documentação.

Implementação: três imagens/papéis separados, bridge interna owned com ACLs nos namespaces dos contêineres, controlador que utiliza eventos oficiais, gateway bot-only e auditor somente leitura. O teste comprovou que segredo no handshake não bastava para todos os comandos do servidor1.4.0 fixado; a mitigação bloqueia mensagem administrativa no gateway e acesso à porta bruta. Nenhum bot recebe o segredo administrativo.

**Lote referência [38048459272](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38048459272), fonte9dd75a8, aprovado:** duas batalhas de três rounds, Walls223 × Spin Bot193 e Walls159 × Spin Bot186.24 invariantes por papel,19 verificações por bot, namespaces PID/net/mnt distintos e6 pacotes recusados pela ACL de cada bot. Abortos `after_containers`/`after_ready` limparam recursos; nenhum órfão owned. ZIP/gzip/eventos/manifestos baixados e auditados fora do runner, não por auditoria externa.

Nesse lote passaram286 testes automatizados (275 unitários/contratos/regressão e11 transportes contra engine falso). Uma correção adicional de H04 incluiu regressão de daemon indisponível durante cleanup; o novo código exige consulta de existência bem-sucedida. Os placares históricos não são reescritos pelas regressões posteriores.

Fontes e detalhes: `docs/qualidade/evidencias/S04-T04-I2.md` e `.json`, `spikes/isolamento/arena/README.md`, `specs/004-isolamento-execucao/i2-audit-results.md`. I2 atende apenas ao experimento descrito; tarefas T amplas/gates de produção continuam abertos.

## Próximos incrementos

**I3:** detalhar e implementar broker autenticado, fila durável, ledger/idempotência, retry, cotas e suspensão sem socket Docker na API. A existência de contratos puros não equivale a esse serviço. Qualquer lacuna descoberta deve ser planejada no Spec Kit antes do código.

**I4:** verificar patches, discos, rede e provisionar/testar VM real, com ação e autorização específicas no host. **I5:** calibrar quotas de jogos, vinte ciclos, matriz completa de ameaças, backup/restauração, revisão e decisão de liberação. Telefone físico e revisão pedagógica permanecem em S04-T03/S03.

G-EXP permitiu engenharia/experimentos sintéticos no CI; G-PROD continua bloqueado. Sem nova linguagem, aluno real, endpoint público, instalação de VM, mudança em Docker Desktop/WSL/.env/Compose/Postgres/firewall/VHDX/roteador ou serviços pessoais. O servidor18081 continua com acesso à CLI Docker do host e **não deve ser exposto**. Sem Codex/R4 ou sessão remota na máquina do responsável.

## Atualização — I2 reconciliado antes de I3 (2026-10-10)

Plano de reconciliação R01–R10 versionado antes dos patches; análise comparou PRs #18/#19/#21. PR #19 (`e7afd8a2ac7cb1ab45eeec2146ae828e56f93e0a`) é a única base executável I2; #18 e #21 encerrados sem merge, branches preservadas. C01–C05 fechados no escopo experimental, incluindo timeout REAL, verificação de processos e manifesto de evidências associado à fonte/run. Quatro workflows PASS: [arena I2](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207968), [Spec Kit](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207983), [I1](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207938), [editor e motor](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207943). Offline: 320 testes PASS; artefato I2 baixado, hash/CRC, 12 arquivos e conteúdo conferidos; nenhuma revisão independente por terceiro foi alegada. [Relatório](../qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md).

**Zero pendências I2 abertas dentro do recorte experimental planejado; S04-T04 continua EM_EXECUCAO, G-PROD BLOQUEADO.** I3 não iniciado. VM pessoal/host não testados, código de alunos e serviços públicos não habilitados. O termo “I2 concluído” nunca deve ser usado como aprovação de produção.

## Integração em main — verificação pós-I2 (2026-10-10)

A cadeia #11→#12→#13→#14→#16→#17→#19 foi incorporada em `main` sem squash ou force push. SHA do merge final `dfd9148d104bb016b5ee4082ef59849afc3109e9` e árvore conferida idêntica à fonte final do PR #19. Os dez PRs históricos têm estado `closed`: sete `merged`, três alternativas `not merged`. Planejamento em `main` passou no run [38060749180](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38060749180). Subtarefas experimentais I1 e I2 permanecem fechadas no recorte; S04-T04 permanece EM_EXECUCAO e S00-T06 BLOQUEADA. Nenhum teste no host pessoal ou liberação de estudantes foi alegado. [Relatório de integração](../qualidade/evidencias/INTEGRACAO-PRs-2026-10-10.md).

**Validação pós-merge adicional:** PR [#22](https://github.com/thalesvalente/project-robocopa-ifma/pull/22), commit `989bf6ab`, cinco workflows PASS: planejamento [38061014782](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38061014782), Spec Kit [38061014777](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38061014777), I1 [38061014766](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38061014766), autoria [38061014795](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38061014795) e arena I2 [38061014844](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38061014844). A validação não habilita G-PROD nem substitui a VM real.

## I3 — revisão do plano antes da implementação (2026-10-10)

Após integrar I1/I2 na main `69c624df`, a auditoria verificou ausência de plano detalhado I3 e Q-07 (autenticação/transporte) ainda aberta. A nova branch `feat/s04-i3-control-plane` recebeu [plano I3-01..I3-07](../../specs/004-isolamento-execucao/iteration-3.md) e [decisões experimentais](../../specs/004-isolamento-execucao/i3-design-decisions.md) ANTES do código. O primeiro incremento é fila persistente e broker interno offline, com gate desativado por padrão, apenas fixtures sintéticas; nenhum serviço público/worker/VM é iniciado. Autenticação real, ledger completo, recuperação e I4/I5 continuam pendentes. A mera criação da branch não comprova testes nem fecha I3.

## Resultado da primeira implementação I3-01 (2026-10-10)

PR [#23](https://github.com/thalesvalente/project-robocopa-ifma/pull/23) em branch própria `feat/s04-i3-control-plane`. Planner Spec Kit publicado ANTES do código. Broker interno sem rede/worker/Docker e fila SQLite de **laboratório** com atomicidade, idempotência, capacidade persistida por arquivo, gate OFF e simulação explicitamente não autenticada de worker. F01/F02 corrigidos e documentados, 26 testes novos e 346 testes de seis suítes PASS fora do CI. Seis workflows do head `4d89fc5` com success, incluindo duas batalhas reais e cleanup de I2. Artifact I2 auditado fora do runner. [Relatório I3-01](../qualidade/evidencias/S04-T04-I3-01.md). **I3-01 concluído somente no G-EXP; I3 completo EM_EXECUCAO; Q-07 aberta; macro S04-T04 EM_EXECUCAO; S00-T06 e G-PROD BLOQUEADOS.** Nenhum usuário real, endpoint público, VM local, autenticação real ou pontuação foi processado.

## I3-02 — planejamento específico antes da implementação (2026-10-10)

Em branch empilhada `feat/s04-i3-02-mtls-identity` sobre PR #23: [plano](../../specs/004-isolamento-execucao/i3-02-auth-plan.md), [contrato](../../specs/004-isolamento-execucao/contracts/worker-channel.md) e decisões experimentais publicados ANTES do código. A hipótese de canal é mTLS TLS1.3 worker→broker com certificados sintéticos de CI, sem transitar job ou liberar worker real. Q-07 continua aberta para produção e a tarefa macro S04-T04 EM_EXECUCAO; G-PROD BLOQUEADO. A prova I3-02 ainda não foi executada nesta linha de planejamento.
