# Tarefas — Feature 005 (Google Workspace e Gmail pessoal)

**Data:** 2026-10-10. **Estado:** D-011 aprovada e plano Spec Kit atualizado ANTES de qualquer implementação. Histórico D-010/ID-001..09 é preservado em Git, porém as tarefas abaixo substituem versões que proibiam Gmail. S03/S04/S08 e G-PROD não são fechadas por documentação.

- [ ] **ID-001** Confirmar domínio real/Google Workspace IFMA e eventual integração SUAP com conta de teste autorizada; não presumir `acad.ifma.edu.br` como claim `hd` efetivo.
- [ ] **ID-002** Confirmar regras Google Workspace for Education para app terceiro e menores; registrar também política de Gmail pessoal/consentimento e aprovação institucional antes do piloto.
- [ ] **ID-003** Verificar token Google/Supabase real: `sub`, `email_verified`, `iss/aud/exp`, `hd` assinado quando Workspace; **ausência de hd no Gmail é válida**. Não confiar em parâmetro `hd` de request.
- [ ] **ID-004** Desenhar e testar PostgreSQL/RLS com `schools`, `school_memberships`, status, papéis e contextos de competição, para contas acadêmicas e Gmail sem distinção indevida de direitos.
- [ ] **ID-005** Configurar e testar hook de criação que permita **Gmail pessoal e Workspace verificados por Google** e rejeite outros provedores indevidos; não usar hook como substituto de autorização.
- [ ] **ID-006** Implementar frontend Vercel com "Continuar com Google" sem forçar Workspace global, em ambiente de teste autorizado; sem senhas próprias.
- [ ] **ID-007** Testes negativos de autenticação/autorização: `hd` falso ou ausente de Workspace, Gmail não verificado, papel autoatribuído, entrada de escola falsa, convite repetido, PENDING/SUSPENDED, tenant cruzado, JWT inválido, acesso entre turmas.
- [ ] **ID-008** E2E em celular e OAuth real com contas **de teste** (Gmail e Workspace quando disponível), com proteção de menores e dados minimizados, sem PII em Git/artefatos.
- [ ] **ID-009** Sincronizar Spec Kit, decisões, índice, evidências/CI e gates reais a cada incremento.
- [x] **ID-010** [recorte CI inicial] Implementar política pura de classificação de identidades **já verificadas**, com Gmail `@gmail.com` sem `hd` e Workspace com `hd` autenticado; sempre iniciar PENDING sem derivar escola/papel. Testar provider, sub, email_verified, hd textual forjado, dados malformados. **Não é login OAuth real.**
- [ ] **ID-011** [posterior] Planejar e implementar convites/aprovação multiescola no servidor e RLS de vínculos ACTIVE por escola/turma, com TTL, rate limit, auditoria e suspensão.
- [ ] **ID-012** [posterior] Exercitar casos multi-escola e onboarding externo sob revisão institucional; não confundir conta permitida com torneio publicamente aberto.

**Regra de execução:** incluir lacuna no plano ANTES de qualquer patch de código; só marcar checkbox quando houver relatório e testes no SHA correto.

**Evidência ID-010:** plano publicado primeiro no commit `4f4b911` e política offline implementada depois no commit `2dcea3c`. [Relatório S03-ID-010](../../docs/qualidade/evidencias/S03-ID-010.md) confirma **20 casos sintéticos PASS** no CI, além do planejamento e autoria. Os testes não representam login Google real nem autorização escolar; ID-001..009, ID-011/012, S03 e G-PROD permanecem abertos.

## Priorização da apresentação à diretoria — D-012 (2026-10-10)

**ID-011 e ID-012, bem como a conexão OAuth Google real ID-001..009, NÃO fazem parte do caminho crítico da demonstração controlada (Marco A)**. Permanecem **[ ]** e são planejadas para o **Marco B**, piloto com estudantes e expansão para outras escolas, conforme [D-012](../../docs/planejamento/decisoes/D-012-prioridade-demonstracao-diretoria.md). **A D-011 de aceitar Google acadêmico OU Gmail pessoal continua válida para o produto**. O classificador ID-010 testado no CI permanece prova offline, não login. O MARCO A usa identidades sintéticas, acesso estritamente restrito, sem liberação de estudantes.
