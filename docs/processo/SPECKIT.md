# Spec Kit no projeto

A dependência oficial está fixada em `tools/speckit.lock.json`: release v1.1.2, commit completo 959e866caa3618bf3dc290d5dca33394365af9c6. A integração escolhida é `generic`, com comandos em `.agents/commands/` e scripts Python para reduzir diferenças entre sistemas operacionais.

## Inicialização preservando documentos

```sh
python scripts/bootstrap_speckit.py
python scripts/bootstrap_speckit.py --apply --script py
```

A primeira chamada é simulação. A segunda requer Python 3.11+, uv/uvx, Git e rede; obtém o upstream oficial, inicializa um projeto temporário, verifica arquivos esperados e só então copia arquivos novos. Preserva `.specify/memory/constitution.md`, rejeita conflitos e links simbólicos e não faz commit, push, abertura de porta nem conexão MCP.

O workflow `fundacao.yml` permite executar esse bootstrap em runner GitHub-hosted e registrar arquivos/SHAs na branch `chore/s00-fundacao-speckit`. A execução só se considera confirmada quando o run e o commit gerado forem verificados. O arquivo `docs/qualidade/evidencias/SPECKIT-CI.json`, quando existir após sucesso, registra o ambiente correto; não comprova instalação no host do MVP.

## Uso pelo ChatGPT Pro

Ler o comando gerado e os artefatos atuais, executar as instruções aplicáveis com as ferramentas realmente disponíveis e registrar o resultado. Fluxo completo: constitution, specify, clarify, plan, checklist, tasks, analyze, implement e converge. Cada etapa é revisada antes da próxima. Não enviar todos os comandos cegamente nem executar código de alunos durante planejamento.

Os comandos são instruções para agentes; não são comandos de terminal e não ganham automaticamente uma invocação nativa nesta conversa. A busca de plugin nesta rodada não retornou conector específico para Spec Kit. O uso pelo repositório continua possível sem alegar conexão MCP.

A feature ativa é controlada por `.specify/feature.json` ou pela variável documentada pelo toolkit; mudar a branch não deve ser tratado como seleção automática da feature. A configuração será gerada/conferida pelo toolkit antes do uso técnico.

## Fontes

- https://github.com/github/spec-kit/releases/tag/v1.1.2
- https://github.github.com/spec-kit/quickstart.html
- https://github.github.com/spec-kit/reference/integrations.html

Consultadas em 2026-10-09. A documentação online pode evoluir; a execução deste projeto usa o commit fixado.
