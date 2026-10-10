# D-011 — Google acadêmico OU Gmail pessoal; escolas por vínculo autorizado

**Data:** 2026-10-10 · **Estado:** decisão expressa do responsável, APROVADA para a direção do MVP; implementação e liberação de usuários ainda pendentes. **Precedência:** amplia/supera a restrição de login exclusivo acadêmico da [D-010](D-010-login-google-academico-ifma.md), preservando a preferência por conta acadêmica quando disponível.

## Motivação e decisão

A RoboCopa não deve se restringir ao IFMA: é prevista expansão a outras escolas, inclusive estudantes sem Google Workspace institucional. O responsável decidiu explicitamente **permitir também contas Gmail pessoais**. Por isso, o login será **"Continuar com Google"**, via Supabase Auth/Google OAuth, aceitando:
- Google Workspace acadêmico de instituição cadastrada, comprovado por identidade Google e `hd` assinado quando usado para afirmar domínio institucional (o `hd` informado no pedido de login é só dica);
- conta Google pessoal com e-mail verificado `@gmail.com`, **sem exigir o claim `hd`**, que não existe normalmente para Gmail pessoal.

Um e-mail de outro domínio associado a uma conta Google mas sem `hd` verificável não é, por essa razão, prova de instituição; tratar como **sem classificação/pendente** até decisão posterior, não como aluno automaticamente autorizado. Não acrescentar outros provedores OAuth ou senha própria no MVP.

**Autenticação não é autorização.** Google somente demonstra identidade. Mesmo depois de criar uma sessão, o usuário fica em `PENDING` e não recebe permissão de treino, inscrição, leitura de estratégias privadas, resultados privados ou criação de escola até que um vínculo com escola/turma/competição seja **registrado e aprovado pelo serviço confiável**. E-mail acadêmico, Gmail pessoal, domínio, `hd`, nome da escola digitado no formulário e convites inválidos **não dão papel ou matrícula automaticamente**.

## Política multiescola inicial

- A entidade Escola/Organização é tenant e tem ID opaco estável; IFMA é uma escola/organização inicial; outras escolas são cadastradas **somente por administrador autorizado**, sem depender de domínio de e-mail.
- Um usuário pode ter vínculo com mais de uma escola, com papéis independentes, estados `PENDING/ACTIVE/SUSPENDED` e escopos por turma/competição; o `auth.users.id` é a identidade interna estável, e Google `sub` é identidade do provedor, nunca e-mail.
- Vínculo pode decorrer de convite administrativo de um professor/organizador autorizado, a validar no servidor com expiração, uso único e rate limits, ou aprovação manual. O estudante não pode criar a própria vinculação, escolher papel `admin` nem alterar `school_id` via metadata.
- Contas pessoais aprovadas podem competir **pela escola autorizada**, não apenas numa categoria separada. Permissões exigem a mesma política para contas institucionais e pessoais.
- A participação externa é **escopo de identidade/arquitetura do MVP**, não declaração de lançamento multiescolas/competição pública. O marco de demonstração permanece restrito a dados sintéticos; piloto com estudantes reais e expansão institucional exigem gates específicos.

## Segurança, privacidade e menores

O backend deve validar sessão Supabase e identidade Google com fonte confiável; `email_verified`, `sub`, provedor Google, `iss/aud/exp` e `hd` **quando se afirmar domínio Workspace**. Não confiar em `user_metadata` alterável ou JSON do navegador como prova de autorização. O `hd` ausente para Gmail é esperado e **não** equivale a falha de autenticação pessoal. Retirar eventual bloqueio global de `@gmail.com` no **Before User Created Hook**; hook continua podendo negar provedores diferentes de Google, mas autorização ativa é sempre aplicada por API/RLS, inclusive em contas antigas.

Contas Google Workspace for Education de menores podem ter acesso a apps terceiros controlado pelo administrador; contas Gmail pessoais não devem ser tratadas como solução para burlar regras escolares, proteção de menores, políticas institucionais e LGPD. Idade/consentimento não podem ser inferidos do tipo de e-mail; cadastrar menores depende de revisão/consentimento aplicável. Não importar diretórios acadêmicos nem PII do SUAP sem autorização.

## Trade-offs explícitos

| Benefício | Custo/risco | Mitigação |
|---|---|---|
| Acesso a estudantes sem e-mail escolar | Não há validação automática de matrícula | Vínculo/convite aprovado pelo organizador |
| Uma só integração Google OAuth | O Workspace pode enviar `hd` e Gmail não | Branch de identidade por claim autenticado, não hint |
| Expansão a diferentes escolas | Risco de acesso cruzado entre escolas | Tenant explícito + RLS por vínculo ativo |
| Menos dependência da DTI de cada escola | Conta pessoal pode ser de menor de idade | Política de consentimento, moderação e privacidade antes do piloto |
| Gratuidade no Supabase Auth | Risco de abuso/spam/quotas | PENDING por padrão, rate limit, auditoria e bloqueio |

## Fontes oficiais consultadas

- [Google OIDC claim `hd`, `sub`, `email_verified`](https://developers.google.com/identity/openid-connect/reference)
- [Supabase Google OAuth](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Supabase Before User Created Hook](https://supabase.com/docs/guides/auth/auth-hooks/before-user-created-hook)
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Google Workspace for Education e apps terceiros sob 18](https://knowledge.workspace.google.com/admin/getting-started/editions/manage-access-to-unconfigured-third-party-apps-for-users-designated-as-under-18)

**Não feito:** criação de projeto Google/Supabase, autenticação OAuth real, importação de contas de escolas, cadastro/validação de estudantes, deploy, quotas reais ou homologação. G-PROD permanece bloqueado.
