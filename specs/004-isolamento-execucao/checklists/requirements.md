# Requirements Quality Checklist — Feature 004

**Purpose:** examinar qualidade, completude e verificabilidade da especificação, não testar sandbox já implementada.  
**Created:** 2026-10-09 · **Feature:** [spec.md](../spec.md)  
**Status:** revisão documental inicial, com decisões ainda abertas.

## Conteúdo, rastreabilidade e limites

- [x] CHK001 O problema identifica o computador pessoal, o servidor Python com Docker CLI e demais ativos.
- [x] CHK002 Histórias priorizadas e aceites Given/When/Then estão declarados.
- [x] CHK003 Requisitos e critérios possuem IDs estáveis FR-001..FR-020 e SC-001..SC-008.
- [x] CHK004 Classes T0/T1/T2 distinguem bot oficial, DSL e código arbitrário.
- [x] CHK005 Todos os FR/SC e ameaças TH têm ao menos uma tarefa planejada (ver CI do validador, quando executado).
- [x] CHK006 Artefatos atuais do laboratório são distinguidos dos componentes futuros.
- [x] CHK007 Não há instruções para atacar o host pessoal ou alterar o daemon existente.
- [x] CHK008 Fontes internas, externas e hipóteses são explicitamente distintas.

## Questões que impedem baseline aprovada

- [ ] CHK009 S00-T06/S03-T06 e decisão S04-T01 ratificadas.
- [ ] CHK010 D1–D5 revisadas e registradas com decisão humana.
- [ ] CHK011 Política de tolerância a timeout/limites calibrada com medição real.
- [ ] CHK012 Fronteira de árbitro/bot e WebSocket tecnicamente demonstrada.
- [ ] CHK013 Política de dados, retenção e responsabilidades institucionais acordadas.
- [ ] CHK014 Verificação de segurança real em ambiente segregado e plano operacional aprovados.

**Interpretação:** itens marcados indicam **qualidade de texto/planejamento**, não segurança comprovada. `CHK009–CHK014` bloqueiam aprovação e implementação pública.
