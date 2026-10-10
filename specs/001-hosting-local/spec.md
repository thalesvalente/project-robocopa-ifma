# Feature 001 — Laboratório de hospedagem local

**Estado:** preparação técnica / validação no CI em andamento; não ratificada.  
**Rastreabilidade:** S00-T05 (inventário), S04-T01 (stack candidata), S04-T05 (topologia candidata), S08 (implantação futura). A execução técnica preparatória não elimina os gates formais das sprints.

## US1 — Iniciar infraestrutura sem afetar outros projetos

Como responsável pelo computador hospedeiro, quero iniciar um ambiente de teste com identidade exclusiva, uma porta local previsível e limites de recursos, para comprovar a capacidade sem interromper meus contêineres existentes.

**Critérios de aceite:**
- `docker compose -f compose.local.yaml config --quiet` é válido.
- Há somente a sonda publicada em `127.0.0.1:18080` (porta configurável) e nenhum banco publicado no host.
- Nome Compose específico; não depende de alterar firewall, roteador, rede doméstica ou serviços de outros projetos.
- A sonda possui limites de CPU, RAM, processos, usuário sem root, disco readonly e capabilities removidas.
- O script gerador cria `.env` secreto local e se recusa a substituir arquivo existente.

## US2 — Persistir dados de infraestrutura sem expor banco

Como mantenedor, quero armazenar dados no PostgreSQL com volume persistente e acesso interno, para reiniciar serviços sem perder dados de teste nem expor o banco à rede.

**Critérios de aceite:**
- PostgreSQL em rede Docker marcada `internal: true`, sem mapeamento de porta.
- Volume nomeado montado no diretório persistente correto da versão do PostgreSQL.
- Saúde do banco verificada por `pg_isready`.
- CI comprova criação de uma tabela de teste, recriação do contêiner de banco e leitura posterior.
- Limites e logs rotativos definidos; backup/restauração independentes permanecem pendentes.

## US3 — Operar com evidência e rollback

Como responsável, quero procedimentos claros de iniciar, testar e parar apenas os serviços da RoboCopa, para evitar danos a outras aplicações.

**Critérios de aceite:**
- Manual Windows PowerShell com comandos de validação, subida, inspeção e parada sem remoção dos volumes.
- Testes automatizados do contrato de isolamento e de segurança do gerador de senha.
- Workflow em GitHub-hosted runner; sua aprovação não significa execução no Windows hospedeiro.
- Inventário compartilhado permanece fora do Git; documentação pública é sanitizada.

## Fora de escopo nesta feature

Interface do participante, autenticação, programação e execução de bots, integração com Tank Royale, acesso público remoto, túnel, TLS externo, migração do disco Docker, migração do banco e backups completos.

## Restrições

Não executar código de participantes nesta configuração. Não executar `down -v` ou `docker system prune` no computador pessoal por instrução automatizada. Não declarar a infraestrutura pronta para alunos com base na resposta de uma sonda HTTP.

## Adendo ao escopo da Feature 001 — direção do MVP híbrido (2026-10-10)

As histórias US1..US3 acima descrevem o **experimento local já executado**, não o alvo definitivo de banco/worker. A decisão [D-006](../../docs/planejamento/decisoes/D-006-hospedagem-hibrida-e-persistencia-remota.md) aprovou **a direção**, sem implantar: PostgreSQL cloud no Supabase para todo estado canônico; Storage cloud para arquivos; Vercel para a PWA; VMs Linux dedicadas no PC somente para computação e staging temporário. As histórias, aceites e tarefas adicionais do MVP estão em [hybrid-mvp.md](hybrid-mvp.md), ainda não concluídas. O Compose PostgreSQL local não será promovido automaticamente para banco de produção nem apagado. A ratificação institucional e os gates de segurança continuam exigidos.
