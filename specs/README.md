# Especificações da RoboCopa IFMA

| Feature | Escopo | Estado |
|---|---|---|
| [000-governanca](000-governanca/spec.md) | Fundação, rastreabilidade e bootstrap | Base técnica entregue; ratificação pendente |
| [001-hosting-local](001-hosting-local/spec.md) | PostgreSQL e sonda local | CI e primeira execução no host confirmados; não é MVP |
| [002-tank-royale](002-tank-royale/spec.md) | Batalha real de referência | CI aprovado; reprodução no Windows informada pelo responsável |
| [003-autoria-mobile](003-autoria-mobile/spec.md) | RoboDSL e editor com treino real | CI e observações no PC; celular físico e ratificação pendentes |
| [004-isolamento-execucao](004-isolamento-execucao/spec.md) | Ameaças, arquitetura candidata, gates e plano de implementação | **Documentação em revisão; nenhum teste adversarial ou aprovação de sandbox** |

`000-governanca/` contém a primeira especificação de execução: fundação do repositório, rastreabilidade, bootstrap e limites operacionais. Não confundir essas features preparatórias com as funcionalidades finais do produto.

Para cada feature: `spec.md` descreve problema, histórias e aceite; `plan.md` descreve decisões, interfaces e testes; `tasks.md` detalha execução. Cada tarefa técnica referencia uma tarefa macro Sxx-Tyy. Requisitos aprovados na S03 serão a fonte de verdade; projeções no Spec Kit não criam baseline concorrente.

Fluxo: constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge. Revisar a cada etapa. A CLI e o estado de feature devem ser verificados no ambiente de execução; trocar branch não substitui a seleção de feature.
