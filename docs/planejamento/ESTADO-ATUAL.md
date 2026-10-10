# Estado atual — fundação, motor e laboratório de autoria

**Plano operacional:** 0.1.1 · **Trabalho técnico corrente:** S04-T03, candidato de autoria com CI aprovado e aceite físico pendente. Evidências deste avanço são registradas na feature 003; os gates formais anteriores continuam abertos.

## Fundação e acompanhamento

Leitura/escrita no GitHub confirmadas. Commit inicial `1cbc58a3a8c7c958c35b071332fbb8a5f0a5a1ae`; base `02924287f87c48f114fc153fcf31d722c3a765e6`. PR #11 contém governança e planejamento; PRs #12, #13 e #14 são incrementos empilhados. Não foi realizado merge na main por esta rodada.

O Spec Kit está fixado em v1.1.2 / `959e866caa3618bf3dc290d5dca33394365af9c6`, integração generic. Bootstrap no run https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842; commit `51ee9727d8eda0f58c471262abcfc9d50eaeebb2`. A ferramenta é utilizada por arquivos/scripts versionados; não é uma conexão MCP nativa da conversa.

O backlog JSON continua canônico para 10 sprints e 60 tarefas, com visões geradas por `scripts/render_planning.py`. S00-T01–T05 foram concluídas tecnicamente; S00-T06 aguarda ratificação humana. A tarefa macro S04-T02 permanece EM_REVISAO. A execução preparatória de S04-T03 não encerra o aceite físico, a revisão pedagógica ou seus pré-requisitos; os avanços verificáveis da feature 003 estão em `specs/003-autoria-mobile/tasks.md`. Não confundir entrega técnica parcial com encerramento da sprint.

## Descoberta, BMC, projeto e requisitos

Há 12 minutas S01/S02 (índice em `docs/descoberta/README.md`), sem pesquisa de campo ou aprovação institucional presumida. A baseline completa S03 e a arquitetura integral continuam sem homologação. A autorização de continuar experimentos não aprova automaticamente essas entregas.

## Infraestrutura local confirmada

PR #12: Docker Compose privado, PostgreSQL 17, sonda local, preflight e feature 001. A execução no Windows foi realizada pelo responsável e confirmada com serviços healthy e resposta /health; `docs/qualidade/evidencias/INFRA-LOCAL-HOST.md`. O assistente não possui sessão remota no host. A mudança de unidade da pasta Git não comprova migração do VHDX do Docker.

## Motor real e reprodução no Windows

PR #13: Tank Royale 1.4.0, Battle Runner JVM, amostras oficiais, checksums e imagem isolada. No lote CI https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38004097096: 63 testes unitários OK e duas batalhas de cinco rounds. Walls/Spin Bot: 495/229 e 465/141. Replays e resultados do CI foram inspecionados.

O responsável **também reproduziu o spike no Windows**: Walls 391 × Spin Bot 364, cinco rounds, 5255 ticks, 10718ms, término PASS no run `20261010T001533Z-5709ce1f`. Fonte: saída PowerShell compartilhada; `docs/qualidade/evidencias/TANK-ROYALE-HOST.md`. Os arquivos de manifesto/replay dessa execução local não foram anexados; não foi feita inspeção independente de seus bytes. A frase antiga que dizia faltar reprodução do motor no host está superada por essa evidência.

## Autoria responsiva com motor real

PR #14 (`feat/s04-mobile-authoring`, base #13): editor HTML/CSS/JS, RoboDSL candidata em português, rascunho no navegador, validação por linha, treino local e replay resumido. A DSL permite ações ordenadas e condições; não apenas aparência. Nenhum Java/JavaScript livre recebido da interface é executado.

Lote de referência https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38009658981, fonte `6c101094b75f212de5f65719234fd74614f29e51`: **97 testes unitários OK**, Spec Kit nativo PASS e dois treinos reais disparados pela UI em Chromium com viewport 390×844. Três viewports validados (360/390/1280), rascunho recuperado, erros preservados, sem overflow horizontal e sem erros JavaScript.

Aprendiz/sentinela: 44 × Walls 449, velocidade média 0. Aprendiz/explorador: 124 × Walls 243, velocidade média 5,7989. Cada treino teve três rounds. Artifact baixado e conferido quanto a hashes, replay oficial, placar final e métricas; screenshots reais desktop/móvel inspecionados. Evidência estruturada `docs/qualidade/evidencias/AUTORIA-MOBILE-CI.json`; análise `docs/arquitetura/spike-autoria.md`.

A execução em Chromium emulado **não é teste em telefone físico**. O responsável compartilhou posteriormente uma captura da interface funcionando no PC, com Sentinela e resultado exibido de **Aprendiz 536 × Walls 226** em três rounds, replay no último round e velocidade média 0. Evidência visual e ressalvas em `docs/qualidade/evidencias/AUTORIA-MOBILE-HOST.md`. Em segunda captura no PC, o **Explorador** também apresentou batalha concluída: Aprendiz 188 × Walls 188, velocidade média 5,47, movimento em 94,3% dos turnos; painel mostra Walls 1º e Aprendiz 2º apesar do empate nos pontos exibidos. É uma questão de classificação a investigar antes da S03-T03. Ambas as capturas foram resumidas em `docs/qualidade/evidencias/AUTORIA-MOBILE-HOST.md`; replay/manifesto locais não foram anexados nem auditados independentemente. O serviço permanece em `127.0.0.1:18081`; não modifica o Compose existente. Manual: `spikes/autoria-mobile/README.md`.

## Limites e próximos aceites

MOB-008: os dois exemplos e seus resultados foram observados por capturas no PC, demonstrando diferença expressiva de movimento. Ainda faltam edição própria, revisão dos arquivos locais, teste em smartphone físico por conexão controlada previamente autorizada e ratificação pedagógica. MOB-009: revisar a candidata RoboDSL com finalidade pedagógica e reconciliar a escolha à baseline. S04-T04: ensaios de isolamento para código não confiável ainda não realizados. Não há contas de estudantes, inscrição, fila durável, competição administrável ou MVP entregue.

Nenhum roteador, firewall, DNS, túnel, VHDX ou serviço de outro projeto foi alterado. O servidor de laboratório tem acesso local à CLI Docker; as verificações de Host/Origin/token não o tornam seguro para exposição pública. Backups, restauração, acesso externo e capacidade real sob carga continuam pendentes. Não foi usado Codex nem R4 nesta rodada.
