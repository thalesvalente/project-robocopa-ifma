# Implementation Plan — Isolamento de execução não confiável

**Data de revisão:** 2026-10-10 · **Feature:** [spec.md](spec.md) · **Branch:** `feat/s04-isolation-validation`.

**Status:** implementação experimental autorizada por D-005. **NÃO IMPLEMENTAR em produção nem liberar alunos antes de G-PROD.** O antigo bloqueio genérico foi separado em G-EXP (experimentos autorizados) e G-PROD (liberação pendente), evitando exigir testes aprovados antes de construir os testes.

## Summary e decisões

O MVP aceita apenas RoboDSL básica. A direção de uma VM Linux dedicada foi aprovada pelo responsável, com sistema, disco e daemon independentes; não é simplesmente outra distribuição WSL. Não houve instalação no host. Broker público sem Docker socket, worker segregado, sandbox por job e árbitro fora do ambiente do robô continuam o desenho alvo.

A pesquisa externa confirmou a direção e corrigiu premissas: mount/socket ausentes não eliminam outros acessos ao daemon; rede `internal` não é garantia de afastamento do host; `externalServer()` do Battle Runner 1.4.0 ainda inicia bots pelo BooterManager local; hashes consistentes não autenticam um árbitro comprometido. Fontes e distinção entre documentação e inferência estão em [pesquisa oficial](../../docs/arquitetura/pesquisa-isolamento-2026-10-10.md).

## Technical Context

| Elemento | Recorte atual |
|---|---|
| Ambiente de testes | Ubuntu 24.04 GitHub-hosted descartável; sem virtualização aninhada, dados pessoais ou credenciais da plataforma nos contêineres |
| Linguagem | Python stdlib para contratos/provas; RoboDSL 0.1 existente preservada |
| Motor | Tank Royale 1.4.0 e código upstream fixados; nova separação bot/árbitro ainda não implementada |
| Estado operacional | Laboratório Python pessoal continua somente localhost; novos módulos NÃO foram ligados à UI pública |
| Limites da bateria | 64 MiB RAM, sem swap extra, 0,5 CPU, 16 PIDs, 4 MiB tmpfs, saída de até 8 KiB; são limites das sondas, não quotas de jogos |
| Armazenamento | Sem migração de banco; relatórios sintéticos limitados e exclusivos por execução |
| Implantação futura | VM Linux dedicada aprovada como direção; patching, discos, switches, guest networking e recuperação ainda precisam de prova no host |

## Constitution Check

- Inclusão/pedagogia e escopo preservados: RoboDSL básica; intermediário/avançado pós-MVP.
- **G-EXP autorizado:** somente módulos offline e sondas fixas em runner descartável, com orçamento finito, sem teste adversarial na máquina pessoal.
- **GATE BLOQUEADO — G-PROD:** faltam VM real, isolamento bot/árbitro, broker, autenticação, limites de partidas calibrados, backup, recuperação e aceite humano.
- Teste de CI não comprova Hyper-V do host. Configuração declarada não substitui inspeção de runtime nem prova negativa. Uma prova aprovada não demonstra ausência de vulnerabilidades desconhecidas.
- A aprovação D1/D2 e o início de experimentos não homologam a constituição S00-T06 ou os requisitos S03.

## Planejamento completo e dependências

O catálogo [tasks.md](tasks.md) preserva 39 tarefas T001–T039 com IDs FR/SC/TH. [iteration-1.md](iteration-1.md) foi publicado antes do primeiro código e detalha o incremento autorizado. Os checkboxes amplos continuam abertos enquanto houver escopo de produção não entregue; a evidência parcial é vinculada em I1.

| Etapa | Tarefas | Critério de saída e dependência |
|---|---|---|
| 0. Fontes, autorização e ameaças | T001–T004 | Registrar D1/D2 e G-EXP; riscos/limites explícitos. Demais ratificações de produto permanecem em paralelo. |
| 1. Fronteira e compatibilidade | T005–T007 | VM própria e canal bot/árbitro demonstrados. I1 apenas testa contenção de contêiner no CI e verifica o contrato upstream. |
| 2. Plano de controle | T008–T012 | Contratos estritos, broker autenticado e política desligada por padrão. I1 implementa o contrato puro, não o broker. |
| 3. Admissão | T013–T016 | Entradas/AST/versões inválidas negadas antes de execução; autorização de usuário precisa da plataforma. |
| 4. Sandbox por job | T017–T022 | Imagens verificadas, mounts/privilégios bloqueados, redes efetivas e árbitro segregado. Sem publicar rede por conveniência. |
| 5. Recursos e falhas | T023–T027 | Quotas reais, cancelamento, recuperação durável, 20 ciclos sem órfãos e controle de fila/abuso. |
| 6. Integridade | T028–T032 | Resultado do árbitro independente, hashes/identidades/rounds e ledger idempotente; hash sozinho não é autenticação. |
| 7. Suspensão e operação | T033–T035 | Fail-closed, nenhum fallback ao host e runbook de rollback específico. |
| 8. Homologação | T036–T039 | Matriz de ameaças, regressões, smoke da VM por ação autorizada do responsável e revisão dos riscos; só então decidir liberação. |

