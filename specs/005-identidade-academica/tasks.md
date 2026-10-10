# Tarefas da feature 005 — Identidade acadêmica com Google

**Estado:** tarefas PLANEJADAS, não executadas. Tudo deve entrar em commits de planejamento antes de código ou configuração real. O backlog canônico não deve ser marcado como concluído por esta feature, e não autoriza liberação de alunos.

- [ ] **ID-001** [US-ID1/5] Confirmar com administrador IFMA Google Workspace o domínio efetivo da conta Google dos estudantes e fluxo SUAP/Google Sala de Aula com uma conta de teste autorizada. Registrar valores de configuração sem nomes/PII/tokens. Resolver Q-ID01.
- [ ] **ID-002** [US-ID1/5] Confirmar política para aplicativos OAuth externos e menores de 18, responsável pelo Google Cloud OAuth Client, consent screen, escopos mínimos, callback e app approval. Resolver Q-ID02.
- [ ] **ID-003** [US-ID1/3] Validar tecnicamente o `hd` confiável na identidade Google emitida pelo fluxo Supabase; não aceitar `hd` de URL/request ou metadata user-editable. Se não disponível, planejar método seguro antes da implementação. Resolver Q-ID03.
- [ ] **ID-004** [US-ID2/3] Especificar e implementar (CI PostgreSQL) perfis, vínculo campus/turma/participação, status e papéis com RLS/deny-by-default. Não transformar qualquer `@acad.ifma.edu.br` em aluno autorizado sem vínculo. Resolver Q-ID04.
- [ ] **ID-005** [US-ID4] Implementar e testar Before User Created Hook restritivo (Google/provider/domínio), sem confundi-lo com barreira para usuário já existente; testes de troca de papel/vínculo e token antigo.
- [ ] **ID-006** [US-ID1/6] Implementar PWA "Entrar com Google acadêmico" em projeto de teste com Supabase Auth e fluxo OIDC controlado. Sem senha local/refresh tokens Google desnecessários ou segredos no JS.
- [ ] **ID-007** [US-ID2/3/4] Testes negativos: Gmail pessoal, domínio sósia, sem `hd`, token ausente/expirado/audience divergente, sem vínculo, suspenso, cross-campus, cliente fingindo professor, callback adulterado e RLS.
- [ ] **ID-008** [US-ID5/6] Executar E2E com conta Google acadêmica **de teste** e telefone físico, sujeito a autorizações/Google admin, confirmar resultado sanitizado; nenhuma pessoa real no CI público.
- [ ] **ID-009** [US-ID1..6] Reconciliar Spec Kit, decisões, documentação, CI e evidências por SHA; não declarar autenticado se só foram executados mocks e não habilitar G-PROD.

