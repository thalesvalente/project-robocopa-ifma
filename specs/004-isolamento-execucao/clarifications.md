# Clarify — decisões, pressupostos e dúvidas de S04-T04

**Data:** 2026-10-09 · **Status:** pré-esclarecimento técnico para revisão, não entrevista nem ratificação do responsável.  
**Origem:** constituição proposta, ADRs 001–003, scripts e evidências das features 001–003 e pedido atual.

Regra: `RESOLVIDO_PELA_FONTE` significa que o projeto já estabelece o limite; `CANDIDATO` é proposta ainda não aprovada; `ABERTO` exige investigação/decisão antes da execução.

| ID | Questão | Proposta ou evidência | Estado | Responsável / gate |
|---|---|---|---|---|
| Q-01 | Podemos expor o servidor de laboratório Python aos alunos? | **Não**: porta 127.0.0.1, processo do host com acesso à CLI Docker; não é autenticação pública. | RESOLVIDO_PELA_FONTE | Constituição III e ADR-002 |
| Q-02 | Qual código de estudante é autorizado no primeiro MVP? | RoboDSL restrita é **candidata**; Java/JS livre deve continuar bloqueado, sujeito à ratificação pedagógica. | CANDIDATO | Responsável; S03, S04-T03 |
| Q-03 | Docker Desktop/WSL 2 compartilhado pode ser fronteira final? | **Não assumir**. Propor VM Linux exclusiva do executor, com daemon e credenciais independentes; avaliar alternativa externa caso falhe. | CANDIDATO | Responsável; S04-T01/T05 |
| Q-04 | Como executar Tank Royale com tráfego WebSocket sem rede externa? | Medir comunicação árbitro↔bot em rede isolada do worker, com regras de saída estritas. O `--network none` do spike não comprova essa nova topologia. | ABERTO | Equipe técnica; T011 |
| Q-05 | Engine e bot podem compartilhar a mesma fronteira? | Risco à integridade do árbitro. Preferir processos/contêineres distintos dentro da VM; verificar possibilidade de usar servidor externo e controlar inicialização dos bots. | ABERTO | Equipe técnica; T010–T012 |
| Q-06 | Quais quotas de CPU/RAM/PIDs/disco/tempo/concorrência? | Usar as quotas do laboratório apenas como **pontos iniciais de medição**, nunca SLA ou limite final. | ABERTO | Responsável após testes de carga |
| Q-07 | Como o plano de controle solicita execução sem conceder acesso ao Docker? | Worker segregado recebe contrato tipado por broker autenticado, sem socket nem comando livre nas rotas públicas. Transporte concreto depende da arquitetura de deployment. | CANDIDATO | S03/S04; T008–T010 |
| Q-08 | Quais dados e logs podem ser retidos? | Mínimo técnico sem identificação de alunos; prazos de retenção, LGPD e operação institucional a validar. | ABERTO | Responsável/instituição, S03/S08 |
| Q-09 | Que tipo de evidência comprova resultados honestos? | Hash de versão+motor+política, replay verificado e transições idempotentes; apuração de empates em issue #15/S03-T03. | CANDIDATO | Requisitos de competição |
| Q-10 | É possível usar rootless Docker, userns-remap ou gVisor? | Testar compatibilidade no Linux segregado; não instalar no Docker Desktop existente por decisão implícita. Não confundir camada extra com segurança absoluta. | ABERTO | Prova de viabilidade, T005 |
| Q-11 | Podemos fazer ataques controlados na sua máquina pessoal? | **Não nesta rodada**. Somente em runner/VM descartável sem dados pessoais, com autorização específica para o ambiente alvo. | RESOLVIDO_PELA_FONTE | Constituição, AGENTS |
| Q-12 | Quando liberar alunos e rede externa? | Somente após gates de segurança, identidade/autorizações, backup, TLS e aceite humano; se falhar, manter apenas demonstração com referências confiáveis. | RESOLVIDO_PELA_FONTE | S04-T04, S08 e responsável |

## Decisões que bloqueiam implementação

1. **D1:** aceitar/ajustar o modelo de confiança T0/T1/T2 e escopo da RoboDSL.
2. **D2:** aprovar a fronteira de isolamento (VM exclusiva, worker externo ou alternativa comprovada).
3. **D3:** decidir a separação efetiva bot/árbitro e o canal WebSocket permitido.
4. **D4:** validar limites, testes de abuso autorizados e plano de recuperação.
5. **D5:** ratificar critérios para liberar produção com estudantes — após S03 e revisão independente.

**Estado:** nenhuma dessas decisões foi tomada automaticamente em nome do responsável. A documentação é útil para revisão; a implementação de executor para entradas não confiáveis continua bloqueada.
