# I3-03B / revisão do harness antes da correção

**Data:** 2026-10-10. **Estado:** correção planejada, ainda sem aceitar a integração.

O run 38079559910 do workflow novo `.github/workflows/i3-admission.yml` foi rejeitado antes de executar o job (evento push/failure); as consultas que filtram somente pull_request não o mostravam. O arquivo usa `runner.temp` no nível `jobs.<job_id>.env`, onde o contexto runner não está disponível segundo a [referência oficial do GitHub](https://docs.github.com/actions/reference/workflows-and-actions/contexts).

**Correção delimitada antes do patch:** calcular os diretórios de socket/HBA a partir de RUNNER_TEMP dentro do primeiro step e exportá-los para GITHUB_ENV; no cleanup calcular o mesmo caminho de forma determinística para falhas anteriores ao primeiro step. Manter nomes únicos por run/attempt, Unix socket, SCRAM, network none, ausência de porta publicada, isolamento e verificação de cleanup. Não é motivo para relaxar guardas ou executar no host pessoal.

A suite unitária teve também uma continuação de `with` sem parênteses, corrigida sintaticamente em 50c358d dentro da tarefa AD-04 já planejada; não contar o arquivo anterior como teste aprovado. O novo workflow fará compileall antes de subir o banco.

Aceite: workflow válido, execução real dos testes por Psycopg/SCRAM, fonte/run vinculados e cleanup aprovado. Sem esses resultados, AD-05/06 permanecem abertos. A primeira falha não comprova erro no banco nem na regra de admissão; ocorreu na configuração do workflow.
