# I2 — resultados da revisão previamente planejada

**Plano anterior ao código:** [i2-audit-plan.md](i2-audit-plan.md), commit69ee9c9. **Fonte do lote de referência:**9dd75a8, [run38048459272](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38048459272), aprovado. Este registro refere-se à engenharia do recorte, não homologação dos controles públicos.

| Item planejado | Implementação e evidência | Estado no recorte |
|---|---|---|
| H01 | `arena_evidence.py` e CLI somente leitura: esquema/tipos, IDs, eventos ordenados, replay/resultado, flags obrigatórias, limites de gzip e arquivos; negativos de mutação e artifact real relido | CONCLUÍDO |
| H02 | `arena_policy.py`: conjunto de redes anexadas exatamente permitido, sem IPv6 inesperado; 24 invariantes por papel e namespaces distintos do host observados | CONCLUÍDO |
| H03 | `SessionBudget` e gateway: orçamentos cumulativos de mensagens/entrada/saída, inatividade e vida total. Unitários com relógio controlado; testes de transporte real com engine falso para mensagens/idle/saída; jogo real preservado | CONCLUÍDO no experimento, não rate-limit de produção |
| H04 | Manifesto de lote, cleanup por ownership e duas falhas Docker reais `after_containers/after_ready`, sem órfãos; fixture de build parcial. Correção adicional testada: daemon indisponível não pode significar imagem inexistente | CONCLUÍDO para esses cenários, não vinte ciclos/recovery durável |
| H05 | 19 verificações por bot nas duas partidas; canários positivos host/peer ativos e 6 rejeições na ACL de saída de cada bot | CONCLUÍDO |
| H06 | Reuso do PR19 em vez de terceira implementação, N5 confirmado na fonte e prova benigna, NOTICE/README, relatório `.md`/`.json`, tasks/estado e PR reconciliados; sem claims de alunos/VM segura | Registro concluído; resultado do último commit deve ser confirmado no CI |

A fonte9dd75 registra286 testes automatizados; a correção de cleanup acrescenta1. Lote histórico preservado sem trocar seus placares pelos de regressões seguintes. O verificador de evidência foi executado novamente fora do CI sobre os bytes baixados; não houve auditoria por organização independente.

**Continuidade:** I3 precisa detalhar contratos/autorização/fila/ledger e recuperação antes de implementar qualquer lacuna. A prova de rede/árbitro no CI não substitui I4/VM real e I5/revisão operacional. Os39 itens T amplos e18 gates continuam pendentes conforme seu aceite integral.
