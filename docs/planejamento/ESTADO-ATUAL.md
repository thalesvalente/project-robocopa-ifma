# Estado atual — pesquisa, autoria e primeiro incremento de isolamento

**Atualizado:** 2026-10-10. **Trabalho corrente:** S04-T04, incremento I1 implementado e testado em ambiente descartável. VM dedicada aprovada como direção, ainda não instalada. Não há liberação para alunos.

## Repositório e decisões

PRs empilhados: #11 fundação/Spec Kit; #12 laboratório Compose; #13 motor de referência; #14 autoria responsiva; #16 especificação de isolamento; **#17 pesquisa oficial e primeiro incremento de segurança** (`feat/s04-isolation-validation`, base #16). Não houve merge na main.

Spec Kit v1.1.2 permanece fixado em `959e866caa3618bf3dc290d5dca33394365af9c6`. Sua estrutura versionada e verificador nativo são usados; não é uma conexão MCP nativa ou invocação fictícia de slash commands.

O backlog `docs/planejamento/backlog.json` continua canônico: dez sprints, sessenta tarefas. O publicador restrito do PR #17 reconcilia somente **S04-T04 para EM_EXECUCAO**, regenera as visões e não encerra nenhuma tarefa. S00-T01–T05 já têm entregas técnicas; S00-T06, S03 e revisão arquitetural integral continuam pendentes. Minutas S01/S02 existem, sem pesquisa de campo ou aprovação institucional presumida.

**D1:** somente RoboDSL básica no MVP; intermediário, avançado e blocos no pós-MVP. **D2:** VM Linux com daemon/disco próprios e sem drives pessoais é direção aprovada pelo responsável. Registro: D-004 e D-005. D3/limites de D4 precisam de provas, D5 continua bloqueando produção.

## Evidências anteriores preservadas

- Laboratório Compose executado pelo responsável no Windows: Postgres e sonda healthy, redes/volume próprios, loopback18080. `docs/qualidade/evidencias/INFRA-LOCAL-HOST.md`.
- Referência Tank Royale 1.4.0: CI documentado no run38004097096; reprodução Windows informou Walls391 × Spin Bot364, cinco rounds,5255ticks,10718ms,PASS. `TANK-ROYALE-HOST.md`. Replay/manifesto dessa rodada local não foram anexados.
- Autoria: editor/RoboDSL em Chromium emulado e motor real passaram no CI. Capturas locais mostraram Sentinela536 × Walls226, velocidade0; Explorador188 × Walls188, velocidade5,47, movimento94,3%. `AUTORIA-MOBILE-HOST.md`. Não é auditoria independente dos arquivos locais nem teste em celular físico. Empate com ranks distintos está na issue#15, sem defeito confirmado.

## Pesquisa externa e correções aplicadas

Fontes oficiais Docker, Microsoft, GitHub, gVisor e código Tank Royale fixado sustentam a direção da VM, com ressalvas. Outra distribuição WSL compartilha kernel; bridge/internal não garante rede inacessível ao host; ausência de socket não elimina todos os canais do daemon; externalServer do runner não separa automaticamente os processos de bot; hash sozinho não autentica um resultado produzido em ambiente comprometido.

Relatório: `docs/arquitetura/pesquisa-isolamento-2026-10-10.md`. Atualizações do produto Docker Desktop precisam ser avaliadas separadamente do Engine28.1.1 informado pelo responsável. Não declarar a máquina vulnerável sem conhecer a versão/configuração do produto.

## S04-T04 / I1 — código e provas reais

Plano publicado antes do código: `specs/004-isolamento-execucao/iteration-1.md`, oito subentregas vinculadas às 39 tarefas amplas T001–T039. G-EXP permite engenharia e testes sintéticos descartáveis; G-PROD continua bloqueado. Nenhum teste adversarial foi executado no computador pessoal.

Implementados: `services/worker_agent/contracts.py` (admissão estrita, não autenticação/ledger), `policy.py` (perfil diagnóstico e inspeção), `bounded.py` (limites durante leitura/tempo), harness e probes fixos. Nenhuma ampliação da RoboDSL nem integração pública foi feita.

Lote conferido: [run38021817642](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38021817642), fontebc82edb. **164 testes unitários OK, sendo55 novos**, Spec Kit nativo PASS e **nove provas reais** de baseline, arquivos, rede, CPU, PIDs, tmpfs, memória, timeout e stdout. Vinte invariantes antes de iniciar cada contêiner; todos removidos ao final. O artifact foi baixado e verificado por SHA256/CRC/JSON. Evidência detalhada: `docs/qualidade/evidencias/S04-T04-I1.md`.

A bateria roda em GitHub-hosted Ubuntu e recusa execução local/WSL/Desktop. Não valida a VM, rede ou Hyper-V do Windows. Os limites pequenos das sondas não são limites aprovados de partidas. A reconciliação de progresso possui três testes adicionais aos164 do lote histórico.

## O que permanece pendente

**Próxima prioridade técnica:** separação real bot/árbitro e canal WebSocket mínimo com papéis/segredos distintos. Depois: broker autenticado, fila durável, ledger/idempotência, política de imagens/patches, limites do motor, rate-limit, vinte ciclos de falha/limpeza, inventário/provisionamento da VM, backup/restore, revisão e aceite.

S04-T03 ainda requer uso em telefone físico e revisão pedagógica. Sem contas, inscrições/competição completas, piloto ou MVP homologado. A segurança é prioridade antes dessas expansões; níveis intermediário/avançado não entram agora.

Não foram alterados Docker Desktop/WSL, .env, Compose, Postgres, firewall, VHDX, roteador ou serviços pessoais. O servidor 18081 do laboratório continua com acesso à CLI Docker e **não deve ser exposto**. Não foi usado Codex/R4; não foi criada sessão remota na máquina do responsável.
