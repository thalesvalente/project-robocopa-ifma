# Trilha prioritária Spec Kit — Demonstração RoboCopa à diretoria (Marco A)

**Data:** 2026-10-10. **Estado:** REPRIORIZADO / PLANEJADO, ainda sem novo código. **Decisão:** [D-012](../../docs/planejamento/decisoes/D-012-prioridade-demonstracao-diretoria.md). **Backlog macro:** S04-T04 EM_EXECUCAO, S03/S08 e G-PROD não ratificados. **Marcos:** demonstração controlada e piloto com estudantes são distintos. Nenhum usuário real nesta trilha.

## Fluxo end-to-end alvo

1. Avaliador autorizado abre PWA responsiva e altera estratégia em **RoboDSL básica** (sem linguagem geral).
2. API restrita à demonstração valida identidade/escopo DEMO e código com contratos I1, produz versão imutável e trabalho idempotente no PostgreSQL remoto.
3. Broker cloud autoriza worker por identidade própria, entrega trabalho por conexão outbound, e PostgreSQL controla lease/fence/cancelamento.
4. VM Linux dedicada executa Tank Royale em contenção I2, com dois robôs e árbitro separados, sem rede/dados pessoais.
5. Resultado oficial + replay são verificados contra versão, política, tentativa e fence. Transação persiste **efeito único** no resultado; frontend mostra status e replay autorizado.
6. Simular indisponibilidade e recuperação para provar que edição/projetos persistem e o placar não duplica.

## Incrementos ordenados e dependências

- [ ] **DEMO-01 — Reconciliação da base:** alinhar branches #23→#24→#26 e a main com D-011/D-012 (sem modificar evidência histórica); revisar gates e API de demo restrita. Aceite: SHA/árvore, Spec Kit e regressões coerentes, nenhuma alteração de host.
- [ ] **DEMO-02 — Próximo incremento de implementação I3-04:** publicar contrato de resultado/ledger/replay e tarefas técnicas **ANTES do código**. No PostgreSQL isolado CI, atestar que só resultado validado de tentativa vigente afeta score, que duplicatas repetidas/concorrentes/fence vencida/canceladas falham com efeito único. Sem afirmar que arquivo de replay já existe na nuvem.
- [ ] **DEMO-03 — Broker/autenticação operacional:** completar I3-03 e demais recortes I3 com identidade real de serviço, API cloud compatível, claim outbound, quotas, suspensão e recuperação. Testar fail-closed. Nenhum segredo admin em VM/bot/browser.
- [ ] **DEMO-04 — Segurança da VM (I4):** preparar procedimento, aprovação específica do responsável, inspeção de isolamento de host, rede, volumes, permissões, limites e limpeza. CI em Ubuntu não vale como ensaio do computador real.
- [ ] **DEMO-05 — Aplicação de demonstração:** PWA Vercel ou fallback permitido + Supabase PostgreSQL/Storage; autoria real com conta sintética, endpoint restrito e testado, seleção de estratégias admitidas, trabalho e placar/replay. Nenhuma conta acadêmica nem Gmail real obrigatória para o MARCO A.
- [ ] **DEMO-06 — Qualidade operacional/aceite (I5):** backups de banco/Storage e restore, timeout/falha/restart, testes no celular e recursos gratuitos, documentação/rollback e go/no-go de apresentação. G-PROD de estudantes só depois dos gates do piloto.

## Limites, risco e proteção obrigatória

- Contas sintéticas **não significam** API anônima aberta. Qualquer ambiente exposto na internet terá proteção de acesso ao DEMO, quotas, negações e segredos fora do frontend; se não comprovados, demonstrar em ambiente privado/não publicado.
- Somente RoboDSL básica admitida; estratégia alterada pelo avaliador dentro do escopo conhecido e testado. Não executar códigos arbitrários nem permitir bot participante interagir com rede/host/segredos.
- **I3-04** não é simplesmente armazenar placar: deduplicação por `job_id/attempt_id/fence`, commit atômico, integridade de replay e teste contra reentrega exigidos. O resultado oficial do árbitro é fonte; stdout do bot não é.
- Não prometer que CI verde, demonstração sintética ou deploy Vercel/Supabase equivalem a homologação da segurança para alunos, LGPD ou uso institucional.
- A escolha D-011 de **Google acadêmico e Gmail pessoal permanece aprovada**, mas ID-011/convites/tenants e integração OAuth real deixam de bloquear a primeira demonstração. Planejamento detalhado dessas funcionalidades continuará disponível para **Marco B**.
- Todo ajuste descoberto sem planejamento gera adendo Spec Kit antes de patch. Após testes atualizar decisão, `tasks`, evidências/JSON, `ESTADO-ATUAL` e PR.

**Próxima tarefa técnica efetiva (sem execução neste documento):** DEMO-02 / I3-04; precedida pela reconciliação DEMO-01.