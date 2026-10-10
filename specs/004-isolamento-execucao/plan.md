# Implementation Plan — Isolamento de execução não confiável

**Revisão:** 2026-10-10 · **Feature:** [spec.md](spec.md) · **Branch de I2:** `feat/s04-i2-separated-arena`.

**Status:** implementação experimental autorizada por D-005, I1 e recorte I2 verificados no CI. **NÃO IMPLEMENTAR em produção nem liberar alunos antes de G-PROD.** G-EXP permite construir provas; G-PROD exige a arquitetura alvo validada e aceites humanos.

## Summary e decisões

MVP somente RoboDSL básica. VM Linux dedicada, sistema/daemon/disco próprios e sem drives pessoais é direção aprovada, não outra distribuição WSL. Não houve instalação no host. API pública sem socket Docker, broker autenticado, worker segregado, isolamento por job e árbitro independente continuam o alvo completo.

A [pesquisa oficial](../../docs/arquitetura/pesquisa-isolamento-2026-10-10.md) já demonstrou que rede internal e ausência de mounts/socket não bastam; externalServer do BattleRunner ainda inicia bots localmente; hashes não autenticam árbitro comprometido. I2 acrescentou prova controlada do protocolo fixado e filtro de mensagens planejado antes do código em [N5](i2-protocol-guard.md).

## Technical Context

| Elemento | Recorte atual |
|---|---|
| Testes | Ubuntu24.04 GitHub-hosted descartável; sem dados/credenciais pessoais, sem VM aninhada |
| Linguagem | Python para supervisor/contratos; websockets15.0.1 fixado no gateway; RoboDSL básica inalterada |
| Motor | Tank Royale1.4.0 fixado; servidor extraído de runner oficial; controlador recebe eventos oficiais sem booter local de bots |
| Separação I2 | Árbitro, Walls e Spin Bot em contêineres distintos; bridge internal owned e ACLs em seus namespaces; gateway7654, motor bruto7655 inacessível aos bots |
| Operação | Novos módulos não foram ligados à UI pública/pessoal. O laboratório Python existente continua localhost |
| Limites I1 | Sondas pequenas:64MiB,0,5CPU,16PIDs,tmpfs4MiB,saída8KiB; não dimensionam jogos |
| Limites I2 | 1CPU por papel, árbitro1GiB/bots512MiB,128PIDs,tmpfs128MiB; quotas de sessão finitas e timeout externo; orçamentos experimentais |
| Dados | Resultados/replay/manifestos sanitizados por execução; nenhum banco migrado; sem ledger de produção |
| Host futuro | VM independente ainda exige patches, discos, switches, rede guest, backup e recuperação verificados |

## Constitution Check

- Inclusão e escopo mantidos: RoboDSL básica, intermediário/avançado pós-MVP.
- **G-EXP autorizado:** referências conhecidas, fixtures finitas e runner descartável. Nenhum teste adversarial no computador pessoal.
- **GATE BLOQUEADO — G-PROD:** ainda faltam VM alvo, broker/autenticação/fila/ledger, quotas calibradas, vinte ciclos, backup/restauração, revisão e aceite. A prova de separação no CI não substitui implantação segura.
- Configuração declarada não substitui inspeção/runtime/negativos. Um conjunto de testes aprovado não prova inexistência de vulnerabilidades.
- D1/D2 e experimentos não homologam S00-T06, S03 ou o MVP.

## Planejamento completo e dependências

O catálogo [tasks.md](tasks.md) mantém39 tarefas T001–T039 com FR/SC/TH, abertas onde o aceite amplo ainda não foi atendido. [I1](iteration-1.md) e [I2](iteration-2.md) registram subconjuntos concluídos com evidência. A revisão extra de I2 foi planejada em [i2-audit-plan.md](i2-audit-plan.md) antes das correções, com [resultados](i2-audit-results.md).

