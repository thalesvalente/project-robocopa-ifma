# Evidência — primeira execução na máquina hospedeira

**Data:** 2026-10-09 · **Ambiente:** Windows 11 Pro, Docker Desktop com contêineres Linux (WSL 2).  
**Origem:** saídas de PowerShell fornecidas pelo responsável no chat. **Não** é execução direta pelo assistente na máquina.

## Execução confirmada

O responsável atualizou a branch `feat/infra-local-compose`, gerou a credencial local, validou o Compose e a política de isolamento e executou o preflight. Na segunda tentativa, com o daemon disponível, as seis verificações do preflight retornaram PASS.

O comando `docker compose -f compose.local.yaml up -d --wait` concluiu. Evidências observadas:

| Componente/etapa | Resultado observado |
|---|---|
| Rede `robocopa-ifma-local_data` | Created |
| Rede `robocopa-ifma-local_edge` | Created |
| Volume `robocopa-ifma-local_postgres_data` | Created |
| `robocopa-ifma-local-database-1` | Up (healthy) — `postgres:17-alpine` |
| `robocopa-ifma-local-infra-probe-1` | Up (healthy) — `node:24-alpine` |
| Porta publicada da sonda | `127.0.0.1:18080->8080/tcp` |
| `Invoke-RestMethod http://127.0.0.1:18080/health` | `service=robocopa-ifma-infra-probe`, `status=ok`, `scope=local-development-only` |
| PostgreSQL no host | Sem porta publicada, conforme `docker compose ps` |
| Alteração da pasta do repositório | Responsável passou a executar o projeto em outra unidade de armazenamento; caminho individual omitido |

A senha local não foi exibida nem publicada. Nenhum serviço de outro projeto foi alterado pelos comandos de inicialização da RoboCopa apresentados.

## Limitações e pendências

1. O volume foi criado e o banco está saudável; **não** foi verificada, no Windows, a persistência de dados após reinício, dump/restore ou backup externo. Persistência após recriação **no CI** tem evidência separada em `INFRA-LOCAL-CI.md`.
2. A pasta Git estar em outra unidade **não** comprova que o disco virtual Docker Desktop, seus volumes ou imagens estejam nessa unidade. Local do VHDX permanece desconhecido.
3. `/health` comprova somente o laboratório HTTP; não há API RoboCopa, motor de batalhas, executor seguro de robôs nem portal de alunos.
4. O acesso ao exterior não foi configurado nem autorizado. Segurança de código de participantes, backup, rede externa e capacidade sob carga seguem pendentes.
5. A constituição do projeto, ADRs e gates de S03/S04 ainda exigem ratificação.

**Rastreabilidade:** `specs/001-hosting-local/tasks.md` — INF-008; `docs/planejamento/backlog.json` — inventário S00-T05 já concluído; `docs/operacao/COMPOSE-LOCAL.md`.

**Conclusão restrita:** laboratório Docker Compose inicial funcionando na máquina hospedeira; não equivale a MVP implantado ou pronto para estudantes.
