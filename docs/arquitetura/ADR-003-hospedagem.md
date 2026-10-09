# ADR-003 — Hospedagem própria, local e segregada

**Data:** 2026-10-09 · **Estado:** topologia candidata/experimento preparatório.  
**Relacionamento:** S00-T05, S04-T05 (não concluída), S08.

## Inventário e implicações (dados sanitizados)

O responsável confirmou Windows 11 Pro, Docker Engine 28.1.1 em Linux, Compose 2.35.1, WSL 2 com Ubuntu e docker-desktop e execução de contêiner `hello-world`. CPU/ram são suficientes para iniciar experimentos pequenos; isso **não estima capacidade real de competição**. A unidade onde reside o repositório tem pouco espaço livre. Há projetos e serviços Docker existentes que não podem ser modificados. As medições específicas não são publicadas em arquivos de produção.

O `DockerRoot=/var/lib/docker` é caminho do ambiente Linux, **não identifica o volume do Windows** que hospeda o VHDX do Docker Desktop. O local deve ser confirmado na interface do Docker Desktop antes de qualquer migração. Uma unidade com mais espaço livre foi identificada, mas não será utilizada automaticamente.

## Topologia alvo — etapas

```text
Etapa A (este PR; somente localhost):
  Windows 11 Pro / Docker Desktop / WSL2
  localhost:18080 -- TCP HTTP --> probe Node.js (sem lógica RoboCopa)
                                    PostgreSQL 17 (rede data INTERNAL; porta não publicada)
                                    Volume Docker exclusivo: postgres_data

Etapa B (após requisitos, spikes de motor e segurança):
  Estudante/Professor celular/PC
      HTTPS sob gateway autenticado, implantação externa só após aprovação
       -> PWA -> API de domínio -> PostgreSQL + fila durável
                            -> orquestrador -> battle runner -> executor de robôs isolado
                                              (rede e arquivos mínimos; limites e auditoria)
```

A sonda de infraestrutura **não usa a rede do banco**. Isso permite verificar separadamente a disponibilidade HTTP sem conceder acesso implícito aos dados. O `depends_on: condition: service_healthy` estabelece ordem inicial, mas não substitui monitoração contínua.

## Proteções implementadas na etapa A

1. Projeto Compose com nome exclusivo `robocopa-ifma-local`, redes e volume nomeados próprios.
2. Banco PostgreSQL acessível apenas na rede interna do Compose (`internal: true`); **sem `ports`**.
3. Apenas a sonda publica `127.0.0.1:18080`; nunca `0.0.0.0`.
4. Sonda em imagem Node sem root, filesystem somente leitura, `cap_drop: ALL`, `no-new-privileges` e limites de CPU/memória/PIDs.
5. PostgreSQL com limites de recursos e autenticação `scram-sha-256` para conexões externas ao contêiner; credencial criada por gerador local, não commitada.
6. Logs por contêiner com rotação; `restart: "no"` evita inicialização automática não solicitada.
7. Nenhum serviço Docker existente é apagado, parado ou recriado por este Compose. O comando `down -v` só aparece no CI **efêmero**, nunca nas instruções do host pessoal.

**Limites:** a senha ainda será visível ao mecanismo Docker/administradores com acesso ao contêiner; é credencial local de laboratório, não desenho final de secrets. O banco pode fazer escrita normal em seu volume. A sonda HTTP não autentica, logo não deve ser publicada externamente.

## Recursos e persistência

| Serviço presente | Limite de memória | CPU | Persistência |
|---|---:|---:|---|
| `database` | 2 GiB | 2 vCPU | Volume `postgres_data` |
| `infra-probe` | 512 MiB | 0,5 vCPU | Nenhuma; fonte read-only |

Worker, arena, runner, sandbox e frontend **não existem** neste Compose. Recursos futuros serão definidos com testes e limites de execução; não presumir 13 GiB alocados automaticamente.

O volume nomeado persiste após `docker compose down` (sem `-v`). O volume **não é backup**; ainda são exigidos teste de dump/restauração, política de retenção e cópia independente do mesmo computador.

## Gatilhos para hospedagem externa

Antes de acesso externo de alunos: avaliar upload, estabilidade, CGNAT/IPv6, disponibilidade elétrica, suspensão do Windows, TLS e domínio, proteção de contas de estudantes, autorização institucional, logs, backup, restauração e segregação do executor de código. Abrir portas ou configurar túnel é uma decisão posterior e separada.

## Rollback

`docker compose -f compose.local.yaml down` interrompe **apenas** os serviços deste projeto e mantém os volumes. Não usar `down -v` ou `docker system prune` no computador pessoal sem backup e autorização específica. Alterações futuras do banco exigirão migrações controladas.

## Critérios de saída do experimento

- Configuração do Compose e isolamento verificados estaticamente.
- Subida dos serviços, health checks e persistência após recriar contêiner comprovadas **em runner do CI**.
- Validação **na máquina alvo** será separada e dependerá de execução pelo responsável.
- Não declarar S04-T05, implantação ou segurança de código não confiável concluídas por um teste com PostgreSQL e sonda.
