# Implementation Plan — Isolamento de execução não confiável

**Revisão:** 2026-10-10, após I3-03B. **Feature:** [spec.md](spec.md). **Branch vigente:** `feat/s04-i3-03-postgres-leases`, PR #26. **Macro S04-T04:** EM_EXECUCAO.

**Status:** implementação experimental autorizada por D-005 e pedidos posteriores; I1/I2 e subconjuntos I3 verificados. **NÃO IMPLEMENTAR em produção nem liberar alunos antes de G-PROD.** G-EXP permite construir provas finitas; **GATE BLOQUEADO — G-PROD** exige integração, VM-alvo, recuperação, revisão e aceites próprios.

## Summary e decisões vigentes

MVP somente RoboDSL básica, mobile-first. Vercel Hobby é primeira escolha do frontend no contexto voluntário sem remuneração associada declarado em D-009; Cloudflare é alternativa. Supabase PostgreSQL/Auth/Storage são destino canônico remoto; SQLite e Compose/Postgres pessoal são laboratório, não banco definitivo. API/controle cloud não recebem socket Docker. VM Linux dedicada no PC, sistema/daemon/disco próprios e sem drives pessoais, é direção aprovada, não outra distribuição WSL nem instalação já executada.

A [pesquisa de isolamento](../../docs/arquitetura/pesquisa-isolamento-2026-10-10.md) e os [riscos](../../docs/arquitetura/ameacas-sandbox.md) guiam as fronteiras. I2 demonstrou separação e filtro do protocolo fixado, planejado em [N5](i2-protocol-guard.md); redes internal e ausência de mounts isoladamente não bastam, hashes não autenticam árbitro comprometido. Não ampliar linguagens pelo sucesso das provas.

## Technical Context

| Elemento | Estado demonstrado e limite |
|---|---|
| Testes | Ubuntu GitHub-hosted descartável, dados sintéticos; regressões locais sem Docker pessoal |
| Linguagem | Python para contratos/supervisão/admissão; RoboDSL básica preservada; nenhuma portabilidade automática de Python a Deno |
| Motor e I2 | Tank Royale1.4.0 fixado; árbitro/bots separados, gateway com allowlist, ACLs em namespaces owned; provas reais de batalha e limpeza |
| I3-01 | Broker interno e SQLite em arquivo temporário, somente experimento OFF por padrão |
| I3-02 | mTLS TLS1.3 real de probe em loopback CI, sem canal de jobs/PKI de produção |
| I3-03 / PG | Migration001, PostgreSQL17 real, jobs/attempts/leases/fencing, cancelamento/retry/reap e privilégios; não é Supabase implantado |
| I3-03B / AD | Migration002, catálogo privado de hashes/revisão, papel rc_admission, parser/compilador I1 e adaptador Psycopg3.3.6; 22 integrações reais de banco/driver |
| Persistência final | PostgreSQL/Auth/Storage Supabase, RLS/app/cloud a integrar; não guardar banco mestre no PC |
| VM real | Direção aprovada; hypervisor/rede/discos/patches/segredos/recuperação ainda sujeitos a I4 e autorização específica |

## Constitution Check

Inclusão, acessibilidade e escopo básico mantidos. G-EXP autoriza fixtures finitas e runner descartável, nunca testes adversariais na máquina pessoal. S00-T06, S03 e homologação não são ratificados por decisões técnicas. Configuração declarada não substitui inspeção/negativos; CI verde não prova inexistência de vulnerabilidades. Não abrir serviço de aluno ou escolher conta/projeto cloud pago nesta entrega.

## Planejamento completo e dependências

O catálogo [tasks.md](tasks.md) mantém 39 tarefas T001–T039 com FR/SC/TH, abertas até o aceite integral. Os planos de incremento decompõem esses objetivos sem criar uma baseline concorrente.

| Etapa ampla | Tarefas | Aceite restante |
|---|---|---|
| Governança/ameaças | T001–T004 | Ratificações e limites de produto; minutas não são pesquisa de campo |
| Fronteira/compatibilidade | T005–T007 | I1/I2 provados no runner; VM-alvo/rede/host ainda pendentes |
| Plano de controle | T008–T012 | Núcleo PG e ponte AD implementados; falta API cloud autenticada e identidade operacional do worker |
| Admissão | T013–T016 | I1 conectado a PostgreSQL em CI; falta identidade multiusuário real, catálogo da aplicação, RLS e roteamento seguro |
| Sandbox/árbitro | T017–T022 | Evidências I2 limitadas; não implantação de alunos |
| Recursos/recuperação | T023–T027 | Leases/cancelamento/retry no banco; watchdog da VM, quotas/20ciclos e recovery ampliado pendentes |
| Integridade | T028–T032 | Descriptor/versionamento comprovados; resultado/replay e ledger com efeito único ainda I3-04 |
| Suspensão/operação | T033–T035 | Gate OFF em biblioteca/banco; operação cloud/runbook da VM pendentes |
| Homologação | T036–T039 | Matriz integral, revisão independente, smoke autorizado do host e decisão de liberação |

