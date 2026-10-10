# Estado atual — fundação, laboratório local e prova do motor

**Data:** 2026-10-09 · **Plano operacional:** 0.1.1 · **Trabalho corrente:** S04-T02 em revisão; gates anteriores pendentes.

## Publicação e execução confirmadas

Leitura e escrita no GitHub funcionaram. O repositório estava vazio. Commit inicial: `1cbc58a3a8c7c958c35b071332fbb8a5f0a5a1ae`. A base foi publicada em `02924287f87c48f114fc153fcf31d722c3a765e6`, na branch `chore/s00-fundacao-speckit`. A `main` permanece somente com a inicialização, até revisão e integração das branches.

A execução real do Spec Kit terminou com sucesso no GitHub Actions: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842. O commit de geração é `51ee9727d8eda0f58c471262abcfc9d50eaeebb2`. O toolkit está fixado em v1.1.2 / `959e866caa3618bf3dc290d5dca33394365af9c6`, integração generic e scripts Python.

O manifesto em `docs/qualidade/evidencias/SPECKIT-CI.json` registra 36 arquivos sob `.specify` e `.agents`, incluindo a constituição própria preservada. A validação do backlog e os 16 testes iniciais de planejamento/preservação foram executados naquele run. O ambiente foi GitHub-hosted Ubuntu, não a máquina que hospedará o MVP.

## Backlog e acompanhamento

10 sprints e 60 tarefas macro estão publicadas, com dependências, artefatos, executores e critérios de aceite. Issues #1 a #10 espelham as sprints; correspondência em `issues-map.json`.

S00-T01 a S00-T05 estão concluídas tecnicamente com evidência. Inventários v1/v2/v3 e verificações Docker/WSL fornecidos pelo responsável confirmaram hardware e execução de contêineres: `docs/operacao/inventario-sanitizado.md`. S00-T06 continua **BLOQUEADA**, aguardando ratificação detalhada da constituição, plano e riscos. A sprint S00 não está homologada.

**S04-T02 está EM_REVISAO.** O responsável autorizou antecipar o experimento de motor; duas batalhas reais e replays foram validados em CI. A dependência formal S04-T01/S03 não foi encerrada artificialmente. Registro: `decisoes/D-002-spike-antecipado.md`. O backlog JSON e as visões geradas contêm o mesmo estado/evidência.

## Entregas de conteúdo preparadas

Foram redigidas 12 minutas ligadas a S01/S02: problema, jornadas, referências, ideação, BMC, hipóteses, projeto, recursos/custos, plano pedagógico, governança/riscos, pitch e revisão de coerência. Entrada: `docs/descoberta/README.md`; registro em `entregas-preparatorias.json`.

Esses documentos não comprovam entrevistas, validação de campo ou aprovação institucional. Requisitos detalhados e arquitetura final do produto ainda não estão homologados.

## Verificação contínua

O workflow `planejamento.yml` verifica projeções, testes, minutas, links e pré-requisitos da feature 000. `infra-local.yml` verifica o laboratório Compose. `tank-spike.yml` executa regressão de planejamento/infra, contratos do motor, pré-requisitos nativos da feature 002 e duas batalhas reais. São runners GitHub-hosted; CI não é uma sessão remota na máquina pessoal.

## Infraestrutura local confirmada

PR #12 (`feat/infra-local-compose`, baseado no PR #11) contém ADRs candidatos, Compose privado, PostgreSQL 17, sonda HTTP, credenciais locais, preflight e feature 001. CI: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38001273168. Evidência: `docs/qualidade/evidencias/INFRA-LOCAL-CI.md`.

O laboratório **foi iniciado e verificado no Windows pelo responsável**: PostgreSQL e sonda saudáveis, volume/redes criados e resposta local `/health` correta. Evidência separada: `docs/qualidade/evidencias/INFRA-LOCAL-HOST.md`. O caminho do repositório mudou para outra unidade; isso não comprova migração do VHDX Docker.

## Motor real confirmado no CI

PR #13 (`feat/s04-tank-royale-spike`, baseado no PR #12) contém Tank Royale 1.4.0 fixado, Battle Runner JVM, dois bots oficiais e comando Python de execução isolada. Lote de referência: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38004097096.

**63 testes unitários OK** (27 planejamento, 13 infraestrutura, 23 spike), Spec Kit nativo PASS e **duas batalhas reais de cinco rounds**. Walls/Spin Bot: 495/229 e 465/141. Replays e resultados foram baixados e comparados; onze controles efetivos Docker passaram em cada execução. Evidência: `docs/qualidade/evidencias/TANK-ROYALE-CI.json`; análise em `docs/arquitetura/spike-motor.md`.

O código do spike **ainda não foi executado no Windows do responsável**. Instruções em `spikes/tank-royale/README.md`; a execução requer apenas Docker Linux e Python já disponíveis, sem alterar o Compose.

## Limites explícitos

O assistente não estabeleceu acesso remoto ao computador pessoal. O próprio responsável executou o laboratório local; as batalhas desta rodada ocorreram no GitHub. Não foram alterados roteador, firewall, DNS, túneis ou serviços de outros projetos.

Existe uma prova real do motor, mas ainda não há portal de alunos, autoria móvel, fila integrada, competição administrável, sandbox validado para código hostil, piloto ou MVP entregue. Não foi usado Codex nem R4 nesta rodada. Spec Kit é utilizado pelos arquivos e scripts do projeto, não por uma conexão MCP nativa com esta conversa.

## Próximos aceites

Reproduzir o spike no Windows, registrar sua evidência separadamente e revisar o PR. Manter em paralelo a ratificação da base/requisitos. Os próximos experimentos previstos são autoria pelo celular e isolamento de código de participantes, sem abrir acesso externo. Backup, local físico do VHDX e hospedagem pública continuam pendentes.
