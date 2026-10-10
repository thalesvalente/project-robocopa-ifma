# Tarefas técnicas — Feature 002 (S04-T02)

**Resultado técnico:** PASS. **Estado da tarefa macro:** EM_REVISAO; não encerra os gates S03/S04.

- [x] TR-001 [US1] Verificar release, API JVM, bots oficiais, licença e hashes. Evidência: `spikes/tank-royale/upstream.lock.json`, `NOTICE.md` e fontes de `docs/arquitetura/spike-motor.md`.
- [x] TR-002 [US1] Implementar wrapper Java com resultados oficiais, eventos e gravação de replay. Compilação e uso real confirmados no CI.
- [x] TR-003 [US2] Criar imagem/executor descartável sem rede externa, mounts ou credenciais do host. Onze controles efetivos verificados por `docker inspect` em cada execução.
- [x] TR-004 [US3] Implementar validações, timeout configurado, saída por execução e limpeza restrita. Transporte stdout preserva bytes antes do encerramento do tmpfs; não é teste completo de abuso.
- [x] TR-005 [US3] Executar 23 testes unitários do spike; regressão adicional de 27 testes de planejamento e 13 de infraestrutura, total 63 OK no CI.
- [x] TR-006 [US1/US3] Executar e conferir duas batalhas reais, cinco rounds cada, pontuações e replays. Run: https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38004097096. Placares Walls/Spin Bot: 495/229 e 465/141. Não exigir placar idêntico nas repetições.
- [x] TR-007 [US3] Registrar evidência e atualizar S04-T02 para EM_REVISAO sem encerrar gates. Arquivos: `docs/qualidade/evidencias/TANK-ROYALE-CI.json`, `docs/arquitetura/spike-motor.md`, backlog e projeções.
- [x] TR-008 [US2] Responsável reproduziu no Windows com Docker: cinco rounds, Walls 391 × Spin Bot 364, 5255 ticks, 10718ms e término PASS. Evidência fornecida no terminal: `docs/qualidade/evidencias/TANK-ROYALE-HOST.md`. Os bytes de manifesto/replay desse run não foram anexados nem inspecionados independentemente nesta conversa.

O artifact real do CI foi baixado e conferido: hashes, gzip, eventos JSON e resultado final do replay concordam com `results.json`. Isso não autoriza executar submissões de estudantes; sandbox pertence à S04-T04. A reprodução do host acrescenta a evidência de término informado, sem substituir a inspeção dos artifacts locais ausentes.
