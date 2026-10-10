# Plano técnico da feature 005 — login acadêmico Google

**Data:** 2026-10-10; **estado:** PLANEJADO ANTES DE CÓDIGO. **Decisão:** D-010/ADR-007. **Dependências:** S03; esquema/RLS HYB-01/02, autenticação cloud I3-03, HYB-09 (Vercel), S08 (LGPD/termos), autorização Workspace e identidade real ainda sem prova. Feature 005 não é o serviço do worker, nem substitui a admissão RoboDSL.

## Arquitetura

1. PWA React/TypeScript Vercel, botão do Google acionando `supabase.auth.signInWithOAuth({provider:'google', options:{queryParams:{hd:DOMAIN}}})`; o `hd` de solicitação é apenas dica visual e deve vir de configuração **confirmada**, não do JSON do aluno.
2. Google OIDC valida credenciais e identidade; Supabase Auth gerencia a sessão. Não solicitar escopos além de `openid,email,profile`, nem refresh token Google offline.
3. Borda backend/API valida sessão Supabase pelo SDK e consulta inscrição/vínculo autorizado. Verificar identidade de provedor Google e **claim `hd` assinado ou prova autenticada equivalente**. **Não promover usuário** se `hd` não for comprovado. A aplicação não deve confiar no cliente para decidir papéis.
4. Postgres privado: `profiles`, `campus`, `enrollments`/participações e papéis sob RLS; registrar apenas os identificadores minimamente necessários, tenant correto e situação ACTIVE/PENDING/SUSPENDED. `auth.users.id` e `identity.provider_id` estáveis; email não é PK.
5. Before User Created Hook configurado para recusar cadastro por provider/domínio inelegível; política API/RLS independente cobre usuários já existentes, revogação e mudança de login.
6. Gerenciamento de domínio/administrador Workspace: se conta Google Sala de Aula via SUAP não usar OAuth padrão, **retornar à clarificação/arquitetura antes de implementar fallback**.

## Testes antes de liberar estudantes

CI não precisa de contas escolares: testes de regras pura/hook/RLS com identidades e tokens sintéticos **rotulados mock**; casos positivos e negativos de dono, domínio, provider, `hd`, provider fake, identidade velha, revogação e acesso entre campus. **Integração OIDC real** só com conta de teste institucional e administrador aprovando a aplicação; nunca com dados de aluno real em GitHub, nunca fingir handshake Google.

Testar callback URL exata, `state`/PKCE/nonce conforme SDK, `email_verified`, clock/audience/issuer, provider sub, logout e revalidação de sessão. Documentar se `hd` aparece ou não em claims do fluxo Supabase real; se não, seguir decisão fail-closed e revisar implementação. Evitar configurar client secret no bundle da Vercel.

## Riscos e escolhas

- A conta `@acad.ifma.edu.br` pode **não corresponder** ao Google Workspace Google Sala de Aula configurado no SUAP. Sem prova, `hd` não é fixado.
- Google Workspace for Education **bloqueia apps terceiros não aprovados de menores de 18 anos**. Necessita suporte do admin; não contornar com Gmail pessoal.
- Domínio IFMA inclui campus/turnos além de Itapecuru e contas sem matrícula ativa. Participar exige vínculo explícito; domínio não é autorização.
- Preço: Supabase Auth Google social é candidato ao Free, mas confirmar quotas (MAUs e limites). SAML enterprise é desnecessário para MVP.
- Política de dados educacionais e consentimento institucional continuam por revisar antes de alunos reais.

## Ordem de engenharia

1. Registrar D-010/ADR-007/spec/plan/tasks **antes do código**; sincronizar índice, ADR-005 e estado, sem marcar S03 concluída.
2. Testar com DTI/admin uma conta Google acadêmica de teste e documentar **somente o domínio/claims sanitizados** e se app terceiro é liberado; resolver Q-ID01–03.
3. Planejar migrações `profiles/enrollments/roles` e hooks RLS em PostgreSQL CI; implementar testes negativos.
4. Configurar OAuth em ambiente de teste sob conta Google Cloud autorizada e Supabase de teste; segredos só em secret stores, nunca Git/CI artifacts.
5. Implementar login PWA/Supabase Auth e autorização backend, negar todos os caminhos não aprovados. Integrar com vínculo de versão/owner do I3-03 após autenticação.
6. Bateria de segurança, testes com telefone físico e logout; documentar custos, identidade/retorno e gates. Só então considerar acesso real de estudantes após S03/S08/I3/I4/I5.

**Nenhuma credencial ou instituição foi conectada nesta etapa.**

