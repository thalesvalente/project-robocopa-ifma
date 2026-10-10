# Plano — Feature 005, Google OAuth misto e multiescola (D-011)

**Data:** 2026-10-10 · **Estado:** PLANEJADO ANTES DO CÓDIGO de política. Nenhum login OAuth/Supabase real configurado. D-011/ADR-008 **substituem exclusividade acadêmica da D-010/ADR-007**; histórico preservado.

## Separação de componentes

1. **Identidade Google:** login único "Continuar com Google" via Supabase Auth. Sem `hd` obrigatório no request; `hd` apenas hint opcional de UI para login Workspace, não prova. Nenhuma senha RoboCopa.
2. **Verificação de identidade:** backend validará tokens/sessão Supabase e prova de Google OIDC (issuer/audience/expiry/signature/sub/email_verified) antes de produzir `VerifiedGoogleIdentity`. Integração verdadeira depende de projeto OAuth e Supabase de teste. `hd` autenticado **não** exigido de Gmail pessoal.
3. **Política pura de elegibilidade (primeiro incremento ID-010):** receber **somente objeto de identidade já verificada por adaptador confiável**, com origem Google, Google sub, e-mail verificado, `hd` autenticado se aplicável; classificar `PERSONAL_GMAIL` ou `WORKSPACE` e decidir `PENDING` sem matrícula. Não validar assinatura criptográfica dentro desse objeto; tests com doubles não provam login Google. Não expor função como endpoint client; rejeitar parâmetros extras de role/school vindos do usuário.
4. **Vínculo e autorização (incremento ID-011 e migrações posteriores):** `schools`, `school_memberships`, `classrooms`, `competition_entries`, papéis por vínculo sob RLS. Usuário PENDING pode consultar apenas próprio status. Aprovação somente por ator admin/professor verificado, com convite aprovado/TTL/uso único e auditoria; escola externa entra por fluxo administrativo.
5. **Hooks e Edge/API:** Before User Created Hook pode impedir outros provedores, mas **não pode negar Gmail pessoal só por domínio nem exigir `hd` geral**. Hook não concede ACTIVE ou cobre usuários preexistentes; API/RLS revisam vínculos.
6. **Worker:** não recebe tokens OAuth, acesso direto ao banco ou permissão de escola. O `owner_id` que chega ao I3 provém de `auth.users.id` + vínculo ativo validado pelo broker; nenhuma confiança em owner/role/school do navegador.

## Ordem de execução com testes

- Primeiro documentar D-011/ADR-008/spec/plan/tasks/contrato/pesquisa/índice; só então desenvolver **classificador de elegibilidade puro** com testes negativos e prova de que PENDING não autoriza operações. CI Linux sem rede ou contas reais.
- Depois especificar migrações PostgreSQL/RLS por escola, política de convites e controle de abuso; testar concorrência, autorização cruzada e suspensão em runner descartável. Só marcar ID-011+ conforme aceites.
- Configurar Google OAuth/Supabase em ambiente autorizado. Testar **Gmail pessoal sintético/teste** e conta Workspace de teste, `hd` quando existir, sub e callback PKCE, logout, JWT e limites. Nenhuma credencial em Git/CI aberto.
- Validar LGPD, menores, governança de escola, consentimento e limites do plano gratuito antes de piloto; demonstrar diretoria com identidade sintética e escopo de avaliação transparente.
- Após cada implementação, sincronizar `ESTADO-ATUAL`, task checkboxes/evidências e gate, com SHA/workflow real, sem marcar tarefa ampla ou G-PROD como concluído sem prova.

## Casos negativos obrigatórios

Gmail verificado não recebe escola/role automaticamente; `hd` ausente de Gmail é permitido; Workspace `hd` desconhecido pode fazer login PENDING mas não participar; email institucional sem `hd` comprovado não vira Workspace; Gmail com email_verified false é inelegível; provider ≠ Google/Google sub vazio é inelegível. PENDING/SUSPENDED/tenant divergente negam treino/inscrição, independentemente da origem. Regras de permissão não usam email como key. Usuário pode ter múltiplos vínculos ACTIVE sem vazamento entre escolas.

## Gates abertos

Confirmar IFMA Google Workspace/SUAP, admin para menores, consentimento, atribuição de escolas e convites, RLS, infraestrutura Vercel/Supabase real e worker. **Não usar conta Gmail pessoal para contornar política institucional de menores.**

## Resultado ID-010 — política de classificação offline

O planejamento D-011/ADR-008, a especificação, o contrato e as tarefas foram publicados ANTES do runtime no commit `4f4b911`. A implementação do classificador puro `services/identity/google_policy.py` foi publicada depois, no commit `2dcea3c`, seguida de **20/20 testes unitários sintéticos PASS no CI** (run `38082735138`); planejamento e autoria passaram nos runs `38082734825` e `38082734828`. [Evidência](../../docs/qualidade/evidencias/S03-ID-010.md). Resultado elegível sempre PENDING, sem escola/role; não valida JWT/assinatura Google e não participa de competição. **ID-010 concluída somente no recorte offline; Google OAuth, vínculos escolares, RLS e autorização para menores ainda não foram executados.** Próximo incremento ID-011 exige plano específico antes de SQL, endpoints e convites.

## Desacoplamento do Marco A — D-012

Foi corrigida a prioridade: **modelagem multiescola ID-011, convites, RLS por escola e Google OAuth real** deixam de ser pré-requisito para a apresentação controlada à diretoria. Permanecem necessários antes do **piloto com estudantes reais**, em que Google Workspace/Gmail pessoal foram aprovados. Demonstração (Marco A) usa contas/versões sintéticas e **autorização restrita de DEMO própria**, nunca API pública anônima. Antes da apresentação deve haver acesso protegido, fila/placar/replay íntegros, VM segura e ensaio, conforme [trilha DEMO](../004-isolamento-execucao/demo-diretoria-mvp.md). Não implementar ID-011 por reflexo do CI ID-010: respeitar a nova ordem escolhida pelo responsável. Nenhuma ID pendente marcada como concluída.
