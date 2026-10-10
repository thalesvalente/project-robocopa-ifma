# D-007 — Execução após revisão: demonstração segura e persistência remota

**Data:** 2026-10-10. **Origem:** aprovação explícita do responsável: executar as decisões apresentadas. **Estado:** direção aprovada; entregas só encerram com evidência.

## Decisões de escopo

Manter RoboDSL básica/PWA, Supabase PostgreSQL como fonte canônica, Auth e Storage privado, VMs Linux dedicadas no PC apenas para processamento. Priorizar demonstração privada à diretoria com identidades sintéticas e estratégias previamente verificadas. Piloto aberto com estudantes é um marco posterior, não a consequência automática da demonstração.

Ajustar a prioridade de hospedagem estática para Cloudflare Pages Free, mantendo Vercel como alternativa condicionada ao enquadramento contratual. Não presumir que Vercel Hobby pessoal/não comercial homologa uso institucional. Supabase Edge Functions é o candidato para operações curtas do plano de controle, sem árbitro ou loop de worker permanente. Retorno de status e replay precede streaming contínuo.

Avaliar pgmq antes de codificar. A decisão técnica limitada da ADR-006 usa inicialmente uma tabela transacional PostgreSQL como único registro de jobs/leases/tentativas; não criar uma segunda fila pgmq em paralelo. Não confundir entrega em janela de visibilidade com efeito único de resultado. O ledger de placar continua em I3-04.

Preservar os experimentos SQLite e mTLS dos PRs #23/#24, sem promovê-los a banco de produção ou exigir mTLS não comprovado na borda serverless. O armazenamento PostgreSQL deve ser independente do transporte e aceitar apenas chamador de serviço confiável; nenhuma credencial administrativa vai à VM de bots. A seleção final de credenciais assimétricas curtas/PKI e a integração HTTPS outbound requerem prova própria antes de claim remoto.

## Ordem e limites

1. Reconciliar o conteúdo de #23/#24 com a main/ADR-005, preservando histórico e sem force-push.
2. Registrar ADR-006 e plano I3-03 antes do código; implementar o núcleo PostgreSQL com testes reais de transação, concorrência, expiração, cancelamento, fencing e restart em CI descartável.
3. Depois implementar e testar integração de autenticação/cloud, resultados, RLS por usuário, Storage e frontend; ensaiar VM/backup e go/no-go da demonstração.

A aprovação não é pagamento, liberação de alunos, migração em projeto real Supabase, alteração de firewall/VM/roteador, nem bypass de proteção. Não presumir relatórios de pesquisa não anexados como provas de execução. Fontes oficiais consultadas e critérios estão na ADR-006 e no plano I3-03.
