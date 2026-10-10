# Tarefas técnicas — Feature 003 / S04-T03

**Resultado:** protótipo técnico verificado no CI. Macro S04-T03 continua aberta; aparelho físico e ratificação pendentes. Os checks abaixo não são aceite global da sprint.

- [x] MOB-001 Registrar a reprodução S04-T02 pelo responsável: Walls 391 × Spin Bot 364 em cinco rounds; não houve inspeção independente do replay/manifesto não anexados. Evidência: `docs/qualidade/evidencias/TANK-ROYALE-HOST.md`.
- [x] MOB-002 Implementar RoboDSL candidata: parser, limites, erros de linha, AST/hash e compilação por template fixo.
- [x] MOB-003 Criar editor responsivo, rascunho local, botões de inserção e mensagens recuperáveis.
- [x] MOB-004 Ligar o treino local a contêiner descartável e capturar BattleResults/replay com vínculo de versão.
- [x] MOB-005 Executar unitários: 34 testes de autoria e 63 anteriores no lote de referência, 97 OK. Regressão adicional de token não ASCII adicionada posteriormente.
- [x] MOB-006 Executar duas estratégias pela UI e conferir artifacts reais: três rounds por treino; sentinela velocidade média 0; explorador 5,7989. Logs/resultados/replays e onze controles efetivos Docker por execução conferidos.
- [x] MOB-007 Validar Chromium nos viewports 360/390/1280px; rascunhos recuperados, erros preservados, layout sem overflow e screenshots reais inspecionados. **Emulação**, não aparelho físico.
- [ ] MOB-008 Reproduzir o novo laboratório no Windows e avaliar em smartphone físico, com conexão controlada autorizada. **Parcial:** duas capturas compartilhadas pelo responsável demonstram editor/replay no PC, Sentinela (Aprendiz 536 × Walls 226, 3 rounds, velocidade 0) e Explorador (Aprendiz 188 × Walls 188, 3 rounds, velocidade 5,47, movimento 94,3%). Evidência `docs/qualidade/evidencias/AUTORIA-MOBILE-HOST.md`. Ainda pendentes: teste de edição livre, arquivos locais não inspecionados, teste em celular físico e ratificação pedagógica. Empate na pontuação exibida com ranks 1/2 exige investigação antes de fechar as regras da competição.
- [ ] MOB-009 Ratificar escolha pedagógica da autoria e reconciliar com a baseline S03/S04; nenhuma aprovação presumida.

Evidência do lote: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38009658981 e `docs/qualidade/evidencias/AUTORIA-MOBILE-CI.json`. Fonte testada `6c101094b75f212de5f65719234fd74614f29e51`. Não houve uso de Codex/R4, inscrições, participantes reais, modificação do Compose ou abertura de rede.
