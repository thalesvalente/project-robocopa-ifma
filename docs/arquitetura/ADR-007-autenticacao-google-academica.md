# ADR-007 — Google acadêmico do IFMA com Supabase Auth e autorização por vínculo (histórico)

**SUPERADA PARCIALMENTE POR [ADR-008](ADR-008-google-multiescolas.md) / [D-011](../planejamento/decisoes/D-011-google-pessoal-multiescolas.md):** esta era uma proposta de login acadêmico exclusivo e bloqueio de Gmail. A regra atual permite também **Google Gmail pessoal sem `hd`**, mas exige aprovação de vínculo escolar para participação. Preservam-se do desenho original autenticação Supabase, IDs estáveis e RLS; não seguir as antigas negativas de Gmail presentes no texto histórico abaixo.

**Data:** 2026-10-10 · **Estado:** PROPOSTA TÉCNICA COERENTE COM D-010, sujeito a prova da identidade Google Workspace/gestão SUAP. **Rastreabilidade:** [D-010](../planejamento/decisoes/D-010-login-google-academico-ifma.md), [feature 005](../../specs/005-identidade-academica/spec.md), ADR-005, I3-03.

## Decisão arquitetural

PWA estática na Vercel → `supabase.auth.signInWithOAuth({ provider: 'google' })` → Google OIDC → Supabase Auth → sessão Supabase → API com validação de JWT + políticas RLS PostgreSQL → recursos do estudante. Banco, objetos e executor continuam conforme ADR-005; a VM **não recebe Google tokens**, tokens de alunos, senha, cookie de sessão nem service-role.

Apenas os escopos `openid`, `email`, `profile`, necessários à autenticação. Não solicitar Drive, Classroom, contatos, dados escolares ou refresh token offline do Google. O provedor Google guarda a senha. A plataforma trata o Google `sub` como identidade estável do provedor, com `auth.users.id` como chave interna do Supabase.

**Atributo de domínio:** ao solicitar `hd` na UI do Google, seu valor é apenas sugestão; servidor deve validar o `hd` de token Google **com assinatura e audiência verificadas** e `email_verified`, além de `email` de domínio aceito. Se esse dado **não for comprovadamente propagado** pelo Supabase no fluxo padrão, não confiar em campos de metadata de perfil atualizáveis pelo usuário: definir hook/fluxo adicional ou validação id-token Google no backend antes de autorizar. O domínio provisório `acad.ifma.edu.br` NÃO é ratificação de que o Workspace Google/Google Sala de Aula tem esse mesmo domínio.

## Segurança e estrutura de dados

Separar **autenticação** (Google/OIDC), **sessão** (Supabase Auth) e **autorização** (matrícula/vínculo, campus, turma, competição e papel). Cadastro pode existir sem aprovação: `PENDING` não recebe permissão de criar/participar em partidas. Cada operação consulta vínculo ativo/tenant e RLS, nunca `user_metadata.role` nem cabeçalho `X-Owner-Ref` vindo do navegador.

A matrícula não deve ser inferida do endereço, e não deve haver importação de dados pessoais do SUAP sem permissão institucional e desenho LGPD. Para docentes/organizadores, papel é atribuído por administrador autenticado; endereço `@ifma.edu.br` sozinho não dá privilégios. Revogação/suspensão após desligamento de vínculo invalida autorização mesmo com cookie ainda válido.

Bloquear criação indevida via **Before User Created Hook** (quando habilitado), checando provider e domínio, mas tratar esse hook como **defesa adicional**: ele não cobre contas existentes. RLS e backend devem validar participantes autorizados sempre. Proibir método de senha/anon para estudantes no MVP, salvo conta sintética administrada em ambiente de laboratório que não pode acessar dados reais.

Por proteção de menores, exigir autorização/admin do Google Workspace for Education para OAuth externo e política de consentimento institucional. Não presumir que uma tela Google OAuth funcionará com contas Google Classroom do SUAP; criar spike com conta de teste autorizada antes do deploy.

## Trade-offs

- **Custo:** login Google como provedor social do Supabase é adequado à estratégia de usar plano gratuito, sujeito à quota MAU e limites futuros.
- **Fricção:** uma conta escolar evita criação de senhas RoboCopa, mas os alunos sem conta Workspace ativada precisarão de suporte institucional; não substituir por Gmail pessoal sem nova decisão.
- **Controle:** exigir domínio Google e vínculo institucional eleva segurança, mas demanda cadastro de turma/organizador e validação periódica da lista de participantes.
- **Dependência:** Google/IFMA podem bloquear OAuth para menores; necessitamos confirmação administrativa antes de piloto. Contas sintéticas continuam necessárias para apresentação privada.
- **Evolução:** desenho multi-tenant permite futuramente escolas de fora do IFMA sem permitir automaticamente contas Gmail externas no MVP inicial.

## Critérios de aceite e teste

Gate A (prova de identidade): conta acadêmica de teste autorizada, retorno Google comprovado com `hd`, provider, `sub`, e-mail verificado, sem dados de aluno real nos registros Git. Gate B (autorização): Gmail pessoal negado, lookalike negado, tenant cruzado negado, vínculo suspenso negado, perfil sem permissão sem acesso, admin não obtido por email, tokens falsos/expirados negados. Gate C (operação): aluno menor consegue OAuth após liberação do Workspace/autoridade; estado PENDING e política RLS verificados; teste de login/logout em celular; documentar resposta de falha de OAuth sem exposição de tokens.

## Referências

[Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect) · [Supabase Google](https://supabase.com/docs/guides/auth/social-login/auth-google) · [Supabase Hooks](https://supabase.com/docs/guides/auth/auth-hooks/before-user-created-hook) · [Google Workspace menores e terceiros](https://support.google.com/edu/classroom/answer/15163043?hl=pt-BR) · [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).

**Sem mudança operacional nesta ADR:** nenhum usuário Google real criado, credencial/dado de estudante importado, Google OAuth configurado, service-role distribuída ou alteração de VM. G-PROD permanece bloqueado.
