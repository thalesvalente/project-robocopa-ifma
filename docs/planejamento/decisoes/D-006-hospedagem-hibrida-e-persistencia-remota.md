# D-006 — Persistência remota e VMs dedicadas no PC para o MVP

**Data:** 2026-10-10 · **Tipo:** decisão explícita do responsável, registrada antes de migrar fila/dados.
**Estado:** DIREÇÃO ESCOLHIDA, **não** implantação/homologação. Gate G-PROD continua BLOQUEADO.

## Decisão

O responsável concordou com Vercel para interface e Supabase PostgreSQL para os dados e informou que, **por enquanto, pode usar seu computador pessoal como hospedeiro de VMs Linux dedicadas para o MVP**, mas **não deseja persistir todos os dados da competição localmente**.

Desdobramento aprovado para o desenho:
- Vercel (PWA responsiva) para acesso via navegador/celular.
- Supabase Auth/PostgreSQL como persistência canônica dos usuários, submissões e versões, fila, transições, resultados e classificação.
- Supabase Storage em buckets privados para replays/artefatos grandes, com hashes e autorização.
- VMs Linux dedicadas hospedadas no PC para motor e execução isolada, recebendo trabalho apenas via canal autenticado de saída, sem abrir serviço diretamente à internet residencial.
- SQLite apenas como protótipo/testes de I3-01; não escolher SQLite para dados ou jobs definitivos do MVP.
- Discos operacionais da VM e armazenamento temporário ou spool mínimo necessário continuam locais, com cleanup após confirmação remota.

## Escopo do aceite e limites

Esta mensagem aprova **a direção arquitetural híbrida**, não instalação da VM, criação dos projetos/contas Vercel/Supabase, autorização de pagamento, migração de banco, abertura de portas, dados reais de alunos, publicação de serviço ou testes adversariais no host. Não transformar em aceite formal de S00-T06, S03-T06, S04 integral, I3-03/I4/I5 ou G-PROD. Mudanças no Windows/WSL/Docker Desktop/arquivos pessoais ainda exigem procedimento e consentimento específicos.

O experimento de PostgreSQL local (Compose) permanece histórico e útil em testes; não é promovido para fonte permanente. A implementação do I3 existente em SQLite permanece válida como laboratório, mas o plano I3-03 precisa **incluir a persistência/leases transacionais no PostgreSQL** antes de claim real. Não armazenar credenciais de banco no ambiente de bots.

## Links canônicos

[ADR-005 — arquitetura híbrida](../../arquitetura/ADR-005-hospedagem-hibrida-mvp.md) · [Spec Kit de implantação híbrida](../../../specs/001-hosting-local/hybrid-mvp.md). Manter D-005 (VM independente/ensaios CI) e demais decisões sem alteração retroativa de suas evidências.