**Caminho de experimentação:** pesquisa → contrato/política → provas descartáveis → separação bot/árbitro → worker/broker → VM real e recuperação → revisão/liberação. Contratos e testes sintéticos podem ser construídos antes da prova final da VM; não são autorização de uso por alunos.

## Incremento I1 — código e medição

- `services/worker_agent/contracts.py`: envelope estrito, JSON sem campos duplicados/NaN, IDs/hashes/deadline, lista de versões autorizadas fornecida pelo plano de controle, RoboDSL básica e descritor imutável. Desabilitado por padrão. Não autentica usuário nem mantém ledger.
- `services/worker_agent/policy.py`: perfil de teste e 20 invariantes pré-start de Docker; imagem content-ID, ownership, mounts, redes, capabilities, RAM/swap/CPU/PIDs/logs/tmpfs.
- `services/worker_agent/bounded.py`: subprocesso sem shell, limite de saída durante leitura, prazo externo e limpeza do grupo de processo da invocação; é componente POSIX, não sandbox por si.
- `spikes/isolamento/probes/`: nove sondas sintéticas com controles positivos/negativos, cgroups e seccomp efetivos, memória/processos/disco pequenos. Sem código de estudantes, kernel exploits ou varredura externa.
- `scripts/run_isolation_checks.py`: recusa Windows/WSL/Desktop/local; exige contexto descartável, não encaminha credenciais, verifica ownership antes de remover somente seus recursos. Essa trava evita uso acidental, não é atestado criptográfico do host.
- `tests/security/`: 55 testes iniciais dos módulos, separados das nove provas Docker reais.

## Complementos necessários encontrados na pesquisa

- Antes da VM: inventário de versões do **produto Docker Desktop**, Windows/WSL/Hyper-V e Linux guest; Engine 28.1.1 não informa a versão Desktop. Revisar avisos oficiais e backups antes de qualquer atualização.
- Definir switch/ACLs do Hyper-V: Internal permite host↔VM; Private impede esse canal e exige solução própria para o controle. A topologia precisa permitir só o necessário, não simplesmente esconder portas publicadas.
- Investigar inicialização de bots sem dar Docker socket ao booter. `externalServer()` não externaliza processos de bot. Provar segredos de bots e de controlador distintos contra versão 1.4.0.
- Revisar SBOM/artefatos/runtime; digest fixa bytes, não ausência de CVE. Rootless/gVisor são camadas opcionais sujeitas à compatibilidade, não um requisito de complexidade por si.
- Medir memória+swap, stdout/stderr e espaço do arquivo de VM; testes de 64 MiB não definem recursos de partidas.

## Estrutura de documentação e implementação

Feature 004 mantém spec, clarifications, research, data-model, contracts, tasks, analysis e checklists. O mapeamento de caminhos do plano anterior para o incremento é explícito: `services/worker-agent/` era destino proposto; o módulo Python deste incremento usa `services/worker_agent/`. Nenhum serviço de produção foi substituído silenciosamente.

[Contrato](contracts/job-protocol.md) · [Modelo de dados](data-model.md) · [Ameaças](../../docs/arquitetura/ameacas-sandbox.md) · [ADR-004](../../docs/arquitetura/ADR-004-isolamento-execucao.md).

## Rollback e limites de aceite

Em falha, negar novas execuções; não usar Docker Desktop pessoal como fallback. Limpeza apenas dos recursos com identidade/label da execução. Nenhum prune global, down -v, ajuste de firewall, VHDX ou compartilhamento de drives faz parte desta rodada. A VM preferida e os controles de CI reduzem riscos específicos, mas não aprovam a recepção de alunos. Critérios finais continuam em [security-gates.md](checklists/security-gates.md).
