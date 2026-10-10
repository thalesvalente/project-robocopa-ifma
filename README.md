# RoboCopa IFMA

Plataforma educacional em desenvolvimento para aprender programação por meio de uma competição de robôs virtuais. O ponto de partida é o IFMA Campus Itapecuru-Mirim; participação de outras escolas é uma evolução a validar.

**Direção do MVP:** o estudante acessa pelo computador ou celular, aprende o básico, programa uma estratégia, salva uma versão, testa seu robô, inscreve-o na competição e consulta os resultados. A execução dos robôs ocorrerá no servidor hospedado na máquina do responsável, não no aparelho do aluno.

> Esta base contém planejamento e ferramentas de execução. Não é uma aplicação pronta e não comprova implantação na máquina alvo.

## Navegação

| Área | Entrada |
|---|---|
| Estado e bloqueios | [Estado atual](docs/planejamento/ESTADO-ATUAL.md) |
| 10 sprints e 60 tarefas | [Plano mestre](docs/planejamento/PLANO-MESTRE.md) · [Backlog canônico](docs/planejamento/backlog.json) |
| Regras de trabalho | [AGENTS.md](AGENTS.md) · [Processo](docs/processo/EXECUCAO.md) |
| Princípios | [Constituição proposta](.specify/memory/constitution.md) |
| Spec Kit | [Integração e limites](docs/processo/SPECKIT.md) · [Lock](tools/speckit.lock.json) |
| Hospedagem própria | [Inventário sanitizado](docs/operacao/inventario-sanitizado.md) · [Laboratório Docker local](docs/operacao/COMPOSE-LOCAL.md) · [ADRs candidatos](docs/arquitetura/visao.md) |
| Especificações | [Índice](specs/README.md) · [Hospedagem local (feature 001)](specs/001-hosting-local/spec.md) |
| Descoberta, BMC e projeto | [Índice de minutas](docs/descoberta/README.md) |

## Verificação do planejamento

Requer Python 3.11 ou superior. Não exige credenciais nem instala a aplicação.

```sh
python scripts/render_planning.py
python scripts/verify_planning.py
python -m unittest discover -s tests/planning -v
```

## Spec Kit

```sh
python scripts/bootstrap_speckit.py
python scripts/bootstrap_speckit.py --apply --script py
```

A primeira chamada simula; a segunda requer uv/uvx, Git e rede, inicializa o upstream fixado em staging e preserva os documentos. Evidência de CI, quando produzida, não significa que a CLI esteja instalada na máquina do responsável nem que exista conexão MCP nesta conversa.

ChatGPT Pro conduz o projeto. Codex fica reservado ao trabalho pesado; R4 somente quando justificado. Não publicar dados pessoais de alunos, credenciais, IP residencial ou backups. Não abrir o host à internet sem uma etapa específica de segurança e autorização.
