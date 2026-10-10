# Especificações da RoboCopa IFMA

`000-governanca/` contém a primeira especificação de execução: fundação do repositório, rastreabilidade, bootstrap e limites operacionais. Não confundir essa feature com as funcionalidades futuras do produto.

Para cada feature: `spec.md` descreve problema, histórias e aceite; `plan.md` descreve decisões, interfaces e testes; `tasks.md` detalha execução. Cada tarefa técnica referencia uma tarefa macro Sxx-Tyy. Requisitos aprovados na S03 serão a fonte de verdade; projeções no Spec Kit não criam baseline concorrente.

Fluxo: constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge. Revisar a cada etapa. A CLI e o estado de feature devem ser verificados no ambiente de execução; trocar branch não substitui a seleção de feature.
