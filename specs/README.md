# Especificações da RoboCopa IFMA

| Feature | Escopo | Estado |
|---|---|---|
| [000-governanca](000-governanca/spec.md) | Fundação, rastreabilidade e bootstrap | Base técnica entregue; ratificação pendente |
| [001-hosting-local](001-hosting-local/spec.md) | Laboratório PostgreSQL/sonda e [evolução híbrida](001-hosting-local/hybrid-mvp.md) | Experimento local demonstrado; implantação híbrida pendente |
| [002-tank-royale](002-tank-royale/spec.md) | Batalha de referência | CI aprovado; reprodução Windows informada pelo responsável |
| [003-autoria-mobile](003-autoria-mobile/spec.md) | RoboDSL e editor | CI/PC demonstrados; telefone físico e ratificação pendentes |
| [004-isolamento-execucao](004-isolamento-execucao/spec.md) | Contratos, isolamento e controle | I1/I2 e recortes I3 demonstrados; integração cloud/VM/produção pendentes |

A feature004 mantém o catálogo amplo [T001–T039](004-isolamento-execucao/tasks.md), [I1](004-isolamento-execucao/iteration-1.md), [I2](004-isolamento-execucao/iteration-2.md), [guarda de protocolo](004-isolamento-execucao/i2-protocol-guard.md) e [reconciliação](004-isolamento-execucao/i2-reconciliation-plan.md). Só encerrar recorte com evidência; não encerrar gates amplos por existir um documento ou CI verde.

**I3:** [plano por subincrementos](004-isolamento-execucao/iteration-3.md) e [decisões](004-isolamento-execucao/i3-design-decisions.md). I3-01 SQLite é laboratório; I3-02 é [probe TLS](004-isolamento-execucao/i3-02-auth-plan.md), não serviço cloud.

**I3-03:** [plano PG-01..06](004-isolamento-execucao/i3-03-postgres-plan.md), [contrato SQL privado](004-isolamento-execucao/contracts/postgres-control.md) e [evidências](../docs/qualidade/evidencias/S04-T04-I3-03.md). Núcleo PostgreSQL validado, I3-03 integral ainda em execução. As correções [F01](004-isolamento-execucao/i3-03-ci-audit-plan.md), [F02](004-isolamento-execucao/i3-03-reap-fix-plan.md) e [C02](004-isolamento-execucao/i3-03-cleanup-plan.md) tiveram planejamento antes dos patches.

**Direção após revisão:** [D-007](../docs/planejamento/decisoes/D-007-execucao-pos-revisao-mvp.md) e [ADR-006](../docs/arquitetura/ADR-006-demo-gratuita-plano-controle.md): demonstração privada, frontend estático econômico, persistência Supabase remota e computação em VM local. Implementação cloud/VM e piloto estudantil não estão homologados.

`spec.md` descreve problema/histórias/aceites; `plan.md` decisões/interfaces/testes; `tasks.md` execução. Requisitos ratificados na S03 serão a baseline formal, sem catálogo concorrente. Fluxo: constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge. Usar scripts versionados e checagem nativa da feature, não alegar slash commands executados sem ferramenta. [Estado atual](../docs/planejamento/ESTADO-ATUAL.md).