## I1/I2 — provas históricas preservadas

[I1](iteration-1.md): contrato de admissão puro, invariantes e limites, nove sondas reais; [evidências](../../docs/qualidade/evidencias/S04-T04-I1.md). Não autentica usuários nem cria ledger.

[I2](iteration-2.md): arena_policy, arena_protocol/gateway, run_separated_arena e auditores somente leitura; imagens/papéis distintos, isolamento/ACLs, duas batalhas de referência, abortos e timeout/cleanup. [Auditoria planejada](i2-audit-plan.md), [resultados](i2-audit-results.md), [reconciliação R01–R10](i2-reconciliation-plan.md), [decisão](i2-reconciliation-decision.md), [relatório de reconciliação](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md). Os placares históricos não são reescritos por novas regressões. ACLs manuais só nos namespaces verificados; Docker cria suas próprias regras no runner. Não afirmar que o host pessoal foi testado.

## I3 — decomposição executada e próxima fronteira

[Plano geral I3](iteration-3.md) e [decisões](i3-design-decisions.md) preservam o histórico de I3-01/I3-02. [I3-01](../../docs/qualidade/evidencias/S04-T04-I3-01.md): SQLite de laboratório, não fallback de produção. [I3-02](i3-02-auth-plan.md): probe mTLS real e [contrato](contracts/worker-channel.md), sem jobs; [evidências](../../docs/qualidade/evidencias/S04-T04-I3-02.md). Q-07 só foi provada para o laboratório.

[I3-03 / PG-01..06](i3-03-postgres-plan.md): migration001 testada em PostgreSQL real, owner NOLOGIN sem superuser/BYPASSRLS, RLS forçada, estado transacional e fencing; [relatório](../../docs/qualidade/evidencias/S04-T04-I3-03.md). [Contrato PostgreSQL](contracts/postgres-control.md) atualizado para distinguir antes/depois da migration002.

**I3-03B / AD-01..06:** [plano anterior ao código](i3-03-admission-plan.md), [contrato](contracts/admission-postgres.md), [relatório](../../docs/qualidade/evidencias/S04-T04-I3-03B.md) e [manifesto](../../docs/qualidade/evidencias/S04-T04-I3-03B.json). Fonte `4179e5b`: 22 testes reais I1/Psycopg/PostgreSQL; 25 unidades novas incluídas em407 regressões locais e sete workflows aprovados. Cadastro privado de versões/hashes; revisão/política reconferidas na gravação; commit antes de sucesso. **Após002:** rc_admission é a entrada de enfileiramento, rc_broker conserva operações de execução mas perde o enqueue bruto. A compilação ocorre fora de transação longa. Revogar versão bloqueia novas admissões, não cancela automaticamente jobs já enfileirados; definir política de ciclo de vida na integração futura.

**I3-03 integral permanece EM_EXECUCAO:** falta JWT/identidade operacional, API cloud/clientes compatíveis, cadastro de versões da aplicação, conexão Supabase real com permissões/pooler/TLS, controle de worker outbound e ensaio fim a fim. Contexto ServiceActor não é autenticação. Psycopg Python não vira runtime de Edge Deno; só contrato SQL pode ser compartilhado. Não transportar DSN de rc_admission/rc_broker para bot/cliente.

**I3-04:** resultado/replay validado e ledger de efeitos únicos. **I3-05/06/07:** quotas/polling econômico, recuperação ampliada e integração. **I4:** instalação/rede/patches/disco/segredos de VM no host apenas sob procedimento/autorização específicos. **I5:** 20ciclos, matriz TH, backup de banco e objetos, restauração, revisão independente e ensaio de demonstração. Rootless/gVisor são camadas a avaliar, não condição para ampliar o MVP.

## Estrutura, testes e invariantes

Pacotes concretos Python: `services/worker_agent/` e `services/execution_control/`; os nomes com hífen do catálogo macro são rascunhos de organização e não módulos Python existentes. SQL versionado em `services/execution_control/postgres/`. Ver [dados](data-model.md), [contrato legado I1](contracts/job-protocol.md) e [ADR004](../../docs/arquitetura/ADR-004-isolamento-execucao.md).

Verificar scripts de planejamento e Spec Kit nativo, manter as 39 caixas amplas e18 gates sem ratificação indevida. Toda necessidade descoberta vira plano/adendo antes do patch; [correção do CI AD](i3-03-admission-ci-fix.md) exemplifica essa trilha. Artefatos referenciam fonte/run, hashes e limitações. Erro de consulta de cleanup não é prova de ausência. Nenhum prune global, down-v pessoal, migração VHDX, abertura de firewall, mount de drives ou fallback ao Docker pessoal.

Concluir cada rodada sincronizando planos/tarefas/contratos/estado/evidências/dependências. Os relatórios guardam os lotes reais anteriores; descrição do PR registra nova rodada documental sem inventar execução no host. [Gates finais](checklists/security-gates.md).
