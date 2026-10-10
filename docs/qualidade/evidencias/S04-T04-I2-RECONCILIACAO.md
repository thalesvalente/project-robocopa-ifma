# S04-T04 / I2 — Relatório final de reconciliação técnica
**Data:** 2026-10-10 · **Decisão:** FECHADO_NO_ESCOPO_EXPERIMENTAL · **Macro:** S04-T04 EM_EXECUCAO · **G-PROD:** BLOQUEADO.

## Objeto e sequência rastreável
Plano: [R01–R10](../../../specs/004-isolamento-execucao/i2-reconciliation-plan.md), commit anterior às correções `4bb7a5b85dcbf86b667dde07500476d40e510d8e`. [Matriz comparativa e adendo C01–C05](../../../specs/004-isolamento-execucao/i2-reconciliation-decision.md) publicados antes de modificar runtime. Baselines comparadas: PR #19 `3f1b495`, PR #21 `583fe58` e PR #18 `e94ac97`. Coleta de fontes rastreadas no run [38058103430](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38058103430), 226/208/217 blobs conferidos contra árvores; nenhuma topologia mesclada cegamente.

**Arquitetura única escolhida:** PR [#19](https://github.com/thalesvalente/project-robocopa-ifma/pull/19), branch `feat/s04-i2-separated-arena`. PRs [#18](https://github.com/thalesvalente/project-robocopa-ifma/pull/18) e [#21](https://github.com/thalesvalente/project-robocopa-ifma/pull/21) encerrados como alternativas superadas, sem merge, preservando branches/commits. #20 havia sido encerrado previamente sem merge. Nenhuma alteração na main.

## Correções C01–C05 e critérios R01–R10
| Achado | Critério observado | Estado |
|---|---|---|
| C01 — timeout real | Fixture conhecida iniciou, deadline externo 0,5s observou TIMEOUT próprio, cleanup owned sem órfãos; testes negativos contra falso PASS | FECHADO |
| C02 — evidências | `reconciliation.json` estrito vincula fonte `e7afd8a2ac7cb1ab45eeec2146ae828e56f93e0a`, checkout CI `447fb906dbd8d465086e502c0208516670a2e11c`, workflow 38059207968, 3 imagens, 5 IDs únicos e 12 hashes | FECHADO |
| C03 — gateway | Handshake/versão/identidade válidos; allowlist, rejeição de controles antes/depois, frames e campos inválidos, limites cumulativos, sessões/drain | FECHADO |
| C04 — participantes/processos | Roster oficial exato de Walls/Spin Bot, endereços e portas, erros de futures e término controlado; duas partidas reais bem-sucedidas | FECHADO |
| C05 — rastreabilidade | Relatório, matriz, backlog macro preservado, alternativas encerradas, coletor de leitura temporário removido | FECHADO |

**R01–R10:** concluídos conforme checklist do Spec Kit. Nenhum achado C01–C05 I2 permanece aberto. O estado corresponde ao recorte de bots oficiais e infraestrutura efêmera, não aos 39 critérios amplos de implantação.

## Execução verificada
Commit de runtime `e7afd8a2ac7cb1ab45eeec2146ae828e56f93e0a` (10/10/2026). Todos os quatro workflows associados a esse SHA concluíram com **success**:

- [I2 — arena real](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207968): duas batalhas reais, dois abortos `after_containers`/`after_ready`, um `timeout-cleanup` observado e cleanup positivo. Auditor CI próprio reexecutado exigindo SHA e workflow esperados.
- [Spec Kit e backlog](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207983): planejamento, gates, projeções e validação de pré-requisitos.
- [Regressão I1](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207938): contratos e sondas finitas em runner descartável.
- [Autoria/motor real](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207943): testes e experimentos do editor e do motor, sem telefone físico nem entrada de aluno.

Reproduzidas **fora do GitHub Actions** seis suítes da fonte rastreada do run: 41 planejamento, 13 infra, 23 motor, 35 autoria, 187 segurança e 21 gateway, total **320 PASS**. Execução offline não iniciou Docker, bots, rede, VM nem processos não confiáveis; a prova de batalha foi a do CI descartável.

O artifact I2 `11672222277` foi baixado e sua integridade ZIP/CRC confirmada ao extrair cada entrada; **16 entradas**, **595.103 bytes**, SHA-256 do ZIP `96c19f1da8e3ddc259006f27c47bebc731873de649c2aec8c732fd4037f79058`. Arquivos de referência mantidos em [workflow I2](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059207968). Fonte exportada artifact `11672516551`, ZIP **352.695 bytes**, SHA-256 `2c60e85bbe6c695705ee2c196104c0e9a6aed0ed3edd2c86d41505e816f5d282`. O validador `validate_reconciled_batch` foi executado fora do CI contra fonte/run esperados e conferiu os **12 arquivos do manifesto**, 5 IDs únicos, hashes, gzip, eventos/rounds, pontuações, flags de escopo/cleanup, processos e timeout. Não é atestado independente por terceiro.

| Partida | Rounds | Spin Bot | Walls | Ticks | Origem |
|---|---:|---:|---:|---:|---|
| 1 | 3 | 274 | 175 | 3.386 | `GameEndedEventForObserver` |
| 2 | 3 | 311 | 125 | 2.701 | `GameEndedEventForObserver` |

Pontuações acima referem-se exclusivamente ao lote atual, não substituem relatórios históricos. O `recordings.battle.gz` contém eventos oficiais capturados pelo controlador: **não se demonstrou reprodução no GameRecorder/visualizador oficial**. Hash garante integridade de bytes, não honestidade de árbitro comprometido. O teste não é revisão independente de vulnerabilidades.

## Gate de conclusão e pendências
**I2-01..I2-09 e R01..R10: concluídos dentro do escopo experimental. Pendências I2 de severidade bloqueante abertas/inconclusivas: 0.** A redução a zero vem da matriz C01–C05, negativas reproduzidas e auditoria de evidência; não de suposição a partir de CI verde. Não há threads de review abertas nos PRs #18/#19/#21 na verificação de fechamento.

**Pendências FORA de I2 (não transferências de bugs I2):**
- **I3, ainda NÃO INICIADO:** broker autorizado, credencial de worker, admissão multiusuário, fila/ledger/idempotência, retry, quotas e suspensão duráveis.
- **I4:** VM do responsável, sistema/disco/rede guest, hardening/policies e provas específicas no host com autorização própria.
- **I5:** vinte ciclos, capacidade/quotas de produção, matriz integral TH, backup/restauração, revisão independente, runbook e homologação G-PROD.
- **S03/S04 e S04-T03:** baselines e ratificações amplas, aprovação institucional, telefone físico e validação pedagógica.

Sem alteração de Windows/WSL/Docker Desktop, .env, Compose, Postgres, firewall doméstico/roteador/VHDX, sem self-hosted runner e **sem liberação de alunos/endpoint público**. Todas as 39 tarefas de S04-T04 permanecem abertas no catálogo macro até sua conclusão integral. **I3 só deve começar por novo planejamento no Spec Kit, e não por declarar G-PROD aprovado.**

## Adendo posterior: fonte integrada, evidência final e limites (2026-10-10)

O código reconciliado e seu plano foram integrados no PR [#19](https://github.com/thalesvalente/project-robocopa-ifma/pull/19), merge `dfd9148d104bb016b5ee4082ef59849afc3109e9`. Árvores de `main` e do head `518a6709` coincidem byte a byte por hash de árvore Git. Após o relatório inicial, o lote do workflow [38059860067](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059860067) também passou no commit de fechamento `5f07d306`. Artefato `11672308059`, ZIP de 460.212 bytes, SHA-256 `27d4d17814729f1b1c5220ae4654dde5fc2d4ff23b7ac59ac2164bd22cb266b3`, 16 entradas e 12 arquivos de manifesto conferidos fora do runner. Duas batalhas reais de 3 rounds (Walls 267 × Spin Bot 153; Spin Bot 291 × Walls 202), dois abortos e um timeout real com cleanup. A reexecução não substitui os números dos lotes históricos acima. Não houve auditoria independente por terceiro nem mudança de gates de produção. [Relatório de integração](INTEGRACAO-PRs-2026-10-10.md).
