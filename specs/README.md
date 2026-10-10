# Especificações da RoboCopa IFMA

| Feature | Escopo | Estado |
|---|---|---|
| [000-governanca](000-governanca/spec.md) | Fundação, rastreabilidade e bootstrap | Base técnica entregue; ratificação pendente |
| [001-hosting-local](001-hosting-local/spec.md) | Laboratório PostgreSQL/sonda e [evolução híbrida](001-hosting-local/hybrid-mvp.md) | Experimento local demonstrado; implantação híbrida pendente |
| [002-tank-royale](002-tank-royale/spec.md) | Batalha de referência | CI aprovado; reprodução Windows informada pelo responsável |
| [003-autoria-mobile](003-autoria-mobile/spec.md) | RoboDSL e editor | CI/PC demonstrados; telefone físico e ratificação pendentes |
| [004-isolamento-execucao](004-isolamento-execucao/spec.md) | Contratos, isolamento e controle | I1/I2 e recortes I3 demonstrados; cloud/VM/produção pendentes |

A feature004 mantém o catálogo amplo [T001–T039](004-isolamento-execucao/tasks.md), [I1](004-isolamento-execucao/iteration-1.md), [I2](004-isolamento-execucao/iteration-2.md), [guarda de protocolo](004-isolamento-execucao/i2-protocol-guard.md) e [reconciliação](004-isolamento-execucao/i2-reconciliation-plan.md). Só encerrar recorte com evidência, não gates amplos por documento ou CI verde.

**I3:** [plano por subincrementos](004-isolamento-execucao/iteration-3.md) e [decisões](004-isolamento-execucao/i3-design-decisions.md). I3-01 SQLite é laboratório; I3-02 é [probe TLS](004-isolamento-execucao/i3-02-auth-plan.md), não serviço cloud.

**I3-03:** [plano PG-01..06](004-isolamento-execucao/i3-03-postgres-plan.md), [contrato SQL privado atualizado após002](004-isolamento-execucao/contracts/postgres-control.md) e [evidências do núcleo](../docs/qualidade/evidencias/S04-T04-I3-03.md). Núcleo PostgreSQL validado, I3-03 integral em execução. [F01](004-isolamento-execucao/i3-03-ci-audit-plan.md), [F02](004-isolamento-execucao/i3-03-reap-fix-plan.md) e [C02](004-isolamento-execucao/i3-03-cleanup-plan.md) foram planejados antes dos patches.

**I3-03B:** [plano AD-01..06](004-isolamento-execucao/i3-03-admission-plan.md), [contrato admissão/Psycopg](004-isolamento-execucao/contracts/admission-postgres.md), [relatório](../docs/qualidade/evidencias/S04-T04-I3-03B.md) e [JSON](../docs/qualidade/evidencias/S04-T04-I3-03B.json). Admissão I1 ligada à fila PostgreSQL: 22 integrações reais e 25 unidades novas incluídas em407 regressões. Não verifica JWT/worker operacional e não implanta Supabase. Após002, rc_broker não chama enqueue bruto; rc_admission é a entrada restrita.

**Direção vigente:** [D-009](../docs/planejamento/decisoes/D-009-carater-voluntario-vercel-hobby.md) mantém Vercel Hobby preferida para a PWA voluntária, Supabase com persistência remota e VM local só para computação; Cloudflare é contingência. [D-007](../docs/planejamento/decisoes/D-007-execucao-pos-revisao-mvp.md) e [ADR-006](../docs/arquitetura/ADR-006-demo-gratuita-plano-controle.md) conservam os demais trade-offs. Nada homologa implantação cloud/VM ou piloto estudantil.

`spec.md` descreve problema/histórias/aceites; `plan.md`, decisões/interfaces/testes; `tasks.md`, execução. Requisitos ratificados na S03 serão baseline formal, sem catálogo concorrente. Fluxo constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge. Usar scripts versionados e checagem nativa; não alegar slash commands sem ferramenta. [Estado atual](../docs/planejamento/ESTADO-ATUAL.md).
