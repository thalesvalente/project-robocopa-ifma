# Checklist de aceite técnico — Feature 002

Evidência-base: CI 38004097096 e `docs/qualidade/evidencias/TANK-ROYALE-CI.json`.

| Critério | Evidência / resultado |
|---|---|
| US1: motor oficial e versão identificados | 1.4.0; release, commit, tamanho e SHA-256 fixados e validados |
| US1: dois bots de referência | Walls v1.0 e Spin Bot v1.0; sem fontes de alunos |
| US1: cinco rounds concluídos | Duas execuções, com eventos 1–5 e resultado final |
| US1: pontos do motor e replay | BattleResults exportado; replay oficial preservado e conferido |
| US2: runtime sem acesso externo/host | Onze controles efetivos Docker verificados; nenhum bind ou porta publicada |
| US2: execução reproduzida no Windows | PENDENTE; comando entregue no README |
| US3: tratamento de erro | Falhas iniciais registradas como FAILED; testes de contrato/artefatos aprovados |
| US3: limite temporal | Configurado (watchdog Java e timeout Python); esgotamento deliberado não ensaiado |
| US3: diretório único e limpeza | Duas pastas distintas e cleanup_completed=true |
| Governança | Macro EM_REVISAO; nenhuma aprovação global presumida |

Análise de consistência: spec, plan, tasks, lock e implementação usam a mesma versão 1.4.0, cinco rounds e duas identidades oficiais. O diretório SpinBot não é confundido com o nome exibido Spin Bot. Fixtures unitárias não alimentam os resultados reais. Checksums e imagem executada são registrados; não se promete placar determinístico nem segurança contra código hostil.
