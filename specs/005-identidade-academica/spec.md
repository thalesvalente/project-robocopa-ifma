# Feature 005 — Identidade Google pessoal e acadêmica, participação multiescola

**Estado:** especificação revisada ANTES do incremento de política; login real e piloto continuam não implementados. **Data:** 2026-10-10. **Decisões:** [D-011 (vigente)](../../docs/planejamento/decisoes/D-011-google-pessoal-multiescolas.md), [D-010 (histórica)](../../docs/planejamento/decisoes/D-010-login-google-academico-ifma.md), [ADR-008](../../docs/arquitetura/ADR-008-google-multiescolas.md). Referências macro S03 identidade, S04 autorização de jobs, S08 implantação e LGPD. Não marcar backlog macro ratificado.

## Objetivo

Qualquer estudante admitido em uma escola participante poderá **autenticar-se com conta Google acadêmica Workspace ou conta pessoal `@gmail.com`**, por um mesmo provedor OAuth no Supabase Auth. Não haverá senha RoboCopa. A autenticação com qualquer uma das contas **não confere matrícula, papel, acesso a robôs de outra pessoa nem permissão de competir**. A participação depende de convite/aprovação e vínculo da escola/turma/competição com estado ACTIVE. Outras escolas são previstas pela arquitetura, sem presumir lançamento público antes dos gates.

## Requisitos verificáveis

- **RF-ID01**: botão único "Continuar com Google" sem `hd` obrigatório; OAuth seguro, callback validado, Google sub como identidade estável e e-mail verificado. Não ativar login por senha ou outros provedores no MVP.
- **RF-ID02**: acesso pessoal Gmail verificado (sem `hd`) é permitido para criar conta `PENDING`. Não exigir claim Workspace nem barrar globalmente `@gmail.com`.
- **RF-ID03**: acesso acadêmico Workspace usa `hd` assinado quando é feita a afirmação de instituição; endereço/sufixo textual não prova domínio; domínio IFMA Google ainda requer confirmação via DTI/SUAP.
- **RF-ID04**: conta de qualquer origem fica `PENDING` sem vínculo ativo com escola. Somente organizador/professor autorizado valida escola, turma, papel e competição. Gmail pessoal e Workspace seguem **as mesmas regras de autorização de recurso**.
- **RF-ID05**: escola como tenant com IDs opacos; isolamentos entre escolas e papéis por associação, revogação/suspensão imediata via API e RLS. Possibilidade de múltiplos vínculos por usuário sem cruzar dados.
- **RF-ID06**: não permitir autoatribuição de escola, papel organizador, `owner_ref`, tenant ou turma via client metadata; convite só por entidade confiável, uso único/expiração/rate limit. Não conceder acesso por `email_verified` sozinho.
- **RF-ID07**: proteção de menores e política de dados escolar; conta pessoal **não** contorna controles institucionais nem equivale a autorização de responsável. Administração Workspace pode precisar liberar app externo; uso de dados reais depende de consentimento/avaliação institucional.
- **RF-ID08**: manter demonstração privada com identidades sintéticas, sem alegar OAuth de Google real por teste com mocks; testes no telefone físico e piloto só após os gates.

## Histórias e aceite

**US-ID1 — dois tipos de login**: estudantes com Google Workspace acadêmico ou Gmail pessoal verificável conseguem abrir sessão Supabase; ambos inicialmente `PENDING` e não participam automaticamente. Gmail `@gmail.com` não precisa ter `hd`.

**US-ID2 — escola aprova participante**: responsável autorizado vincula estudante à escola/turma/competição; a partir de ACTIVE, ações somente no escopo associado. Uma conta Gmail pessoal pode participar representando a escola aprovada.

**US-ID3 — isolamento entre escolas**: escola A não acessa programas privados/placares internos de B, inclusive com usuário matriculado em mais de uma escola sem escolher autorização correta por operação.

**US-ID4 — segurança e suspensão**: token inválido, identidade falsa, `hd` textual injetado, papel escrito pelo cliente, convite reutilizado, vínculo PENDING/SUSPENDED ou nova sessão após bloqueio são negados no backend/RLS.

**US-ID5 — conta Workspace/menores**: verificar Google Workspace real do IFMA ou outras escolas e regras do administrador para usuários menores. Para Gmail pessoal, não inferir idade ou consentimento de `gmail.com`.

**US-ID6 — demonstração diretoria**: usar contas sintéticas sem estudantes reais; documentar diferenças entre autorização simulada e OAuth real, inclusive falhas controladas.

## Clarificações antes de liberação

- **Q-ID01:** domínio efetivo Google Workspace dos alunos IFMA pode diferir de `acad.ifma.edu.br` do e-mail acadêmico; validar no SUAP/Google admin.
- **Q-ID02:** política de terceiros para menores e controles Google Workspace.
- **Q-ID03:** disponibilidade verificável de `hd` quando precisar provar uma organização; `hd` ausente é normal para Gmail.
- **Q-ID04:** quem institui escola, comprova matrícula/convite e aprova vínculos; validação LGPD e menores.
- **Q-ID05:** autorização para escolas externas e condição de abertura de piloto; operação interna/demo antes da abertura.
- **Q-ID06:** regras para Google Account com endereço não Gmail e sem Workspace `hd` (fora do recorte inicial, sem permissão automática).

## Não objetivos

Password da RoboCopa, login Facebook/Apple, integração Drive/Classroom, matrícula automática por e-mail, aceitar convite não validado pelo servidor, sincronizar SUAP sem consentimento, promover organizador por `@ifma.edu.br`, contas arbitrárias sem provedor Google e liberar torneio público sem revisão de segurança.

## Rastreabilidade

[Plano](plan.md), [tarefas](tasks.md), [contrato de elegibilidade](contracts/google-eligibility.md), [pesquisa](research.md); [ADR-008](../../docs/arquitetura/ADR-008-google-multiescolas.md). G-PROD continua BLOQUEADO.
