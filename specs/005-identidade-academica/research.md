# Pesquisa — Google OAuth misto: acadêmico Workspace e Gmail pessoal

**Data:** 2026-10-10. **Decisão:** D-011 amplia a D-010 para múltiplas escolas. Nenhum Google OAuth real conectado/validado por esta pesquisa.

| Tema | Fonte primária | Consequência para o MVP |
|---|---|---|
| Google OIDC | https://developers.google.com/identity/openid-connect/reference | `sub` é ID estável; e-mail não é chave; `hd` só aparece para usuários de domínio hospedado e deve ser conferido **se** o sistema afirma vínculo Workspace. Não exigir `hd` em Gmail pessoal |
| Google Auth/Supabase | https://supabase.com/docs/guides/auth/social-login/auth-google | Um provedor Google atende pessoal e Workspace; frontend único sem `hd` obrigatório; credenciais Google ficam no provedor/backend |
| Supabase Auth Hook | https://supabase.com/docs/guides/auth/auth-hooks/before-user-created-hook | Hook permite restringir provedor e dados no cadastro, mas não deve bloquear Gmail pessoal nem conceder escola/role; contas antigas exigem autorização contínua |
| RLS PostgreSQL | https://supabase.com/docs/guides/database/postgres/row-level-security | Vínculo autorizado por school_id e owner, não por e-mail ou domínio; isolamento tenant cruzado |
| Workspace for Education para menores | https://knowledge.workspace.google.com/admin/getting-started/editions/manage-access-to-unconfigured-third-party-apps-for-users-designated-as-under-18 | Contas escolares de menores podem estar sujeitas a app terceiro bloqueado; há exceções conforme configuração de scopes básicos, por isso testar a conta real com admin |
| Google de outra escola | https://knowledge.workspace.google.com/admin/apps/control-which-apps-access-google-workspace-data | Cada escola pode ter domínios/controles próprios. Não equiparar Google login a matrícula |
| IFMA academia/SUAP | Histórico [D-010](../../docs/planejamento/decisoes/D-010-login-google-academico-ifma.md) | `acad.ifma.edu.br` é domínio de e-mail acadêmico **candidato**, não evidência definitiva de `hd` |

**Conclusão de engenharia:** preservar a implementação Google OAuth do Supabase, retirar exclusividade Workspace e tratar a autorização por **vínculo escolar verificável** como independente. O risco principal ao abrir contas Gmail é autoinscrição indevida: manter PENDING sem acesso, convite administrativo e RLS. Não é necessário adicionar provedor de identidade ou serviço pago.
