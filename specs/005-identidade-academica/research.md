# Pesquisa inicial — Google acadêmico IFMA

**Data:** 2026-10-10. Esta pesquisa orienta o planejamento; não comprova uma conexão real à conta IFMA Google Workspace.

| Tema | Evidência | Implicação |
|---|---|---|
| Domínio acadêmico do IFMA | Produto educacional depositado no eduCAPES descreve e-mail discente no formato `nome@acad.ifma.edu.br`. https://educapes.capes.gov.br/bitstream/capes/743121/2/Produto%20educacional%20-%20Magalh%C3%A3es%20e%20Pedrosa.%202024.pdf | **Candidato**, confirmar se é Google Workspace/SSO, não hardcode do token ainda. |
| Campo Google Sala de Aula no SUAP | Extratos SUAP públicos distinguem "E-mail Acadêmico" e "E-mail Google Sala de Aula"; entrada Google for Education pode usar link SSO dentro do SUAP, não senha autônoma. | Necessária conta de teste autorizada e confirmação do fluxo; não inferir `hd` do formato do e-mail. |
| Supabase Google | https://supabase.com/docs/guides/auth/social-login/auth-google | Google OAuth pelo Supabase, scopes mínimos, client ID/secret e callback. |
| Validação Google | https://developers.google.com/identity/openid-connect/openid-connect | Google `sub` identifica conta, `hd` assinado prova Workspace; hint de request não restringe servidor. |
| Hook de criação | https://supabase.com/docs/guides/auth/auth-hooks/before-user-created-hook | Gatilho para barrar novos cadastros por provider/domínio. Não cobre contas antigas nem substitui autorização. |
| Menores/Google Education | https://support.google.com/edu/classroom/answer/15163043?hl=pt-BR | Admin do Google Workspace precisa liberar apps terceiros não configurados para menores de 18; risco institucional real. |
| Acesso a apps terceiros | https://support.google.com/a/answer/7281227 | Administrador pode configurar apps OAuth; app externo pode ser bloqueado. |

**Conclusão de pesquisa:** a solução é tecnicamente viável **se** a conta escolar for uma identidade Google OAuth acessível; a política para menores e o domínio real ainda precisam ser provados. É inadequado liberar cadastro apenas comparando `email.endsWith('@acad.ifma.edu.br')`. Priorizar confirmação admin/campus antes de programar o fluxo dependente do domínio.

