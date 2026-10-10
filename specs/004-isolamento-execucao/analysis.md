# Specification Analysis Report — Feature 004 (pré-implementação)

**Data:** 2026-10-09 · **Análise:** leitura crítica cruzada de `spec.md`, `clarifications.md`, `research.md`, `plan.md`, `tasks.md`, modelo de dados, contrato, ADR-004 e constituição.  
**Estado:** análise documental equivalente ao fluxo `speckit.analyze`. **Não afirma invocação interativa nativa dos comandos slash nesta conversa.** A checagem automática dos IDs/cobertura será executada no CI; não confundir análise sintática com aprovação.

## Findings

| ID | Categoria | Severidade | Referência | Problema e tratamento |
|---|---|---|---|---|
| A-001 | Constituição/gate | CRÍTICA (bloqueio de aprovação, não defeito do documento) | S00-T06, S03-T06, S04-T01 | Baselines e decisão de arquitetura ainda não ratificadas. Documentação pode ser revisada; implementação não pode alegar gate cumprido. |
| A-002 | Fronteira de confiança | CRÍTICA | TH-01; `serve_mobile_spike.py` | O servidor do experimento chama Docker a partir do host. Não expor porta nem reutilizar como API pública; substituir por broker/worker antes do MVP. |
| A-003 | Fronteira de confiança | CRÍTICA | TH-15; ADR-004/Q-05 | Separação árbitro/bot requer prova de viabilidade para manter integridade da apuração. Falha do spike bloqueia esta arquitetura. |
| A-004 | Ambiguidade | ALTA | Q-03/Q-04/Q-07 | Fronteira de VM e transporte/network do worker não aprovados. Implementar somente após decisão e teste em Linux efêmero. |
| A-005 | Mensuração | ALTA | FR-008/009; SC-003 | Quotas e tolerância de timeout não medidas/ratificadas; números de spikes anteriores não constituem SLA. |
| A-006 | Privacidade/Operação | ALTA | Q-08; FR-014; SG013–SG017 | Retenção e responsabilidades institucionais abertas; impedir dados reais nos artefatos do projeto. |
| A-007 | Integridade de competição | MÉDIA | TH-10; issue #15 | Posição 1º/2º com 188 pontos iguais na interface não define critério de desempate; remeter a S03-T03. |
| A-008 | Escopo | MÉDIA | FR-001; T2 | Linguagens gerais permanecem excluídas do primeiro MVP, evitando falsa equivalência entre DSL e código hostil; ratificar pedagógica e tecnicamente. |
| A-009 | Risco de evidência | MÉDIA | SC-002, SC-004 | Simulações com fixtures devem ser separadas de testes reais e da inspeção efetiva do kernel/runtime; nenhum PASS de ataque está declarado. |

## Coverage Summary (a ser verificado por validador automatizado)

- **Requisitos:** FR-001..FR-020 (**20** IDs distintos).
- **Critérios mensuráveis propostos:** SC-001..SC-008 (**8** IDs).
- **Ameaças do modelo:** TH-01..TH-16 (**16** IDs).
- **Tarefas futuras:** T001..T039 (**39**, todas não iniciadas).
- A redação das 39 tarefas referencia explicitamente FR/SC/TH e uma user story; verificador `scripts/verify_security_spec.py` deve falhar se qualquer ID ficar sem tarefa, se houver ID inexistente, checkbox prematuro ou se uma decisão crítica for apresentada como aprovada.
- **Constituição:** nenhum princípio é flexibilizado pelo plano. **Aprovação de segurança:** **BLOQUEADA** até resolução de A-001–A-006.
- **Repetição:** entradas/saídas/quotas citadas em vários documentos representam *camadas de especificação*, não um segundo catálogo de RF/RNF; S03 ainda precisa consolidar a baseline.

## Unmapped tasks / duplication / contradições

Nenhuma tarefa intencionalmente fora de US1..US5. Uma tarefa transversal de cobertura (T036) toca todos os requisitos/ameaças, mas **não** substitui os testes específicos nem conta como atestado de segurança. Diferenças entre `rootless`, `userns-remap` e VM estão mantidas; não são sinônimos.

## Next Actions

1. Executar o validador estático e o **check-prerequisites** nativo da feature 004 em CI, registrando resultado real (sem inventar PASS).
2. Revisar D1–D5 com o responsável e resolver o plano de separação árbitro/worker.
3. Não executar `/speckit.implement` nem testes de abuso na máquina pessoal antes de aprovar G0/G1.
4. Após aprovação, testar primeiro em infraestrutura descartável e reconciliar evidências com a S03 e a S04.
