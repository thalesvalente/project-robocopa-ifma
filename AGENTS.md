# Orientações de execução — RoboCopa IFMA

Leia primeiro `docs/planejamento/ESTADO-ATUAL.md`, `.specify/memory/constitution.md` e a tarefa selecionada em `docs/planejamento/backlog.json`. Consulte a branch e os arquivos reais; memória de conversa não substitui o estado do repositório.

## Diretrizes autorizadas

ChatGPT Pro é o ambiente principal. Codex somente para implementações pesadas ou execução justificada do R4. O MVP será hospedado na máquina do responsável. A jornada móvel inclui programar, salvar, testar e inscrever robôs, não apenas acompanhar resultados. Participar não exige saber construir aplicações web ou mobile.

## Planejamento e execução

O backlog JSON é canônico para as 60 tarefas macro. `python scripts/render_planning.py` gera o plano mestre e as visões das sprints. As tarefas técnicas vivem em `specs/<feature>/tasks.md`, com referência à tarefa macro. Issues são espelhos, não requisitos concorrentes. Antes de executar, conferir dependências e critérios de aceite. Minutas antecipadas devem ser identificadas como preparação paralela, sem encerrar gates.

Usar os comandos versionados em `.agents/commands/` quando disponíveis. Antes do bootstrap, eles não existem e não se deve fingir invocá-los. Instalação de arquivos do Spec Kit não cria, por si, uma conexão MCP com esta conversa.

## Segurança e integridade

Não publicar dados identificáveis de participantes, segredos, IP residencial, caminhos pessoais ou cópias do banco. Não instalar serviços persistentes, abrir portas, mudar firewall/DNS nem instalar runner self-hosted sem autorização específica. Nunca executar código arbitrário de participantes no host pessoal ou junto às credenciais da plataforma.

Preservar mudanças existentes. Ler SHA atual antes de atualizar; não fazer force push. Não alterar automaticamente regras de proteção nem a visibilidade do repositório. Trabalhar em branch; revisão por pull request. Não interpretar autorização para executar o plano como homologação dos resultados ainda inexistentes.

## Qualidade

Cada conclusão exige evidência: arquivo, comando/roteiro, ambiente, resultado e commit/run. Distinguir teste local de planejamento, teste com mocks, integração com motor real, piloto e implantação na máquina alvo. Não registrar entrevistas, PASS, conexão, publicação ou instalação que não ocorreram.

## Encerramento da rodada

Atualizar estado e tarefas conforme confirmações reais. Informar entregas, verificações, bloqueios e próxima tarefa elegível. Não prometer execução em segundo plano. Handoff ao Codex deve especificar objetivo, branch/commit, arquivos permitidos, exclusões e testes obrigatórios.
