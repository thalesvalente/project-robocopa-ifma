# Especificações da RoboCopa IFMA

| Feature | Escopo | Estado |
|---|---|---|
| [000-governanca](000-governanca/spec.md) | Fundação, rastreabilidade e bootstrap | Base técnica entregue; ratificação pendente |
| [001-hosting-local](001-hosting-local/spec.md) | PostgreSQL e sonda local | CI e primeira execução no host confirmados; não é MVP |
| [002-tank-royale](002-tank-royale/spec.md) | Batalha de referência | CI aprovado; reprodução Windows informada pelo responsável |
| [003-autoria-mobile](003-autoria-mobile/spec.md) | RoboDSL e editor com treino real | CI/PC demonstrados; telefone físico e ratificação pendentes |
| [004-isolamento-execucao](004-isolamento-execucao/spec.md) | Segurança, contratos e provas de isolamento | I1 e I2 técnicos comprovados no CI; VM real, broker, revisão e produção pendentes |
| [005-identidade-academica](005-identidade-academica/spec.md) | Google OAuth acadêmico IFMA/outras escolas e Gmail pessoal, com vínculo escolar e RLS | D-011/ADR-008 aprovados; identidade/autorização reais pendentes |

A feature004 mantém catálogo amplo [T001–T039](004-isolamento-execucao/tasks.md) e incrementos vinculados: [I1](004-isolamento-execucao/iteration-1.md), [I2](004-isolamento-execucao/iteration-2.md), [adendo de protocolo](004-isolamento-execucao/i2-protocol-guard.md) e [plano da revisão](004-isolamento-execucao/i2-audit-plan.md). Detalhar novas necessidades antes do código; só marcar concluído o recorte realmente evidenciado.

`spec.md` descreve problema/histórias/aceite, `plan.md` decisões/interfaces/testes e `tasks.md` execução. Cada incremento referencia tarefa macro Sxx-Tyy. Requisitos aprovados na S03 serão a fonte de verdade; artefatos no Spec Kit não criam baseline concorrente.

Fluxo: constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge. Usar os arquivos/scripts versionados e verificar a feature selecionada; não alegar execução nativa dos slash commands nem segurança aprovada por ter documentos.

A reconciliação dos PRs I2 foi [planejada e encerrada no recorte experimental](004-isolamento-execucao/i2-reconciliation-plan.md), com [matriz de decisão](004-isolamento-execucao/i2-reconciliation-decision.md) e [relatório](../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md). G-PROD e tarefas amplas continuam bloqueados/abertos.

**Feature 005 (D-011 vigente):** [spec](005-identidade-academica/spec.md), [plan](005-identidade-academica/plan.md), [tasks](005-identidade-academica/tasks.md), [contrato](005-identidade-academica/contracts/google-eligibility.md) e [research](005-identidade-academica/research.md). Google Workspace acadêmico **ou Gmail pessoal**; ambos precisam de escola/participação aprovadas, não apenas login. [D-011](../docs/planejamento/decisoes/D-011-google-pessoal-multiescolas.md) · [ADR-008](../docs/arquitetura/ADR-008-google-multiescolas.md). [D-010](../docs/planejamento/decisoes/D-010-login-google-academico-ifma.md) registra a decisão histórica exclusiva, agora superada. **Nenhum login Google real implementado.**
