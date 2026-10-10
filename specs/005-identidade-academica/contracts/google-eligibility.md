# Contrato ID-010 — Classificação local de identidade Google já verificada

**Status:** classificador offline ID-010 implementado e validado no CI conforme [evidência S03-ID-010](../../../docs/qualidade/evidencias/S03-ID-010.md); **não** substitui verificação OIDC, login Supabase ou autorização SQL. **Fontes:** D-011 e ADR-008.

## Entrada de fronteira confiável

O classificador recebe `VerifiedGoogleIdentity(provider, provider_sub, email, email_verified, hosted_domain)`, **somente de adaptador backend que já verificou** Google OIDC e vínculo ao usuário Supabase. Strings/campos vindos diretamente do navegador não devem instanciar este contrato de produção; testes unitários usam fixtures declaradamente sintéticas.

Sem token bruto, senha, metadata user-editable, matrícula, escola/role/owner no objeto de identidade. `provider=google`, `provider_sub` não vazio, `email_verified is True`, e-mail válido e `hosted_domain` como `None` ou domínio autenticado, já normalizado e confiável.

## Decisão pura

- `email` com domínio exatamente `gmail.com` (case-insensitive) **e** `hosted_domain is None` → `PERSONAL_GMAIL`; resultado `PENDING` e **nenhuma escola/papel**.
- `hosted_domain` válido presente e fornecido pelo verificador OIDC Google → `WORKSPACE`; resultado `PENDING` e **nenhuma escola/papel**. Domínio Workspace ainda não é garantia de escola cadastrada.
- `email` de domínio não Gmail sem `hd` confiável → `UNSUPPORTED` no recorte inicial, sem participação. Não classificá-lo como Workspace só pelo sufixo `@acad.ifma.edu.br`.
- Falta de Google provider/sub, e-mail não verificado, campos malformados, `hd` vazio/string inválida, e-mail Gmail com `hd` presente incoerente, ou alegação de autoridade fora do contrato → negar elegibilidade.
- `PENDING` **sempre** significa sem participação, treino ou inscrição; identidade elegível não libera operações.

## A autorização efetiva é outro serviço

Um autorizador posterior receberá `user_id` interno da sessão Supabase + `school_id`/scope canônico e somente retornará acesso se o **vínculo confiável** daquelas entidades estiver `ACTIVE`. Convite da escola deve ser aprovado por docente/organizador. `@gmail.com` não prova matrícula e `hd` não prova permissão.

## Aceite e limitações

- Todos os caminhos permitidos e negados com fixtures de dados sintéticos, incluindo caso com `hd` ausente, `hd` falso textual, e-mail com domínio sósia, `sub` ausente, provider diferente, vazio e tipos falsos.
- Nenhum teste deste recorte alega validação de assinatura Google, callback, sessão real, JWT, RLS ou autorização Workspace/menores.
- Não permitir worker/bot, logs ou UI alterarem `hosted_domain` ou `approval`. Todo dado escolar deve vir de autorização real em PostgreSQL e contas reais somente depois de gate institucional.
