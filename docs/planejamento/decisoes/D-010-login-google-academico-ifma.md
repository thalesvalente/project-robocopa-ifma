# D-010 — Entrada de estudantes com conta Google acadêmica do IFMA (histórico)

**SUPERADA PARCIALMENTE POR [D-011](D-011-google-pessoal-multiescolas.md) EM 2026-10-10:** a regra antiga de conta acadêmica **exclusiva**, proibição de Gmail pessoal, rejeição de `hd` ausente para todo login e adiamento de escolas externas **não vigora mais**. Login Google passa a aceitar **Workspace acadêmico OU Gmail pessoal**, com vínculo escolar aprovado. Este arquivo é preservado como histórico da decisão anterior; para o escopo atual seguir D-011, [ADR-008](../../arquitetura/ADR-008-google-multiescolas.md) e [Spec Kit 005](../../../specs/005-identidade-academica/spec.md).

**Data:** 2026-10-10. **Origem:** decisão explícita do responsável: "Quero que [os estudantes] usem a acadêmica do Google". **Estado:** REQUISITO APROVADO, ainda **não implementado nem integrado a uma conta do Google/Supabase**. **Rastreabilidade:** S03 identidade/perfis, S04 autorização do plano de controle, HYB-01/02/09, I3-03 e [feature 005](../../../specs/005-identidade-academica/spec.md). G-PROD BLOQUEADO.

## Decisão

O **único login de estudante a disponibilizar no MVP** será "Entrar com Google acadêmico do IFMA", com OAuth 2.0/OIDC administrado pelo **Supabase Auth**, cujo provedor social é Google. O estudante não cria senha própria da RoboCopa e NÃO fornece sua senha Google ao sistema. Não usar Gmail pessoal como conta de participante. A PWA React/TypeScript (Vercel preferencial) apenas inicia o fluxo; o servidor, Supabase Auth e RLS determinam identidade e autorização.

**Domínio candidato a confirmar:** `@acad.ifma.edu.br` é informado por material educacional referente ao e-mail acadêmico do IFMA, mas **não há prova ainda de que esta seja a mesma identidade utilizada pelo Google Workspace/Google Sala de Aula**. Registros do SUAP distinguem campos "E-mail Acadêmico" e "E-mail Google Sala de Aula", este último podendo exigir acesso via SUAP. **Não hardcodar o domínio no cadastro liberado antes de um teste com conta de prova autorizada e confirmação da DTI/administrador Workspace**.

## Regras de autorização

- Login bem-sucedido pelo Google **não basta** para participar. É necessária identidade de domínio Workspace aprovada e vínculo ativo/autorizado em uma turma/competição do campus, estabelecido pelo serviço institucional/administrador, com controle de suspensão e revogação. Pertença ao domínio não comprova matrícula vigente ou campus.
- Identidade persistente: `auth.users.id` do Supabase vinculada ao identificador estável do provedor Google `sub` / `provider_id`; nunca usar e-mail mutável ou `owner_ref` de cliente como chave de autoridade.
- Conferir cadeia/verificação de ID token Google via biblioteca/SDK autenticado, `iss/aud/exp`, `email_verified` e **claim assinado `hd`** para Workspace sempre que disponível. O parâmetro de request `hd` é mero hint de UI; se o Supabase não disponibilizar uma prova verificável de `hd`, a implementação deverá bloquear autorização restrita até definir mecanismo verificável equivalente em nova clarificação. Não confiar em `user_metadata.hd` gravável.
- Usar **Before User Created Hook** de Supabase para impedir novos cadastros indevidos por provider/domínio, com políticas negadas por padrão. O hook não protege contas antigas, tokens já emitidos nem substitui autorização RLS por recurso em cada API.
- O fluxo de demonstração privada à diretoria continua com **identidades sintéticas**, não alunos reais. Acesso efetivo de menores/estudantes depende de configuração/aprovação do administrador Google Workspace e avaliações institucionais de privacidade e consentimento.
- Contas de **docentes/organizadores** exigem matriz de papéis distinta, com convite/atribuição administrativos verificados; não conceder admin só por usar e-mail institucional `@ifma.edu.br`. Escolas externas e Gmail pessoal ficam **fora do MVP inicial**, mas a arquitetura deve permitir abrir novos tenants posteriormente sem violar isolamento.

## Dependências externas e risco institucional

O administrador Google Workspace for Education do IFMA pode bloquear aplicativos OAuth terceiros; **menores de 18 anos não podem acessar apps terceiros não configurados sem aprovação administrativa**. Antes de implementar login para estudantes, testar com pelo menos uma conta acadêmica de teste autorizada: qual e-mail, `hd`, token do Google e papel efetivo; quem administra domínio e consent screen; se o app exige aprovação no console Workspace. Se Google Classroom usar fluxo federado SUAP diferente de OAuth normal, abrir clarificação **antes** de codificar suposição errada.

## Fontes

- [Supabase — Sign in with Google](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Supabase — Before User Created Hook](https://supabase.com/docs/guides/auth/auth-hooks/before-user-created-hook)
- [Google — OpenID Connect e `hd`](https://developers.google.com/identity/openid-connect/openid-connect)
- [Google Classroom Help — controles para estudantes menores e apps terceiros](https://support.google.com/edu/classroom/answer/15163043?hl=pt-BR)
- [Google Workspace Help — acesso a apps terceiros](https://support.google.com/a/answer/7281227)
- [Material educacional do IFMA — e-mail `@acad.ifma.edu.br`](https://educapes.capes.gov.br/bitstream/capes/743121/2/Produto%20educacional%20-%20Magalh%C3%A3es%20e%20Pedrosa.%202024.pdf) — verificar identidade real do Workspace; não usar como fonte única de autorização.

**Não feito:** Google Cloud OAuth Client, conta Supabase, credenciais, login de aluno, contatos à DTI, mudança de permissões Workspace, deploy, RLS real ou liberação G-PROD. A aprovação deste requisito não ratifica S03 integral nem substitui I3/I4/I5.
