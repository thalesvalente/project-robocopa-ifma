# Execução de rodadas

## Fonte de verdade

`docs/planejamento/backlog.json` contém as 60 tarefas macro. O plano mestre e dez páginas de sprint são gerados por `python scripts/render_planning.py`; não editar essas projeções isoladamente. `specs/<feature>/spec.md`, `plan.md` e `tasks.md` detalham funcionalidades. Issues acompanham as tarefas e apontam para os artefatos canônicos.

## Estados e gates

`A_FAZER → EM_EXECUCAO → EM_REVISAO → CONCLUIDA`. Bloqueios exigem motivo e condição de desbloqueio. Conclusão exige evidência. Predecessoras pendentes permitem apenas preparação documental explicitamente identificada como minuta paralela; não permitem afirmar sprint concluída ou iniciar execução insegura.

## Rodada

Ler branch/commit, estado, constituição e tarefa. Conferir entradas e dependências. Produzir a entrega autorizada. Revisar diff, testar e registrar o resultado real. Atualizar backlog e suas projeções; reconciliar issues. Fechar a rodada com entregas e bloqueios, sem prometer trabalho posterior em segundo plano.

## ChatGPT, Codex e R4

ChatGPT Pro conduz planejamento, documentação, revisão e alterações delimitadas. Escalar ao Codex quando houver mudanças extensas correlacionadas, depuração repetida, executor isolado, integração do motor ou grandes suítes. Handoff contém tarefa, objetivo, branch/commit, entradas, arquivos permitidos, exclusões, testes e formato da evidência.

R4 é opcional. Antes de usá-lo, verificar versão e artefatos reais. Preservar entradas/saídas, reconciliar IDs e RF/RNF/RN/RES, revisar duplicações e critérios de aceite. Não manter um segundo catálogo autoritativo.

## Evidência

Registrar data, ambiente, versão/commit, tarefa, comando ou roteiro, esperado, observado, resultado e limitações. `Objetivo → requisito → história → tarefa → teste → evidência → commit`. Teste de planejamento não é teste do produto. Mock não é motor. CLI no CI não é instalação no computador do responsável. Artefato gerado não é aprovação humana.

## Autorizações separadas

O pedido de executar autoriza as alterações de projeto e tarefas no repositório indicado. Não autoriza implicitamente exposição pública da máquina, firewall/DNS, instalação persistente, runner self-hosted, publicação de dados pessoais ou coleta de dados de alunos. Essas operações exigem contexto e autorização próprios.
