# Implementation Plan: Isolamento de execução não confiável

**Branch:** `docs/s04-t04-isolamento-speckit` | **Date:** 2026-10-09 | **Spec:** [spec.md](spec.md)  
**Input:** especificação S04-T04; [clarifications.md](clarifications.md), [research.md](research.md), [modelo de ameaças](../../docs/arquitetura/ameacas-sandbox.md).  
**Status:** **PLANO CANDIDATO, NÃO IMPLEMENTAR** até gates/decisões definidos.

## Summary

Separar a execução de robôs T1 (RoboDSL restrita) do computador pessoal e dos serviços da RoboCopa: broker tipado, executor em fronteira Linux independente, sandbox por job com limites e negação de rede/arquivos, árbitro distinto do código do aluno, validação de replay/resultado e recuperação idempotente. **Não aceitar Java/JS arbitrário nem usar diretamente o daemon Docker Desktop compartilhado como fronteira final.**

Este documento descreve **como validar a viabilidade** da abordagem; não instala VM, daemon, worker, regras de rede ou endpoint. A S04-T04 formal depende de S04-T02 e T03 e, indiretamente, da baseline S03. Os spikes anteriores avançaram de forma preparatória autorizada, sem encerrar os gates.

## Technical Context

| Elemento | Estado atual e decisão preliminar |
|---|---|
| Language/Version | Python 3.13 para automação do protótipo; gerador Java/JDK 21 e Tank Royale 1.4.0 fixados; linguagem do API final ainda depende da S03/S04-T01. |
| Primary Dependencies | Docker Engine API/CLI apenas **do worker segregado** (candidato); Tank Royale Battle Runner oficial; broker tipado em tecnologia a definir. Avaliar `runsc`/rootless como camadas adicionais. |
| Storage | PostgreSQL 17 existe no laboratório, mas não fica acessível ao sandbox; dados do job no plano de controle, armazenamento efêmero na VM. |
| Testing | Python `unittest`, contratos, provas negativas com dados sintéticos em GitHub Actions efêmero e futura VM descartável; inspeção efetiva do runtime. |
| Target Platform | Windows 11 Pro / Docker Desktop/WSL2 pessoal existente; **worker alvo em VM Linux dedicada**, a validar antes de uso. |
| Project Type | Arquitetura distribuída em plano de controle, broker/worker, isolamento por job e evidências. |
| Performance Goals | Medir simultaneidade, latência, limpeza e limites; não declarar valores de capacidade sem teste. |
| Constraints | Sem socket Docker na API, sem mount pessoal, sem egress genérico, sem acesso a segredos, sem fallback; operação local/privada até aprovação. |
| Scale/Scope | Piloto limitado; alvo inicial de **uma execução por vez** como hipótese operacional a medir e ratificar, não garantia. |
| Impact | Isolamento tem custo de CPU/RAM/disco/complexidade; nunca comprometer proteção do host para cumprir desempenho. |

## Constitution Check (gate anterior à implementação)

| Princípio | Evidência documental | Situação |
|---|---|---|
| I. Inclusão e pedagogia | RoboDSL candidata permite lógica, sem exigir web/mobile | Condição mantida; avaliação física pendente |
| II. Escopo do MVP | Uma linguagem T1 candidata; T2 negada | Compatível, depende de ratificação |
| III. Execução não confiável | VM separada, controles e teste de abuso exigidos | **GATE BLOQUEADO**: arquitetura ainda não validada |
| IV. Rastreabilidade | FR/SC/TH → tarefas → testes planejados | Conferência estrutural automatizável |
| V. Qualidade e evidências verdadeiras | Testes sintéticos separados de CI e host | Compatível; sem PASS de segurança |
| VI. Operação própria reversível | VM e rollback candidatos; sem mudança no host | **GATE BLOQUEADO**: backup/snapshot/recuperação ainda não testados |
| VII. IA e dados | Sem dados pessoais/credenciais no plano | Compatível; política de retenção ainda aberta |

**Bloqueio explícito:** a existência de plan.md não desbloqueia `/speckit.implement`. Consultar [analysis.md](analysis.md) e [checklists/security-gates.md](checklists/security-gates.md) antes de qualquer execução.

## Phases (ordem obrigatória)

### F0 — Revisão e autorização

Ratificar Q-02/Q-03/Q-04/Q-05/Q-06/Q-07/Q-08/Q-09/Q-10; revisar riscos críticos e delimitar ambiente efêmero sem dados pessoais. Sem autorização, executar somente verificações documentais, testes unitários estáticos e análise de contratos.

**Checkpoint G0:** escopo T1 aprovado, VM/worker aprovados e nenhuma execução em host pessoal prevista.

### F1 — Prova de fronteira e compatibilidade

Criar **somente em runner efêmero ou VM descartável autorizada** ambiente Linux segregado. Testar runtime, snapshots, redes, ausência de drives do host, usuário, namespaces, cgroups, seccomp/AppArmor e política real de conexões. Executar exemplos **confiáveis**, não submissões de alunos.

Testar especificamente Tank Royale 1.4.0 com **árbitro fora do ambiente de processo do bot**, canal de comunicação restrito, inicialização e coleta de replay. Se esse arranjo for inviável, documentar e comparar worker externo antes de seguir.

