# Estado atual — fundação e experimento de infraestrutura local

**Data:** 2026-10-09 · **Plano operacional:** 0.1.1 · **Sprint corrente:** S00.

## Publicação e execução confirmadas

Leitura e escrita no GitHub funcionaram. O repositório estava vazio. Commit inicial: `1cbc58a3a8c7c958c35b071332fbb8a5f0a5a1ae`. A base foi publicada em `02924287f87c48f114fc153fcf31d722c3a765e6`, na branch `chore/s00-fundacao-speckit`. A `main` permanece somente com a inicialização, até revisão e integração da branch.

A execução real do Spec Kit terminou com sucesso no GitHub Actions: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842. O commit de geração é `51ee9727d8eda0f58c471262abcfc9d50eaeebb2`. O toolkit está fixado em v1.1.2 / `959e866caa3618bf3dc290d5dca33394365af9c6`, integração generic e scripts Python.

O manifesto em `docs/qualidade/evidencias/SPECKIT-CI.json` registra 36 arquivos sob `.specify` e `.agents`, incluindo a constituição própria preservada. A validação do backlog e os 16 testes de planejamento/preservação foram executados com sucesso nesse run. O ambiente foi GitHub-hosted Ubuntu, não a máquina que hospedará o MVP.

## Backlog e acompanhamento

10 sprints e 60 tarefas macro estão publicadas, com dependências, artefatos, executores e critérios de aceite. Foram criadas as issues #1 a #10, uma por sprint e seis tarefas por issue; correspondência em `issues-map.json`.

S00-T01 a S00-T05 estão concluídas tecnicamente com evidência. Inventários v1/v2/v3 e verificações Docker/WSL fornecidos pelo responsável confirmaram hardware e execução de contêineres, registrados de forma sanitizada em `docs/operacao/inventario-sanitizado.md`. S00-T06 continua **BLOQUEADA**, aguardando a ratificação detalhada da constituição, plano e riscos pelo responsável. A sprint S00 não está homologada. A sprint S00, como um todo, não está homologada.

## Entregas de conteúdo preparadas

Foram redigidas 12 minutas ligadas a S01/S02: problema, jornadas, referências, ideação, BMC, hipóteses, projeto, recursos/custos, plano pedagógico, governança/riscos, pitch e revisão de coerência. Entrada: `docs/descoberta/README.md`. O inventário de preparação está em `entregas-preparatorias.json`.

Esses documentos permitem revisão de conteúdo sem fingir que entrevistas, validação de campo, dependências ou aprovação institucional foram concluídas. Os estados macro continuam no backlog. Requisitos detalhados, arquitetura validada e implementação do produto ainda não foram entregues.

## Verificação contínua adicional

O workflow `planejamento.yml` verifica projeções, testes, minutas, links locais e pré-requisitos nativos do Spec Kit para a feature 000. Ele é somente leitura e não reinstala o toolkit nem altera o repositório. Seu resultado deve ser consultado no run do commit em revisão; a existência do workflow não é prova de sucesso futuro.

## Limites explícitos

Nenhum acesso remoto ao computador do responsável foi estabelecido; nada foi instalado nele; nenhuma porta, túnel ou serviço foi aberto. Não existe ainda aplicação MVP, teste do motor, piloto ou implantação. Não foi usado Codex. A integração do Spec Kit é pelos arquivos e scripts reais do projeto, não uma conexão MCP nativa desta conversa.

A tentativa inicial de bootstrap no ambiente desta conversa falhou por DNS. A alternativa de execução no GitHub foi concluída e verificada, sem transferir essa conclusão para o host local.

## Experimento de infraestrutura em branch empilhada

PR #12 (`feat/infra-local-compose`, base PR #11) contém ADRs candidatos, Compose privado e sonda HTTP, PostgreSQL 17 persistente, scripts de credenciais e preflight, testes, manual Windows e specs da feature 001. Execução confirmada no CI: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38001273168 (**13 testes OK**, Compose, sonda, persistência após recriação). Evidência: `docs/qualidade/evidencias/INFRA-LOCAL-CI.md`. **Não** equivale a implantação no Windows, segurança de execução de bots, aceite de arquitetura ou conclusão de S04/S08. O laboratório não inicia um jogo.

## Próxima dependência

Revisar e ratificar constituição/escopo e executar voluntariamente o laboratório local após conferir `docs/operacao/COMPOSE-LOCAL.md`. O coletor `scripts/collect_host_inventory.py` já produziu inventário v3 no host, com JSON mantido fora do Git. Nenhuma alteração de rede no host foi feita pelo ChatGPT. A execução do novo Compose **no Windows** permanece pendente.
