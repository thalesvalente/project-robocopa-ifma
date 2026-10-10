# Feature 005 — Identidade Google acadêmica dos estudantes

**Estado:** ESPECIFICADO/PLANEJADO; não implementado. **Data:** 2026-10-10. **Decisão humana:** [D-010](../../docs/planejamento/decisoes/D-010-login-google-academico-ifma.md). **Design:** [ADR-007](../../docs/arquitetura/ADR-007-autenticacao-google-academica.md). Vincular tarefas macro S03 (identidade), S04 (autorização de jobs) e S08 (implantação/consentimento); checklist do backlog canônico não é modificado pela especificação.

## Objetivo

Estudantes usam a **conta Google acadêmica gerenciada pelo IFMA** em um botão "Entrar com Google acadêmico", sem nova senha RoboCopa, podendo salvar, criar estratégia, solicitar treinos e participar de competições após aprovação de vínculo com turma/campus e requisitos de segurança do MVP. A conta pessoal `@gmail.com` não dá participação de aluno. Não usar e-mail como prova de matrícula.

## Esclarecimentos materiais ainda em aberto (antes de código ligado a contas reais)

- **Q-ID01:** e-mail acadêmico documentado como `@acad.ifma.edu.br` é a mesma conta do Workspace/Google Sala de Aula do IFMA? SUAP mostra separadamente `E-mail Acadêmico` e `E-mail Google Sala de Aula`, podendo exigir login via SUAP. Exigir confirmação com DTI e sessão de teste autorizada; **não fixar `hd` ou client_id de produção antes**.
- **Q-ID02:** o administrador Workspace precisa configurar/aprovar a RoboCopa como app OAuth terceiro? Para usuários menores de 18, app terceiro não configurado pode estar bloqueado.
- **Q-ID03:** como obter, provar e guardar (sem vazamento) o `hd` confiável do token Google no fluxo Supabase escolhido, distinguindo de metadata editável? Definir teste real e rejeição do caso sem `hd`.
- **Q-ID04:** quem publica/aprova vínculo de campus, turma e participante e políticas de retenção/LGPD? Não usar domain-only para admitir automaticamente todos do IFMA, nem criar admin a partir do endereço.

## User stories (critérios verificáveis)

**US-ID1 — login de estudante:** estudante com conta Google Workspace acadêmica autorizada abre a PWA no celular, escolhe conta e conclui OAuth via Supabase; o sistema não pede senha. Usuário com Gmail pessoal ou domínio forjado não obtém sessão **autorizada como estudante**, inclusive em URLs diretas.

**US-ID2 — isolamento por participante/campus:** estudante autenticado só consulta/edita versões de robô e inscrições às quais está autorizado. Mesmo com login IFMA válido, não acessa dados de outra turma/campus sem vínculo expresso. RLS e API fazem negativa por objeto, não por UI.

**US-ID3 — segurança de conta e privilégios:** professor/organizador é atribuído por administrador confiável, não por domínio; tokens expirados, payloads com `role` falsificado, conta suspensa ou OAuth de origem distinta não dão permissão. Sem `anon` ou senha local de estudante.

**US-ID4 — bloqueio de cadastro indevido:** Before User Created Hook barra entradas inelegíveis, mas também há política para contas antigas/vínculos revogados. Usuário Google recém-autenticado pode permanecer em `PENDING` e não consegue treinar nem inscrever robôs antes da autorização.

**US-ID5 — acesso institucional real:** demonstrar com conta IFMA de teste autorizada que a instalação Google/SUAP concede OAuth; se terceiro app bloqueado no Google Workspace, registrar procedimento de solicitação para admin e não habilitar login de aluno até ser aprovado.

**US-ID6 — protótipo da diretoria:** demonstrar com conta sintética em ambiente de laboratório sem dados identificáveis de menores. Se login institucional ainda depender da administração Google, não usar Gmail pessoal como bypass de homologação; demonstrar a UI e o status de dependência com honestidade.

## Não objetivos no MVP

Gmail pessoal de estudantes, recuperação de senha própria, acesso a Google Drive/Classroom, sincronização SUAP/matrícula por API sem autorização, escolas externas sem tenant definido, SAML enterprise pago, múltiplos provedores para estudantes e coleta de CPF/data de nascimento. Recursos intermediários da RoboDSL continuam pós-MVP.

## Restrições de segurança

Somente claims autenticados da identidade Google/OIDC; `hd` do parâmetro de solicitação NÃO é prova. A persistência canônica é Supabase Auth + PostgreSQL/RLS; nenhuma credencial Google/SSO admin, cookie de aluno ou chave privilegiada alcança o frontend estático, worker ou bot. Tokens e respostas OAuth nunca entram em logs/artefatos CI. Contas acadêmicas reais exigem validação institucional e proteção de menores. **G-PROD bloqueado até I3/I4/I5 + autorização.**

## Referências externas

- https://supabase.com/docs/guides/auth/social-login/auth-google
- https://developers.google.com/identity/openid-connect/openid-connect
- https://supabase.com/docs/guides/auth/auth-hooks/before-user-created-hook
- https://support.google.com/edu/classroom/answer/15163043?hl=pt-BR

