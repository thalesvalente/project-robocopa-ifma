# Clarify — decisões e lacunas de isolamento

**Revisão:** 2026-10-10. Fontes: decisões do responsável, código, [pesquisa oficial](../../docs/arquitetura/pesquisa-isolamento-2026-10-10.md) e [prova I2](../../docs/qualidade/evidencias/S04-T04-I2.md).

`DECIDIDO_ESCOPO` e `DIRECAO_APROVADA` registram decisões humanas. `VERIFICADO_NO_CI` limita-se ao experimento; `CANDIDATO` e `ABERTO` não são aprovação de produção. Nenhum documento por si homologa segurança.

| ID | Questão | Estado e encaminhamento | Classificação | Referência |
|---|---|---|---|---|
| Q-01 | Expor o servidor Python local? | Não: processo pessoal acessa Docker; localhost sem túnel/LAN. | RESOLVIDO_PELA_FONTE | Constituição, laboratório003 |
| Q-02 | Linguagem do primeiro MVP? | Apenas RoboDSL básica; intermediário/avançado/blocos depois. Gramática/aceite pedagógico ainda precisam da baseline. | DECIDIDO_ESCOPO | D-004 |
| Q-03 | Qual fronteira preferida? | VM Linux independente, daemon/discos próprios e sem drives pessoais; direção aprovada, não instalada. Outra distribuição WSL não equivale a VM independente. | DIRECAO_APROVADA | D-005 |
| Q-04 | WebSocket sem expor host/LAN? | I2 demonstrou bridge owned + ACLs dentro dos namespaces, gateway7654 permitido e acesso a host/peer/7655/DNS/IPv6 negado nos dois bots. Prova no runner não valida a rede da VM real. | VERIFICADO_NO_CI | I2; T007/T011/T019; I4 pendente |
| Q-05 | Separar bot e árbitro? | Duas batalhas reais com três contêineres e namespaces distintos. Cliente oficial de protocolo evita BooterManager local; filtro de mensagens protege comandos após handshake. Nenhum bot no árbitro. Falta reproduzir na VM alvo e revisar produção. | VERIFICADO_NO_CI | I2/N5; T007/T020 |
| Q-06 | CPU/RAM/swap/PIDs/tmpfs/tempo? | I1 usa perfil pequeno; I2 usa1CPU por papel, árbitro1GiB/bots512MiB/128PIDs/tmpfs128MiB e quotas de sessão. São orçamentos de experimento, não capacidade aprovada. | CANDIDATO | T023–T027; I5 |
| Q-07 | Como pedir execução? | Contrato puro existe no I1; futuro broker autenticado deverá entregar versão aprovada, sem shell/Dockerflags/socket. Transporte, identidade e ledger completo continuam pendentes. Há plano I3-01 para fila local experimental, sem autenticação, HTTP ou worker remoto. | ABERTO | I3; T008–T012 |
| Q-08 | Retenção de dados/logs? | Apenas dados sintéticos no CI; retenção institucional/dados de alunos a definir antes do piloto. | ABERTO | FR-014; S03/S08 |
| Q-09 | Resultado honesto? | I2 confirma fronteira e consistência de eventos/replay/identidades/tipos/hashes. Não autentica árbitro comprometido; ledger e autoria do pedido ainda faltam. Empate segue issue15. | CANDIDATO | I2/I3; T020/T028–T032 |
| Q-10 | Rootless/userns/gVisor? | Camadas opcionais a medir na VM; não ampliar complexidade do MVP automaticamente; digest não elimina revisão de vulnerabilidades. | ABERTO | T005/T017/T032 |
| Q-11 | Onde testar? | Módulos e provas sintéticas finitas no GitHub-hosted efêmero autorizados; nenhum teste no Docker pessoal nem instalação automática. | EXPERIMENTO_AUTORIZADO | D-005/G-EXP |
| Q-12 | Quando liberar alunos? | Após VM real, broker/identidades, rede/árbitro revistos, backup/recuperação e aceite. I1/I2 isoladamente não dão liberação. | RESOLVIDO_PELA_FONTE | G-PROD/S08 |

## D1–D5 e separação de gates

1. **D1:** decidido o recorte de linguagem básica, sem ampliação nesta rodada.
2. **D2:** VM dedicada aprovada como direção; instalação e Hyper-V/guest/rede/discos pendentes.
3. **D3:** separação e comunicação restrita demonstradas em duas batalhas do CI. A adoção definitiva na VM pessoal e a liberação da arquitetura completa continuam pendentes.
4. **D4:** testes pequenos autorizados; dois abortos parciais/cleanup comprovados. Quotas de produção, vinte ciclos, reboot, fila e recovery durável ainda precisam de I3–I5.
5. **D5:** produção e alunos bloqueados; nenhum aceite institucional inferido.

**G-EXP** permite engenharia para produzir evidência; **G-PROD** exige a arquitetura alvo validada antes de alunos. I2 não homologa S00/S03 nem o laboratório público. [D-005](../../docs/planejamento/decisoes/D-005-vm-e-experimentos-controlados.md).

**Complemento Q-07 (2026-10-10):** o [plano I3](iteration-3.md) e [decisões G-EXP](i3-design-decisions.md) autorizam SOMENTE implementação offline de fila de laboratório com gate desligado. Isso não resolve a decisão sobre identidade mútua, credenciais de serviço e transporte do broker↔worker. I3-02 deve resolver e testar Q-07 ANTES da primeira entrega de jobs remota; nenhuma autenticação de estudantes é presumida.
