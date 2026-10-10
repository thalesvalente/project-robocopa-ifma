# Incremento I1 — testes limitados de contenção

**Uso de runtime somente em GitHub-hosted Ubuntu descartável. Não executar probes/probe.py diretamente nem contornar a recusa no Windows/WSL/Docker Desktop.**

## O que foi construído

Admissão de um envelope interno de treino básico em `services/worker_agent/contracts.py`; perfil de runtime em `policy.py`; subprocessos com saída limitada durante leitura em `bounded.py`; nove probes sintéticos finitos orquestrados por `scripts/run_isolation_checks.py`. O novo código não altera nem substitui o servidor pessoal `serve_mobile_spike.py`.

## Verificações offline

Na raiz de uma cópia da branch, `python -m unittest discover -s tests/security -v` verifica contratos e política com fixtures. Os testes de subprocesso são POSIX e não executam Docker; Windows ignora essa classe. Aprovação offline não comprova runtime.

## Provas no CI

O workflow `isolation-validation.yml` usa dois jobs de runner descartável e sem segredos fornecidos aos contêineres: regressão/contratos e runtime limitado. Imagem de probe fixada por digest da base, política de cgroups v2, nenhum mount do host, rede none, usuário 10001, sem capabilities e sem log persistente.

| Caso | Prova |
|---|---|
| baseline | UID, capabilities, no-new-privileges, seccomp e limites efetivos em cgroups |
| filesystem | /tmp permitido, rootfs realmente read-only, canário sintético criado no runner não visível no contêiner, sockets/segredos ausentes |
| network | Loopback funciona; nenhuma interface externa; rota para endereço TEST-NET recusada sem tráfego externo; raw socket negado |
| cpu | Progresso finito com throttling observado |
| pids | Até 24 tentativas finitas sob limite 16; recusa EAGAIN e filhos recolhidos |
| tmpfs | Até 8 MiB solicitados para tmpfs 4 MiB; recusa ENOSPC |
| memory | Uma alocação de 96 MiB sob limite 64 MiB/sem swap extra; observar OOMKilled e exit137 |
| timeout | Sleep finito interrompido por watchdog externo; remover o contêiner com seu descendente |
| output | Fixture produz no máximo 1 MiB; coletor interrompe após limite de 8 KiB |

O harness verifica 20 propriedades antes de iniciar cada contêiner, coleta somente JSON limitado e remove apenas os recursos com label/ID da própria invocação. Não há limpeza global de imagens ou volumes. A imagem de referência fixada é reprodutível, não um atestado de ausência de CVEs.

## Limitações

A trava de ambiente é proteção contra uso acidental, não autenticação criptográfica do runner. Testes de negação sem rede não comprovam a futura rede de jogo com WebSocket. Não foram testados escapes de kernel, Hyper-V do responsável, 20 ciclos de recuperação, autenticação/filas/ledger, isolamento de bot contra árbitro ou dados reais de alunos.

A função de admissão não lança processos nem autentica usuários: recebe do plano de controle uma lista previamente autorizada de hashes/versões. Campo idempotency_key é validado, mas deduplicação persistente ainda não existe. As cotas do perfil são para as sondas; não servem para iniciar uma JVM de competição.

## Saídas

O CI publica somente `.local/security-i1/<run>/report.json`, com commit, imagem, kernel/Engine do runner, status por caso, controles observados e cleanup. Não inclui arquivos pessoais nem snapshots de ambiente completo.

Planejamento: `specs/004-isolamento-execucao/iteration-1.md` e `tasks.md`. Relatório: `docs/qualidade/evidencias/S04-T04-I1.md` após validação efetiva.
