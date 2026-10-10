# D-007 — Execução após revisão: demonstração segura e persistência remota

**Data:** 2026-10-10. **Origem:** aprovação explícita do responsável: executar as decisões apresentadas. **Estado:** direção aprovada; entregas só encerram com evidência.

## Decisões de escopo

Manter RoboDSL básica/PWA, Supabase PostgreSQL como fonte canônica, Auth e Storage privado, VMs Linux dedicadas no PC apenas para processamento. Priorizar demonstração privada à diretoria com identidades sintéticas e estratégias previamente verificadas. Piloto aberto com estudantes é um marco posterior, não a consequência automática da demonstração.

**Hospedagem estática — precedência revisada em D-008:** manter **Vercel como primeira opção para a PWA**, condicionada ao enquadramento Hobby do caso concreto, e **Cloudflare Pages como alternativa**. A preferência Cloudflare registrada na decisão inicial foi superada após consultar Terms §4, Fair Use e resposta de staff sobre projeto voluntário sem remuneração para organização sem fins lucrativos. Instituição pública e gratuita não é autorização automática, especialmente se o desenvolvimento integrar função remunerada. Não habilitar publicação oficial com alunos antes de confirmar elegibilidade. Supabase Edge Functions é o candidato para operações curtas do plano de controle, sem árbitro ou loop de worker permanente. Retorno de status e replay precede streaming contínuo.

Avaliar pgmq antes de codificar. A decisão técnica limitada da ADR-006 usa inicialmente uma tabela transacional PostgreSQL como único registro de jobs/leases/tentativas; não criar uma segunda fila pgmq em paralelo. Não confundir entrega em janela de visibilidade com efeito único de resultado. O ledger de placar continua em I3-04.

Preservar os experimentos SQLite e mTLS dos PRs #23/#24, sem promovê-los a banco de produção ou exigir mTLS não comprovado na borda serverless. O armazenamento PostgreSQL deve ser independente do transporte e aceitar apenas chamador de serviço confiável; nenhuma credencial administrativa vai à VM de bots. A seleção final de credenciais assimétricas curtas/PKI e a integração HTTPS outbound requerem prova própria antes de claim remoto.

## Ordem e limites

1. Reconciliar o conteúdo de #23/#24 com a main/ADR-005, preservando histórico e sem force-push.
2. Registrar ADR-006 e plano I3-03 antes do código; implementar o núcleo PostgreSQL com testes reais de transação, concorrência, expiração, cancelamento, fencing e restart em CI descartável.
3. Depois implementar e testar integração de autenticação/cloud, resultados, RLS por usuário, Storage e frontend; ensaiar VM/backup e go/no-go da demonstração.

A aprovação não é pagamento, liberação de alunos, migração em projeto real Supabase, alteração de firewall/VM/roteador, nem bypass de proteção. Não presumir relatórios de pesquisa não anexados como provas de execução. Fontes oficiais consultadas e critérios estão na ADR-006 e no plano I3-03.

## Retificação posterior da preferência de hospedagem — D-008

Esta atualização **não reabre** aprovações técnicas do I3-03. A prioridade de hosting da PWA é [Vercel, Hobby favorável em princípio pelo voluntariado declarado (D-009)](D-009-carater-voluntario-vercel-hobby.md); Cloudflare permanece contingência por portabilidade. Devem ser considerados (a) uso pessoal/não comercial dos Terms, (b) ganho financeiro de participantes na produção segundo Fair Use, (c) colaboração, quotas, retenção, (d) opção de desabilitar treinamento de IA no conteúdo de contas Hobby e ausência de PII/segredos nos builds. [ADR-006 revisada](../../arquitetura/ADR-006-demo-gratuita-plano-controle.md). Banco Supabase, serviço cloud curto e VM de execução não mudam. HYB-09, S08 e G-PROD continuam pendentes.

## Declaração de voluntariado — D-009

O responsável confirmou o desenvolvimento **voluntário e sem remuneração relacionada à RoboCopa**. Consequentemente, Vercel Hobby é opção favorecida pelos termos de uso não comercial e resposta pública da equipe da Vercel em caso equivalente. A confirmação individual escrita é opcional se surgir dúvida concreta, não gate genérico; permanecem quotas, titularidade da conta, colaboração, privacidade/Model Training e representação institucional aplicável. [D-009](D-009-carater-voluntario-vercel-hobby.md). Não modifica PostgreSQL, mTLS experimental nem G-PROD.
