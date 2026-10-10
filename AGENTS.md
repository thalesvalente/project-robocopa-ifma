# Orientações de execução — RoboCopa IFMA

Leia primeiro `docs/planejamento/ESTADO-ATUAL.md`, `.specify/memory/constitution.md` e a tarefa selecionada em `docs/planejamento/backlog.json`. Consulte branch e arquivos reais; memória de conversa não substitui o repositório.

## Diretrizes autorizadas

ChatGPT Pro é o ambiente principal. Codex somente para implementações pesadas ou execução justificada do R4. **MVP híbrido:** frontend estático preferencialmente Vercel Hobby no contexto voluntário declarado (D-009); Supabase PostgreSQL/Auth/Storage para persistência canônica; computador do responsável somente como hospedeiro futuro de VMs Linux dedicadas para computação. Não promover o SQLite experimental nem o PostgreSQL do Compose local a banco definitivo. Cloudflare Pages é alternativa de frontend. A jornada móvel inclui programar, salvar, testar e inscrever robôs, não só acompanhar; participar não exige saber desenvolver web/mobile.

D-006/D-009 e ADR-005/006 substituem hipóteses antigas de hospedagem inteiramente local, mas não ratificam a constituição ou autorizam implantação. Somente RoboDSL básica no MVP; primeiro demonstrar com identidades sintéticas e estratégias conhecidas, antes do piloto estudantil.

## Planejamento e execução

Backlog JSON é canônico para 60 tarefas macro. `python scripts/render_planning.py` gera plano mestre e sprints. Tarefas técnicas ficam em `specs/<feature>/tasks.md` e planos de incremento ligados a elas. Issues são espelhos. Antes de executar, conferir dependências/aceites e registrar novas necessidades no Spec Kit. Preparação paralela não fecha gates. Usar comandos versionados em `.agents/commands/`; não fingir slash commands ou conexão MCP nativa do Spec Kit.

## Segurança e integridade

Não publicar dados identificáveis, segredos, IP residencial, caminhos pessoais ou banco. Não instalar serviços persistentes, abrir portas, mudar firewall/DNS/VM ou instalar runner self-hosted sem autorização específica. Código de participantes jamais roda no host pessoal ou junto às credenciais da plataforma. Experimentos de CI, autenticação do banco e contextos sintéticos não são autenticação JWT/worker operacional.

Preservar mudanças. Ler SHA antes de atualizar, sem force push. Não alterar automaticamente proteção ou visibilidade. Trabalhar em branch/revisão por PR; autorização para executar plano não é homologação de resultados futuros. Após migration002 da admissão, seguir contrato SQL atualizado: rc_admission é a entrada restrita; rc_broker não conserva enqueue bruto.

## Qualidade e encerramento

Cada conclusão exige arquivo/comando, ambiente, resultado e commit/run. Distinguir mocks, regressão local, banco/driver reais, motor real, implantação e piloto. Não registrar entrevistas, PASS, conexão, publicação ou instalação inexistentes. Sincronizar estado, plano, tarefas, contratos, dependências e evidências com o código. Manter lotes históricos e dizer o que ainda falta; não reclassificar prova própria como auditoria independente.

Não prometer execução em segundo plano. Handoff ao Codex deve especificar objetivo, branch/commit, arquivos permitidos, exclusões e testes obrigatórios. Nenhum gate amplo da feature004 ou G-PROD fecha pela aprovação de um recorte do I3.