**Checkpoint G1:** compatibilidade demonstrada e artefatos medidos; se falhar, **sem bypass para o Docker Desktop pessoal**.

### F2 — Plano de controle e entrada

API recebe pedidos autorizados, valida AST e gera `ExecutionRequest` imutável, com quota e idempotência. Worker separado recebe contrato restrito; **sem caminho de usuário que chame CLI Docker nem shell**. Rejeição T2, falha fechada e feature flag desligada por padrão.

**Checkpoint G2:** testes negativos de bypass e adulteração aprovados; binários gerais continuam negados.

### F3 — Sandbox por job e ensaios

Provisionar sandbox efêmero por tentativa na fronteira VM. Restringir mounts, redes, socket, capacidades, dispositivos, processos e recursos. Inspecionar política efetiva. Testar cargas sintéticas (sem arquivos pessoais), timeout, cancelamento, recuperação e ausência de órfãos. Logs e artefatos sanitizados.

**Checkpoint G3:** cobertura de TH-01..TH-16 com resultados, inclusive falhas tratadas; riscos críticos não mitigados bloqueiam avanço.

### F4 — Integridade, corrida e saída

Vincular fonte/versão do programa, motor e política aos resultados; validar esquema do `BattleResults`/replay oficial, rejeitar corrupção e serialização anômala; persistir idempotente e limitar retry e abuso de fila.

**Checkpoint G4:** regressão de 100% de fixtures inválidas negadas e métricas propostas revisadas.

### F5 — Revisão e fechamento

Consolidar artefatos, confronto real CI/VM, testes de segurança e decisão. O responsável ratifica riscos/limites e, se necessário, solicita parecer de segurança independente. Atualizar ADR, backlog e issue **somente após evidências**. Antes de acesso público haverá outro gate S08 de identidade, TLS, backups, dados e operação.

## Project Structure

### Documentação desta feature

```text
specs/004-isolamento-execucao/
├── spec.md
├── clarifications.md
├── research.md
├── plan.md
├── data-model.md
├── contracts/job-protocol.md
├── quickstart.md
├── tasks.md
├── analysis.md
└── checklists/
    ├── requirements.md
    └── security-gates.md
```

### Estrutura planejada para implementação futura (AINDA NÃO EXISTE)

```text
services/
├── execution-control/       # API/broker tipado, nunca Docker socket
├── worker-agent/             # agente da VM segregada
├── execution-sandbox/        # política job por tentativa
└── engine-adapter/           # árbitro e integração com Tank Royale
packages/
├── job-contracts/            # esquemas validados e versão imutável
└── result-validation/        # replay e ledger idempotente
tests/
├── security/                 # negativos de política, quotas e fronteiras (CI/VM efêmero)
└── contract/                 # schema job, resultado e rejeições
docs/
├── arquitetura/ameacas-sandbox.md
└── qualidade/evidencias/S04-T04-*.md
```

A implementação deverá escolher a estrutura final após revisão. Os caminhos em `tasks.md` são **destinos planejados**, não arquivos já criados.

## Dados, interfaces e orquestração

Ver [data-model.md](data-model.md), [contrato interno](contracts/job-protocol.md) e [quickstart](quickstart.md). Nenhum esquema é API pública aprovada. Todos os eventos e campos recebidos do sandbox são tratados como dados não confiáveis.

## Estrutura de validação e monitoramento

| Camada | Onde executar | O que mede | O que não comprova |
|---|---|---|---|
| Análise estática Spec Kit | GitHub Actions, sem segredo | IDs, mapeamento FR/SC/TH, templates e inconsistências | Segurança da VM e isolamento real |
| Fixtures de contrato | CI efêmero | Rejeições de schema, duplicidade, erros de parsing | Privacidade de host |
| Spike de worker/judge | Runner efêmero/VM descartável | WebSocket mínimo, separação de processo, isolamento de network/mount | Host residencial sem teste específico |
| Provas negativas | Somente ambiente isolado autorizado | Limites, negação observada, cleanup e fail-closed | Ausência de vulnerabilidades desconhecidas |
| Smoke da VM dedicada | Somente por ação humana explícita no host | Compatibilidade da fronteira e operação | Liberação de acesso externo |
| Pilotagem S08 | Etapa posterior | Carga real, recuperação e acesso autorizado | Eficácia pedagógica sem estudo |

## Rollback e segurança operacional

Habilitar novas execuções somente com evidência de gate e **flag desligada por padrão**. Em falha, negar novos jobs, cancelar/controlar os existentes, preservar somente logs/manifestos sanitizados e eliminar os recursos temporários **da VM**, sem modificar volumes de outros projetos. Nunca sugerir `docker system prune`, `down -v`, edição de daemon, firewall, DNS, roteador, runner local ou migração de VHDX como parte automática desta feature.

## Complexity Tracking

A VM dedicada introduz sobrecarga deliberada. **Justificativa:** o requisito III da constituição exige proteger o host pessoal e demais projetos. Uma única sandbox Docker no daemon compartilhado deixa dependência forte do mesmo plano de controle; a opção simples não atende ao objetivo proposto sem prova adicional. Revisar após medições, mantendo a possibilidade de um executor externo em vez de afrouxar limites.
