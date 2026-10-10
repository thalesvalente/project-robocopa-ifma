# S04-T04 / I2 — Plano de reconciliação antes de I3

**Data:** 2026-10-10. **Estado:** PLANEJADO; nenhum aceite novo presumido.
**Solicitação:** documentar o plano, executá-lo e eliminar pendências do recorte I2 antes de começar I3.
**Rastreabilidade:** [iteration-2.md](iteration-2.md), [i2-audit-plan.md](i2-audit-plan.md), [tasks.md](tasks.md), [plan.md](plan.md). Macro S04-T04 permanece EM_EXECUCAO.

## Baselines congeladas e preservação

- Base comum I1 / PR #17: `668d82b034cf5e0fab909e13552399c2de7213d5`.
- PR #19: `3f1b4950ccf229ad90ff27b3636575aad0ca5c57`, `feat/s04-i2-separated-arena`.
- PR #21: `583fe580b69f29931c90d66abbc0fd2571a4ff86`, `feat/s04-i2-referee-isolation`.
- Rascunho anterior PR #18 também será inventariado: `e94ac97ff7c3f16b7b7a4a3b38d41df640251ff8`, `feat/s04-judge-bot-isolation`. PR #20 já encerrado sem merge.

Usar #19 como área de reconciliação, sem criar terceira implementação concorrente. A escolha técnica final será registrada após ler código, testes e evidências de todas as alternativas. Não fazer merge cego das arquiteturas. Preservar commits/branches históricos; sem force push, sem merge em main e sem encerrar gates de produção.

## Escopo e limites imutáveis

Somente RoboDSL básica planejada para MVP; neste I2 executar apenas bots oficiais conhecidos. G-EXP: GitHub-hosted Ubuntu descartável. Não modificar Windows/WSL/Docker Desktop, VM pessoal, rede residencial, .env, Compose, Postgres, firewall/roteador/VHDX ou serviços do responsável. Sem endpoint público, aluno, credencial real ou executor self-hosted. I3 não será implementado nesta rodada.

A auditoria local de fonte/artefatos é somente leitura e os testes locais não iniciam Docker nem bots. Se necessário, exportar arquivos rastreados dos SHAs acima por workflow temporário de leitura, sem credencial persistida e sem publicar segredos. Remover o coletor temporário ao encerrar.

## Sequência e tarefas de reconciliação

- [ ] R01 [US5] Inventariar código, planos, workflows, reviews, pendências e evidências dos PRs #18/#19/#21 e confirmar SHAs/base comum. T003/T004/T037/T039; FR-018/019/020; TH-01/14/15.
- [ ] R02 [US2] Escrever matriz comparativa e decisão em `i2-reconciliation-decision.md` ANTES de alterar runtime: fronteiras de confiança, rede efetiva, papéis, segredos, mensagens, limites, evidências e cleanup. Cada diferença recebe decisão preservar/portar/rejeitar com justificativa. T007/T019/T020/T022; FR-005/006/007/012/018; TH-02/03/04/05/09/10/15.
- [ ] R03 [US2] Auditar gateway/handshake e mensagens pós-handshake: tipos/campos, sessão/identidade/token, comandos administrativos antes/depois, mensagens inválidas/duplicadas, limites cumulativos, conexões, timeout, encaminhamento e desligamento. Planejar cada lacuna adicional antes do patch. T019/T020/T021/T024; FR-005/006/009/012/018; TH-04/05/07/08/09/15.
- [ ] R04 [US2] Auditar rede e política aplicada: bot→árbitro permitido exclusivamente pelo gateway; acesso bruto por IP/DNS/IPv6 e host/pares negado com controles positivos; namespaces e recursos inspecionados antes de payload; falhas abortam sem fallback. T018/T019/T021/T022; FR-005/006/007/018; TH-02/03/04/05/15.
- [ ] R05 [US3] Auditar provisionamento, captura limitada, duas batalhas e abortos parciais; falha de daemon não significa ausência de recurso; cleanup somente owned e verificável. Provar casos ainda ausentes antes de fechar. T024/T025/T026(recorte)/T034; FR-009/010/016/019; TH-07/08/12/14.
- [ ] R06 [US4] Validar auditor/manifestos: hash, gzip, eventos oficiais, rounds/IDs/placar, origem, tipos, flags e vínculo à fonte; preservar lotes históricos sem reescrever placares. Classificar gravação de eventos versus replay nativo e auditoria própria versus independente. T020/T029/T031/T032; FR-011/012/014/015/018; TH-10/12/13/15.
- [ ] R07 [US2] Implementar somente correções aprovadas em R02–R06 e portar regressões úteis, mantendo uma única arquitetura executável canônica. Cada achado terá teste de reprodução/negativo e evidência de correção. Não carregar duplicação desnecessária nem ampliar para TeamMessage/novas features sem requisito. T007/T019/T020/T037.
- [ ] R08 [US4] Reexecutar todas as suítes (planejamento, infraestrutura, motor, autoria, segurança e transportes); verificadores de backlog/projeções/Spec Kit; CI I1, editor/navegador/motor e I2 (duas batalhas reais de três rounds + dois abortos). Baixar artefatos, conferir bytes/eventos fora do runner e atribuir resultados ao commit exato. T026(recorte)/T029/T036(recorte)/T037; FR-012/015/018/019.
- [ ] R09 [US5] Reconciliar `iteration-2.md`, `tasks.md`, `plan.md`, esclarecimentos/estado e evidências em `docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md` e `.json`. Criar registro verificável de pendências I2 com severidade, responsável, teste e estado; separar explicitamente I3/I4/I5, sem empurrar lacuna I2 para o futuro. Atualizar PR #19 e marcar alternativas superadas/encerradas sem excluir branches após verificar cobertura. T035/T039(recorte); FR-018/019/020.
- [ ] R10 [US5] Executar gate final fail-closed: R01–R09 concluídos, zero achado I2 aberto/inconclusivo, artefatos auditados e CI final aprovado, revisão threads tratada, uma base canônica. Se qualquer critério falhar, registrar I2 BLOQUEADO e não iniciar I3. T036/T037/T039(recorte); FR-018/019/020.

## Critérios de saída e não equivalência

I2 somente poderá ser declarado FECHADO_NO_ESCOPO_EXPERIMENTAL com matriz de critérios preenchida, nenhuma pendência I2 aberta, evidências reais e regressões aprovadas. Fechar o recorte não homologa S04-T04 integral, G-PROD, revisão independente, VM real, vinte ciclos de operação nem segurança absoluta. Broker/fila/ledger/idempotência durável pertencem a I3; host/VM a I4; capacidade, vinte ciclos, backup/restauração e homologação a I5, como já previsto antes desta reconciliação. Qualquer requisito funcional de isolamento I2 sem prova permanece aqui e bloqueia a saída.

## Reprodutibilidade e ordem

Este documento deve estar em commit remoto anterior às correções. R01→R02→R03–R06 (adendos antes de código)→R07→R08→R09→R10. Resultados serão registrados em documento separado, com commits/runs/artefatos e limitações reais. Não marcar PASS por workflow enfileirado, por número de testes ou por memória de conversa.