| Etapa ampla | Tarefas | Situação e aceite restante |
|---|---|---|
| Fontes/autorização/ameaças | T001–T004 | D1/D2/G-EXP registrados; baselines e aprovações de produto continuam pendentes |
| Fronteira/compatibilidade | T005–T007 | I1 prova contenção e I2 separa bots/árbitro no runner. Falta VM alvo e revisão de rede/host |
| Plano de controle | T008–T012 | Contrato puro I1 pronto; broker autenticado e integração com fila ainda não existem |
| Admissão | T013–T016 | Negativos da DSL/versão implementados; falta autorização multiusuário e ligação com plataforma |
| Sandbox/árbitro | T017–T022 | Imagens/isolamento por papel, rede e gateway comprovados no recorte I2; não é implantação de alunos |
| Recursos/recuperação | T023–T027 | Limites finitos e dois abortos/cleanup testados; não é recuperação durável, cotas de produção ou20 ciclos |
| Integridade | T028–T032 | I2 audita origem lógica, campos, sequência, replay e hashes; ledger/idempotência de produção ainda necessário |
| Suspensão/operação | T033–T035 | Falha fechada nos harnesses; chave operacional do broker e runbook da VM ainda pendentes |
| Homologação | T036–T039 | Matriz completa, revisão, smoke da VM por ação autorizada e liberação permanecem em aberto |

## I1 entregue

Admissão estrita desabilitada por padrão, política com20 invariantes de perfil diagnóstico, subprocesso sem shell e limites durante leitura,9 sondas reais finitas.55 testes iniciais do novo código, distintos das provas Docker. [Evidência](../../docs/qualidade/evidencias/S04-T04-I1.md). Não autentica usuários nem executa ledger.

## I2 entregue no recorte

- `arena_policy.py`:24 verificações por contêiner, conjunto de redes anexadas, namespaces/ownership; regras somente no namespace owned, sem privilégios de administração no bot.
- `arena_protocol.py` e `gateway.py`: handshake exato e allowlist de BotReady/BotIntent, sem canais administrativos; tokens do bot não são segredo do controlador. Limites por sessão e11 testes de transporte contra engine falso, separados da prova real.
- `run_separated_arena.py`: duas batalhas de3 rounds oficiais, testes positivos/negativos nos dois bots, manifestos, dois abortos controlados e limpeza específica. Falha do daemon não é interpretada como recurso ausente.
- `arena_evidence.py` e `verify_arena_evidence.py`: auditoria somente leitura de esquema, tipos, identidades, eventos/rounds, hash, flags e cleanup; nenhum processo ou rede iniciados.
- Lote referência: [run38048459272](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38048459272), duas batalhas reais,24 invariantes por papel e19 verificações por bot. [Relatório](../../docs/qualidade/evidencias/S04-T04-I2.md).

As ACLs manuais só são instaladas nos namespaces verificados; o Docker cria as regras da bridge no runner. Não afirmar ausência de qualquer regra de host ao longo de toda a execução. O host pessoal não é acessado.

## Próximos incrementos a detalhar antes do código

**I3:** broker autenticado, admissão multiusuário, fila e estado duráveis, ledger/idempotência, retry, cotas e suspensão. O catálogo T já prevê esses temas, mas contratos e casos de falha concretos devem virar plano do incremento antes de implementar. A API não recebe socket Docker.

**I4:** inventário de versões do produto Docker Desktop/Windows/Hyper-V/Linux, disco e capacidade; instalação e rede da VM somente sob procedimento específico e ação do responsável. Switch Internal permite host↔VM, não é isolamento automático; a rede guest exige prova própria.

**I5:** quotas calibradas do motor,20 ciclos, matriz integral TH, backup/restauração, resposta a incidentes, revisão independente e liberação. Rootless/gVisor são camadas opcionais sujeitas à compatibilidade, não pretexto para ampliar o MVP.

## Estrutura e invariantes

Os módulos Python concretos estão em `services/worker_agent/`; `services/worker-agent/` era caminho candidato do desenho inicial. Não substituímos serviço de produção. Feature004 conserva spec/clarifications/research/data-model/contracts/tasks/analysis/checklists e iterações vinculadas.

[Contrato](contracts/job-protocol.md) · [Dados](data-model.md) · [Ameaças](../../docs/arquitetura/ameacas-sandbox.md) · [ADR004](../../docs/arquitetura/ADR-004-isolamento-execucao.md).

Em falha, negar execução e registrar incerteza, sem fallback ao Docker pessoal. Limpeza apenas owned; nenhuma orientação de prune global/down-v, migração VHDX, abertura de firewall ou drives compartilhados. Critérios finais: [security-gates.md](checklists/security-gates.md).
