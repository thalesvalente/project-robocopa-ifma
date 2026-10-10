# ADR-008 — Google OAuth para contas institucionais e pessoais, com autorização multiescola

**Data:** 2026-10-10. **Estado:** DIREÇÃO APROVADA em D-011, mecanismo concreto ainda não implantado. **Supersede parcialmente:** ADR-007 quanto a proibir Gmail pessoal e exigir `hd` em todos os logins. **Preserva:** Supabase Auth, PWA Vercel, PostgreSQL/RLS, identidade estável e autorização por vínculo. [D-011](../planejamento/decisoes/D-011-google-pessoal-multiescolas.md) · [Spec Kit feature 005](../../specs/005-identidade-academica/spec.md).

## Fronteiras

```text
PWA Vercel -> Google OAuth (apenas Google, sem senha RoboCopa)
            -> Supabase Auth (sessão autenticada)
            -> API confiável -> classificação de identidade Google verificada
                              -> school_memberships (PENDING/ACTIVE/SUSPENDED)
                              -> autorização contextual + RLS -> trabalho/versão/inscrição
                                                        |
                                         execução isolada VM (sem sessão Google)
```

No MVP, a tela mostra **"Continuar com Google"** e **não envia `hd` obrigatório/global** na solicitação OAuth; opção de sugestão do Workspace pode surgir depois apenas para UX e sempre sem efeito de autorização. Um Google Workspace `hd` verificável identifica domínio hospedado; para conta pessoal `@gmail.com`, **`hd` ausente é o comportamento esperado**. Não aceitar como corporativo `email.endsWith('@ifma.edu.br')` sem prova OIDC.

## Contratos e invariantes

1. **Fonte de identidade autenticada:** verificador/SDK backend comprova `iss` Google, `aud` cliente autorizado, `exp`, assinatura, `sub`, `email_verified` e origem do provedor, com correlação à conta `auth.users.id`/Supabase. Não confiar em propriedades inseridas pelo navegador, hint `hd` de URL, `user_metadata` editável ou e-mail como chave primária.
2. **Tipos distintos:** `GOOGLE_PERSONAL` requer endereço Gmail verificado e ausência de `hd`; `GOOGLE_WORKSPACE` requer `hd` assinado não vazio e e-mail verificado; contas fora dessas condições ficam `PENDING/UNSUPPORTED` ou são recusadas conforme política publicada. **Tipo não é permissão**. Domínios escolares são dados de configuração após confirmação do administrador; IFMA `acad.ifma.edu.br` continua candidato sem prova Workspace.
3. **Separação do vínculo:** `auth.users.id` → `school_memberships(user_id, school_id, status, role, scopes...)` pelo menos 1:N; escolas/turmas têm IDs opacos e políticas RLS tenant-aware. O convite só pode ser emitido por professor/organizador aprovado; aceitação unilateral não prova matrícula; aprovação deve ser registrada pelo backend. Revogação suspende operações existentes conforme política.
4. **Sessão inicial:** conta Google verificada pode autenticar, mas perfil/vínculo inicia `PENDING`; UI deve distinguir "conectado" de "participação aprovada". Apenas privilégios mínimos (ex.: ver próprio pedido de vínculo) antes de ACTIVE. Treino/inscrição/placar privado bloqueados. Não criar admin baseado em domínio/conta pessoal.
5. **Proteção transversal:** validação de permissão por operação e recurso em toda API e RLS, inclusive para usuários anteriormente cadastrados; log seguro de troca de papel, scope, escola e suspensão; cookies/tokens não fornecidos ao bot/worker; sem service-role no bundle Vercel.
6. **Idempotência e execução:** o owner da admissão I3-03B é derivado da sessão validada e vínculo ativo, nunca de `owner_ref` de cliente. `scope_id` de torneio deve coincidir com `school_id`/vínculo aprovado; contrato de execução não será acoplado à string do e-mail Google.

## Diferenciações de risco

O Google Admin pode bloquear aplicativos OAuth terceiros para menores em domínio Workspace (varia segundo configuração, inclusive exceções para escopos básicos); **Gmail pessoal não elimina os deveres de proteção de menores e de autorização da escola**. Regras de inscrição e consentimento para estudantes e escolas externas precisam de validação institucional. Não usar identidade pessoal como bypass de controle de turma. Não solicitar escopos Drive/Classroom e não assumir SAML empresarial pago.

## Testes/gates

- Unitários puros sintéticos: Gmail pessoal com `hd` ausente + e-mail verificado => elegível para **conta PENDING**; Workspace com `hd` verificado => elegível para PENDING; Gmail sem verificação, provedor divergente, Workspace falso por sufixo, dados malformados => recusado; conta ACTIVE sem vínculo, papel de outro tenant, vínculo SUSPENDED => operação negada. Nenhum desses testes demonstra autenticação OAuth criptográfica.
- Integração PostgreSQL: vínculos, RLS por escola, convites e controle de permissões, concorrência/suspensão, negações cruzadas; precedidos por contrato Spec Kit.
- Google real + Supabase Auth: sessão pessoal **e** Workspace de teste, `hd` real se houver, `sub`/provider autenticado, logout e frontend no celular, callback/PKCE; menores e uso institucional demandam aprovação cabível.
- G-PROD permanece BLOQUEADO até todos os gates de segurança, dados, VM, backup e homologação.

**Não implementado por esta ADR:** OAuth/Google Client, migrations de vínculos, RLS em Supabase, convites e operação aberta.
