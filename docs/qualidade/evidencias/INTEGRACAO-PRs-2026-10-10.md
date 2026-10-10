# INTEGRACAO-PRs — Registro de integração técnica até I2 (2026-10-10)

**Escopo:** PRs #11, #12, #13, #14, #16, #17 e #19. **Resultado do merge:** PASS (sete integrados), zero PRs abertos. **Produção:** NÃO homologada. **I3:** NÃO iniciado.

## Método e resultado no GitHub

Merges nativos do GitHub, todos no método `merge`, sem squash/rebase/force-push. Antes de cada merge: base retarget `main` depois de seu antecessor, head SHA confirmado, diff incremental conferido (mesmo conjunto de arquivos da base anterior) e `mergeable=clean`. PRs originalmente draft foram marcados como ready exclusivamente para viabilizar os merges autorizados. Nenhum PR alternativo foi mesclado.

| PR | Descrição | SHA do merge |
|---|---|---|
| #11 | Fundação e Spec Kit | `920b88599153464163e375ab027e5af3f79efae8` |
| #12 | Laboratório Compose | `dc93925a684a3d81463bd563e478a51f95694183` |
| #13 | Tank Royale | `530c03ab537b6a07f43bde20fcaabe866a24eda3` |
| #14 | Autoria responsiva | `0788014a749ce89eede03a066d9706b62e2b4e14` |
| #16 | Spec Kit de isolamento | `883c8c163bc9561bf97306768a84b0b0a8446f0f` |
| #17 | I1 contenção | `d64ac53ec6efc383764179905917ce3eb997900b` |
| #19 | I2 reconciliado | `dfd9148d104bb016b5ee4082ef59849afc3109e9` |

As dez PRs registradas no GitHub estão `closed`. #18, #20 e #21 foram fechadas SEM merge (branches e commits preservados). `main` na data desta auditoria: `dfd9148d104bb016b5ee4082ef59849afc3109e9`. Árvore Git: `38d17596d854cc6d7595849f033694145bca07d5`, idêntica à árvore do head PR #19 `518a6709dd9b411beb64a23bd21b32f3c0d4d46b`. Essa identidade comprova integridade do conteúdo consolidado, não revisão independente de segurança.

## Testes e evidências conservadas

- O workflow de planejamento passou em cada um dos sete commits de merge da `main`. O run [38060749180](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38060749180), pertencente ao merge #19, terminou `success`.
- Head final do PR #19, de árvore idêntica à da `main`, executou com `success` os quatro workflows: [Spec Kit](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38060749180) e regressões de segurança, autoria e arena em seu histórico; [I2 fonte auditada](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38059860067) no commit `5f07d306`. A nota acima do Spec Kit linka o workflow de planejamento da `main`, não uma execução do I2.
- O gate do I2 permanece restrito aos experimentos com bots oficiais, duas batalhas, abortos e timeout, auditoria própria de 12 arquivos, e 320 testes locais documentados. Os lotes de referência não foram reescritos. Não se declara validação com código não confiável de estudantes.
- A própria PR de pós-integração modifica documentação e um plano de reconciliação, acionando testes de Spec Kit/I1/I2/autoria. O encerramento dependerá de resultados dessas verificações; a fonte dessa PR não muda o runtime.

## Limites e pendências legítimas

- I1 e I2: escopo experimental fechado e documentado; macro S04-T04 continua `EM_EXECUCAO`, 39 tarefas amplas não dadas como concluídas.
- S00-T06: ratificação humana da constituição e gates continua `BLOQUEADA`.
- I3: broker autenticado, fila/ledger, idempotência e recuperação, ainda não iniciados.
- I4: VM/host pessoal não inventariados/implantados neste merge, sem autorização implícita.
- I5: vinte ciclos, quotas operacionais, backup/restauração, matriz de segurança e revisão independente ainda abertos.
- `G-PROD` BLOQUEADO; sem endpoint público, estudantes, credenciais reais, instalação de VM, mudanças em Docker Desktop/WSL/.env/Compose/Postgres/firewall/VHDX/roteador ou serviços pessoais.

Registro de processo: [plano de integração](../../docs/planejamento/INTEGRACAO-PRs-2026-10-10.md).
