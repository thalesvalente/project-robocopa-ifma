# Clarify — decisões e lacunas de isolamento

**Revisão:** 2026-10-10. Fontes: decisões do responsável, código do projeto e [pesquisa oficial](../../docs/arquitetura/pesquisa-isolamento-2026-10-10.md).

`DECIDIDO_ESCOPO` e `DIRECAO_APROVADA` registram decisões do responsável; `CANDIDATO` e `ABERTO` não são aprovação. Nenhuma decisão declarada aprovada por existência do documento.

| ID | Questão | Estado e encaminhamento | Classificação | Referência |
|---|---|---|---|---|
| Q-01 | Expor o servidor Python local? | Não: processo pessoal acessa Docker; manter em localhost, sem túnel/LAN. | RESOLVIDO_PELA_FONTE | Constituição, laboratório 003 |
| Q-02 | Linguagem do primeiro MVP? | Apenas RoboDSL básica. Intermediário, avançado e blocos depois do MVP. Gramática/aceite pedagógico ainda precisam da baseline. | DECIDIDO_ESCOPO | D-004 |
| Q-03 | Qual fronteira preferida? | VM Linux independente, daemon e discos próprios, sem drives pessoais. O responsável aprovou a direção; não foi instalada. Outra distribuição WSL não equivale a VM independente. | DIRECAO_APROVADA | D-005; fonte Docker WSL |
| Q-04 | WebSocket sem expor host/LAN? | Definir rede de jogo e canal de controle com destinos mínimos, testar positivos/negativos. Provas network=none não validam essa futura rede. | ABERTO | T007,T011,T019 |
| Q-05 | Separar bot e árbitro? | Sim como objetivo técnico; BattleRunner 1.4.0 ainda usa BooterManager local com servidor externo. Prova de inicialização e segredo de controlador inacessível ao bot é necessária. | ABERTO | T007,T020; upstream fixado |
| Q-06 | CPU/RAM/swap/PIDs/tmpfs/tempo? | Sondas I1 usam 0,5 CPU/64 MiB/sem swap/16 PIDs/4 MiB para testar enforcement, não dimensionar jogos. Quotas finais dependem de medição. | CANDIDATO | T023–T027 |
| Q-07 | Como pedir execução? | Contrato puro implementado no I1; futuro broker autenticado entrega somente versão aprovada, sem comando shell, Docker flags ou socket. Transporte e autenticação continuam pendentes. | ABERTO | T008–T012 |
| Q-08 | Retenção de dados/logs? | Dados sintéticos no CI. Retenção institucional e dados de alunos a definir antes do piloto. | ABERTO | FR-014; S03/S08 |
| Q-09 | Resultado honesto? | Hash e replay verificam consistência, não autenticidade se o bot controlar árbitro/manifesto. Separação, identidade e ledger ainda são necessários; issue #15 trata empate. | CANDIDATO | T020,T028–T032 |
| Q-10 | Rootless/userns/gVisor? | Camadas opcionais a medir dentro da VM, sem complexidade automática no MVP; fixar digest não elimina revisão de CVEs. | ABERTO | T005,T017,T032 |
| Q-11 | Onde testar? | Módulos offline e sondas sintéticas finitas em GitHub-hosted descartável autorizados agora. Não testar no Docker pessoal nem instalar VM automaticamente. | EXPERIMENTO_AUTORIZADO | D-005, G-EXP |
| Q-12 | Quando liberar alunos? | Somente após VM real, rede/árbitro/broker, identidade, backup/recuperação e aceite. Nenhum dos nove testes isolados dá essa liberação. | RESOLVIDO_PELA_FONTE | G-PROD; S08 |

## D1–D5 e separação de gates

1. **D1:** decidido o recorte de linguagem básica; sem ampliação de sintaxe nesta rodada.
2. **D2:** direção VM dedicada aprovada. Instalação e verificação do Hyper-V/guest/rede/discos permanecem pendentes.
3. **D3:** objetivo de separar árbitro e bot; viabilidade técnica ainda em investigação. Não precisa transformar toda escolha de implementação em nova aprovação conceitual, mas não homologar topologia sem teste.
4. **D4:** testes pequenos e descartáveis autorizados; quotas de jogos e recuperação de produção só após medição.
5. **D5:** liberação pública continua bloqueada. Nenhum aceite de alunos ou dados institucionais foi inferido.

**G-EXP** permite implementar e testar controles para produzir evidência. **G-PROD** exige que a evidência demonstre a arquitetura alvo antes de alunos. Assim eliminamos o ciclo de exigir segurança já testada antes de iniciar testes, mantendo a proteção da máquina pessoal.

Registro: [D-005](../../docs/planejamento/decisoes/D-005-vm-e-experimentos-controlados.md). O plano anterior era preparatório; esta revisão autoriza apenas o incremento delimitado, sem apagar a necessidade de ratificação S03/S04 e revisão de operação.
