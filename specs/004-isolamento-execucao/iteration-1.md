# S04-T04 — Incremento 1: pesquisa, admissão e contenção verificável

**Data:** 2026-10-10. **Estado:** planejado antes de implementar. Base: PR #16 / commit af6e0a08c1e51069c7ee8ec4c03168f0351c170d.

## Autorização e fronteira desta rodada

O responsável aprovou a VM Linux dedicada como direção preferencial, pediu pesquisa web para validar a decisão, planejamento com Spec Kit e início das implementações/testes. D1 permanece RoboDSL básica no MVP; níveis intermediário/avançado são pós-MVP. D2 está aprovada como **direção de arquitetura**, não como infraestrutura instalada, segura ou homologada.

A autorização permite componentes locais/offline e sondas sintéticas limitadas em runner GitHub-hosted descartável, sem executar programas recebidos de estudantes. Não instala VM, altera WSL/Docker Desktop, abre portas, muda firewall/roteador ou habilita produção no computador pessoal. CI não será descrito como teste do Hyper-V do responsável.

A regra antiga que exigia provar a segurança antes de implementar qualquer teste gerava um ciclo. Separar: G-EXP autoriza desenvolvimento e experimentos descartáveis nesta rodada; G-PROD continua bloqueado até testes, VM real, autenticação, backup e aceite humano. A constituição não é alterada.

## Sequência e tasks deste incremento

Os 39 IDs T001–T039 do plano anterior permanecem como catálogo macro de implementação da feature. Os itens I1 abaixo detalham um subconjunto, não substituem o backlog S00–S09. Todos começam pendentes.

| ID | Entrega verificável | Vínculo | Pré-requisito | Estado inicial |
|---|---|---|---|---|
| I1-01 | Pesquisar Docker/WSL/Hyper-V, privilégios, rede, recursos e fontes Tank Royale; registrar confirmação, ajustes e limites | T002,T003,T005; FR-005,FR-018 | Fonte primária | A_FAZER |
| I1-02 | Reconciliar D1/D2, Spec Kit, critérios e caminho de execução sem homologar produção | T001,T002; FR-020 | I1-01 | A_FAZER |
| I1-03 | Implementar contrato estrito de job de treino RoboDSL e rejeição de campos/linguagens/versões inesperadas | T008,T009,T013,T014; FR-001,FR-002,FR-011 | I1-02 | A_FAZER |
| I1-04 | Implementar política de sandbox e verificação antes de iniciar: usuário, mounts, rede, seccomp, limites e ausência de privilégios | T017,T018,T022; FR-005,FR-007,FR-008 | I1-02 | A_FAZER |
| I1-05 | Implementar transporte de saída com limite durante leitura, timeout e limpeza de recursos de sua própria invocação | T024,T025,T031; FR-009,FR-010,FR-014 | I1-04 | A_FAZER |
| I1-06 | Executar controles positivos/negativos sintéticos de arquivos, rede e quotas em contêineres descartáveis do CI, recusando Docker Desktop/WSL/local | T021,T022,T026; FR-018,FR-019 | I1-04,I1-05 | A_FAZER |
| I1-07 | Verificar contrato da separação bot/árbitro no upstream fixado e preparar prova de compatibilidade sem presumir suporte | T007,T020; FR-006,FR-012 | I1-01 | A_FAZER |
| I1-08 | Rodar regressão, conferir evidências, atualizar tasks/relatório e preservar aceites restantes | T036,T037,T039; FR-020 | I1-03..I1-07 | A_FAZER |

## Aceite e não objetivos

PASS de I1-06 deve indicar casos exatos, observações reais, versão/commit, quotas pequenas, timeout total e limpeza. Fixture que apenas imita negação não comprova contenção. Uma política lida por docker inspect não basta: controles positivos devem funcionar e negativos falhar por causa conhecida. Não testar exploits de kernel, acesso à rede residencial ou consumo ilimitado.

Mesmo com I1 concluído, permanecem: provisionar e testar a VM real; separar árbitro/bots em rede de jogo restrita; integrar broker autenticado; recuperação durável/idempotência; teste no telefone; avaliação de dependências; backup/restore; produção. Nenhuma dessas entregas será marcada PASS automaticamente.

## Pesquisa inicial — fontes oficiais a conferir

- Docker Engine security: https://docs.docker.com/engine/security/
- WSL e isolamento: https://docs.docker.com/desktop/features/wsl/
- Alertas de segurança: https://docs.docker.com/security/security-announcements/
- Recursos/swap: https://docs.docker.com/engine/containers/resource_constraints/
- Redes bridge: https://docs.docker.com/engine/network/drivers/bridge/
- Hyper-V redes: https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/plan/plan-hyper-v-networking-in-windows-server
- gVisor: https://gvisor.dev/docs/architecture_guide/security/
- Battle Runner: https://robocode.dev/api/battle-runner.html

Conclusões e implementação serão acrescentadas somente depois de leitura/testes efetivos.
