# Especificações da RoboCopa IFMA

| Feature | Escopo | Estado |
|---|---|---|
| [000-governanca](000-governanca/spec.md) | Fundação/Spec Kit | Base técnica; ratificação pendente |
| [001-hosting-local](001-hosting-local/spec.md) | Laboratório e [MVP híbrido](001-hosting-local/hybrid-mvp.md) | Local demonstrado; cloud/VM reais pendentes |
| [002-tank-royale](002-tank-royale/spec.md) | Motor de batalha | CI e provas históricas de host |
| [003-autoria-mobile](003-autoria-mobile/spec.md) | Editor/RoboDSL básica | CI/PC; telefone e revisão pendentes |
| [004-isolamento-execucao](004-isolamento-execucao/spec.md) | Isolamento e controle | I1/I2/recortes I3 validados; I3 integral aberto |
| [005-identidade-academica](005-identidade-academica/spec.md) | Google Workspace/Gmail pessoal | ID-010 offline; login/vínculos/RLS para o piloto |

**Prioridade D-012:** [trilha DEMO](004-isolamento-execucao/demo-diretoria-mvp.md): I3-03C antes de I3-04, seguido de I3-05/06/07, I4, PWA/Supabase e I5. ID-011/multiescola e OAuth estudantil não bloqueiam a demonstração privada, mas proteção da API/VM e dados permanece obrigatória.

**I3-03:** [núcleo PG](004-isolamento-execucao/i3-03-postgres-plan.md), [admissão AD](004-isolamento-execucao/i3-03-admission-plan.md), [CW-01..06](004-isolamento-execucao/i3-03c-worker-api-plan.md) e [contrato worker](004-isolamento-execucao/contracts/worker-api.md). PG/AD possuem evidências; I3-03C em preparação pré-código, não Supabase já implantado. [Evidência AD](../docs/qualidade/evidencias/S04-T04-I3-03B.md).

**Feature005:** [D-011](../docs/planejamento/decisoes/D-011-google-pessoal-multiescolas.md), [ADR-008](../docs/arquitetura/ADR-008-google-multiescolas.md), [spec](005-identidade-academica/spec.md), [plan](005-identidade-academica/plan.md), [tasks](005-identidade-academica/tasks.md), [contrato](005-identidade-academica/contracts/google-eligibility.md) e [evidência ID-010](../docs/qualidade/evidencias/S03-ID-010.md). Gmail verificado e Workspace entram apenas PENDING na política; não é OAuth real.

Backlog JSON é canônico; 39 tarefas amplas de isolamento não se encerram por testes de subincremento. Fluxo constitution → specify → clarify → plan → tasks → analyze → implement → converge; scripts versionados, sem alegar slash commands inexistentes. [Estado atual](../docs/planejamento/ESTADO-ATUAL.md).
