# Evidência — laboratório Docker local RoboCopa IFMA

**Data:** 2026-10-09 · **Branch:** `feat/infra-local-compose` · **Ambiente:** runner GitHub-hosted Ubuntu 24.04 (não é o host do responsável).

## Execução confirmada

[Workflow: Infraestrutura local (Docker Compose) — Run 38001273168](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38001273168)

**Status verificado:** `completed / success`. Job `validar-compose` e etapas de execução concluídos com sucesso.

| Evidência | Resultado |
|---|---|
| `python -m unittest discover -s tests/infra -v` | **13 testes, todos OK** |
| `docker compose -f compose.local.yaml config --quiet` | PASS |
| `python scripts/validate_local_compose.py` | PASS: projeto isolado, banco privado, única porta em loopback e limites |
| `python scripts/preflight_local.py` | PASS: CLI/Engine, arquivo .env, nome Compose, porta local e disco do workspace |
| `docker compose ... up -d --wait` | Banco e sonda marcados **Healthy** |
| `GET /health` em `127.0.0.1:18080` | Resposta HTTP 200, JSON `status: ok` validado |
| `GET /nao-existe` | HTTP 404, conforme esperado |
| Criação de tabela/inserção e recriação de contêiner `database` | PASS: `SELECT COUNT(*)` retornou `1` após recriação |
| `docker compose down -v --remove-orphans` | Executado **somente no runner descartável**, etapa de cleanup aprovada |

Nenhum token/senha gerado no CI é versionado. O ambiente GitHub-hosted não é a máquina pessoal e seu banco não contém dados reais de alunos.

## Critérios que a evidência NÃO demonstra

- Instalação/reexecução na máquina Windows 11 do responsável.
- Backup externo, restauração de desastre e retenção de dados.
- Escolha do local físico do VHDX Docker Desktop no Windows.
- Acesso externo de alunos, TLS ou segurança do gateway.
- Segurança de código arbitrário enviado por participantes, integração com o Tank Royale, métricas de carga ou hospedagem pública.
- Aprovação institucional, do projeto ou da constituição.
- Finalização das sprints S03/S04/S08.

**Rastreabilidade:** `specs/001-hosting-local/tasks.md` (INF-007); `docs/arquitetura/ADR-003-hospedagem.md`; `docs/operacao/COMPOSE-LOCAL.md`.
