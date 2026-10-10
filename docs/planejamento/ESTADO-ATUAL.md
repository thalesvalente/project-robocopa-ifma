# Estado atual — pesquisa, autoria e isolamento de robôs/árbitro

**Atualizado:** 2026-10-10. **Trabalho corrente:** S04-T04 em EM_EXECUCAO; I1 e o recorte I2 possuem código e provas em CI descartável. VM dedicada aprovada como direção, mas não instalada/testada no host. Sem liberação para alunos.

## Repositório e decisões

PRs empilhados: #11 fundação/Spec Kit; #12 Compose; #13 motor de referência; #14 autoria; #16 especificação; #17 pesquisa/I1; **#19 I2 com árbitro e bots separados**, branch `feat/s04-i2-separated-arena`, base #17. Não houve merge na main.

A revisão ampliada encontrou rascunhos I2 prévios em #18 e #19. A continuação reaproveitou #19 e auditou o que já existia. #18 foi preservado sem alteração. #20, criado apenas com plano/coleta de fonte antes de detectar a sobreposição, foi encerrado sem merge para não manter terceira implementação concorrente.

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
