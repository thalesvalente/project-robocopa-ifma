# Estado atual — primeira rodada de execução

**Data:** 2026-10-09 · **Plano operacional:** 0.1.1 · **Sprint corrente:** S00.

## Publicação e execução confirmadas

Leitura e escrita no GitHub funcionaram. O repositório estava vazio. Commit inicial: `1cbc58a3a8c7c958c35b071332fbb8a5f0a5a1ae`. A base foi publicada em `02924287f87c48f114fc153fcf31d722c3a765e6`, na branch `chore/s00-fundacao-speckit`. A `main` permanece somente com a inicialização, até revisão e integração da branch.

A execução real do Spec Kit terminou com sucesso no GitHub Actions: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842. O commit de geração é `51ee9727d8eda0f58c471262abcfc9d50eaeebb2`. O toolkit está fixado em v1.1.2 / `959e866caa3618bf3dc290d5dca33394365af9c6`, integração generic e scripts Python.

O manifesto em `docs/qualidade/evidencias/SPECKIT-CI.json` registra 36 arquivos sob `.specify` e `.agents`, incluindo a constituição própria preservada. A validação do backlog e os 16 testes de planejamento/preservação foram executados com sucesso nesse run. O ambiente foi GitHub-hosted Ubuntu, não a máquina que hospedará o MVP.

## Backlog e acompanhamento

10 sprints e 60 tarefas macro estão publicadas, com dependências, artefatos, executores e critérios de aceite. Foram criadas as issues #1 a #10, uma por sprint e seis tarefas por issue; correspondência em `issues-map.json`.

S00-T01 a S00-T04 estão concluídas tecnicamente com evidência. S00-T05 está bloqueada pelo inventário real da máquina alvo. S00-T06 aguarda as entradas e a ratificação detalhada do responsável. A sprint S00, como um todo, não está homologada.

## Entregas de conteúdo preparadas

Foram redigidas 12 minutas ligadas a S01/S02: problema, jornadas, referências, ideação, BMC, hipóteses, projeto, recursos/custos, plano pedagógico, governança/riscos, pitch e revisão de coerência. Entrada: `docs/descoberta/README.md`. O inventário de preparação está em `entregas-preparatorias.json`.

Esses documentos permitem revisão de conteúdo sem fingir que entrevistas, validação de campo, dependências ou aprovação institucional foram concluídas. Os estados macro continuam no backlog. Requisitos detalhados, arquitetura validada e implementação do produto ainda não foram entregues.

## Verificação contínua adicional

O workflow `planejamento.yml` verifica projeções, testes, minutas, links locais e pré-requisitos nativos do Spec Kit para a feature 000. Ele é somente leitura e não reinstala o toolkit nem altera o repositório. Seu resultado deve ser consultado no run do commit em revisão; a existência do workflow não é prova de sucesso futuro.

## Limites explícitos

Nenhum acesso remoto ao computador do responsável foi estabelecido; nada foi instalado nele; nenhuma porta, túnel ou serviço foi aberto. Não existe ainda aplicação MVP, teste do motor, piloto ou implantação. Não foi usado Codex. A integração do Spec Kit é pelos arquivos e scripts reais do projeto, não uma conexão MCP nativa desta conversa.

A tentativa inicial de bootstrap no ambiente desta conversa falhou por DNS. A alternativa de execução no GitHub foi concluída e verificada, sem transferir essa conclusão para o host local.

## Próxima dependência

Verificar inventário sanitizado na máquina alvo e revisar constituição/escopo. O coletor `scripts/collect_host_inventory.py` grava apenas dados técnicos básicos em `.local/inventory.json`, ignorado pelo Git; revisar antes de compartilhar. Nenhuma alteração de infraestrutura está embutida nessa coleta.
