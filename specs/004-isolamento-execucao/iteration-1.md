# S04-T04 — Incremento 1: pesquisa, admissão e contenção verificável

**Data:** 2026-10-10. Plano inicial publicado no commit 0ecca28288ba9f71f754f618bbf2cae3d4226223, antes do primeiro código. **Estado atual:** incremento de código e provas de contenção aprovado no CI; integração de produção não concluída.

## Autorização e limites

D1: RoboDSL básica no MVP; intermediário/avançado pós-MVP. D2: o responsável aprovou VM Linux independente como direção preferencial. A instalação e a prova do Hyper-V/guest/rede do host não ocorreram.

D-005 separa G-EXP (módulos e sondas sintéticas finitas em CI descartável autorizados agora) de G-PROD (alunos e exposição bloqueados). Não instala VM nem altera Docker Desktop/WSL, .env, Compose, banco, firewall, VHDX ou projetos pessoais.

## Tasks e evidências

Os 39 IDs T001–T039 permanecem o catálogo de entregas amplas da feature 004. Os I1 abaixo detalham subconjuntos; não criam outro backlog macro nem encerram o restante de cada T.

| ID | Entrega e vínculo | Resultado verificável |
|---|---|---|
| I1-01 | Pesquisa oficial e revisão de premissas; T002,T003,T005; FR-005,FR-018 | CONCLUIDA: fontes Docker/Microsoft/GitHub/gVisor e upstream Tank Royale lidas; `docs/arquitetura/pesquisa-isolamento-2026-10-10.md` |
| I1-02 | Reconciliar D1/D2, plano e autorização; T001,T002; FR-020 | CONCLUIDA quanto ao incremento: D-005, clarifications e plan revisados. Não é ratificação geral S00/S03. |
| I1-03 | Contrato de admissão puro; T008,T009,T013,T014; FR-001,FR-002,FR-011 | CONCLUIDA no recorte: 32 testes; envelope estrito, registry de versões autorizadas, DSL básica, prazo/hash e descritor imutável. Não há autenticação pública/ledger. |
| I1-04 | Política de runtime antes de iniciar; T017,T018,T022; FR-005,FR-007,FR-008 | CONCLUIDA para perfil diagnóstico: 15 testes unitários e 20 invariantes verificadas em cada um dos 9 contêineres do CI. Não é perfil definitivo do motor. |
| I1-05 | Saída limitada durante leitura, timeout e cleanup; T024,T025,T031; FR-009,FR-010,FR-014 | CONCLUIDA no recorte: 8 testes de subprocesso e probes de OUTPUT_LIMIT/TIMEOUT; limpeza dos contêineres da invocação observada. Sem recovery durável. |
| I1-06 | Provas positivas/negativas sintéticas; T021,T022,T026; FR-018,FR-019 | CONCLUIDA para 9 cenários descritos abaixo, sem executar exploits ou usar dados pessoais; não equivale a todas TH-01..TH-16 ou aos 20 ciclos de homologação. |
| I1-07 | Verificar contrato upstream de separação bot/árbitro; T007,T020; FR-006,FR-012 | CONCLUIDA como pesquisa: externalServer não evita BooterManager local. A batalha com bot/árbitro separados continua tarefa pendente. |
| I1-08 | Regressões, inspeção e registro; T036,T037,T039; FR-020 | Lote de referência PASS: 164 testes unitários totais (55 novos), Spec Kit nativo e nove probes. Artifact baixado e conferido. Reconciliação de progresso possui regressão adicional separada. |

## Lote real de referência

[Run 38021817642](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38021817642), fonte bc82edbcb425ab0977635e891e536e46ae8fa66e; checkout sintético do PR f83eb616ccb8df8602de574d8ba44274775c10a8. Isso não significa merge na main. Ambiente: runner Ubuntu, Docker Engine 28.0.4/cgroups v2/kernel 6.17.0-1022-azure, não Windows pessoal.

**Nove casos:** baseline efetiva; filesystem; network=none; throttling CPU; limite PIDs; limite tmpfs; OOM de memória; timeout externo; volume de saída. Política reduzida: 64 MiB, swap extra zero, 0,5 CPU, 16 PIDs, tmpfs4MiB, coletor8KiB. Ver [relatório](../../docs/qualidade/evidencias/S04-T04-I1.md).

## Próximos incrementos necessários — não implementados

| Ordem | Escopo | Tarefas amplas / aceite |
|---|---|---|
| I2 | Bot e árbitro em fronteiras distintas; booter e segredos por papel; canal WebSocket mínimo e negativos de rede | T007,T011,T019,T020,T029; provar batalha real e impedir uso do canal controlador pelo bot |
| I3 | Broker autenticado, admissão multiusuário, fila, ledger/idempotência, retry e suspensão | T008–T016,T023–T025,T027–T035; não usar socket Docker na API, não duplicar pontuação |
| I4 | Preparação da VM real: versões/patches Windows/Desktop/Hyper-V/guest, VHDX e capacidade, switches/ACLs, drives ausentes, bootstrap e recuperação | T005,T006,T017,T022,T032,T035,T038; comandos de alteração dependem de execução/autorização consciente do responsável |
| I5 | Calibrar quotas de jogos, provar 20 ciclos/falhas, backup/restore, rastreabilidade, revisão de riscos e aceite | T026,T036–T039; sem liberar dados de alunos enquanto controles críticos pendentes |

A ordem I2/I3 pode usar CI descartável antes da instalação da VM. I4 não é substituído por resultados de contêiner no GitHub. Teste de telefone físico e requisitos pedagógicos continuam em S04-T03/S03. O intermediário/avançado não entra nesses incrementos do MVP.

## Nota posterior à execução do I1 — 2026-10-10

Esta página conserva o estado histórico da rodada I1; os incrementos indicados como futuros acima referem-se àquele momento. I2 foi posteriormente concluído **somente no escopo experimental**, reconciliado e integrado por meio do PR #19 na `main` (merge `dfd9148d`). [Evidências I2](../../docs/qualidade/evidencias/S04-T04-I2-RECONCILIACAO.md) e [integração](../../docs/qualidade/evidencias/INTEGRACAO-PRs-2026-10-10.md). I3, I4, I5 e o aceite completo S04-T04 seguem pendentes.
