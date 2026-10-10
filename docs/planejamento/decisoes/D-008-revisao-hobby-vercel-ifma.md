# D-008 — Prioridade de hospedagem Vercel condicionada à elegibilidade do Hobby

**Data:** 2026-10-10. **Tipo:** revisão de preferência aprovada pelo responsável após confrontar as políticas oficiais da Vercel. **Estado:** DIREÇÃO APROVADA, **caráter não comercial declarado e enquadramento Hobby favorável em princípio (D-009); verificações de conta, quotas e publicação ainda pendentes**. **Revisa apenas** a prioridade Cloudflare Pages da D-007/ADR-006, sem invalidar decisões técnicas já testadas.

## Fundamentação verificada

1. [Vercel Terms of Service §4](https://vercel.com/legal/terms): a modalidade Hobby é gratuita e o texto permite uso **personal or non-commercial**; a Vercel reserva-se o direito de suspender deployments/alterar condições.
2. [Vercel Fair Use Guidelines — Commercial Usage](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage): exige uso pessoal não comercial no Hobby; classifica como comercial uma implantação destinada a ganho financeiro de pessoas envolvidas na produção, **incluindo empregados pagos e consultores**.
3. [Vercel Staff — caso de organização sem fins lucrativos](https://community.vercel.com/t/question-about-commercial-usage/23321/4): uma integrante da equipe confirmou a admissibilidade do projeto de alunos **voluntários e não remunerados** para uma organização sem fins lucrativos. A resposta é contextual, não parecer contratual individual para a RoboCopa/IFMA.
4. [Hobby Plan](https://vercel.com/docs/plans/hobby), [colaboração](https://vercel.com/docs/deployments/troubleshoot-project-collaboration) e [retenção de deployments no Hobby (set/2026)](https://vercel.com/changelog/hobby-projects-now-retain-fewer-deployments-to-free-up-storage): existem limites e regras operacionais que não são garantias de disponibilidade ou aptidão para uso institucional.

**Interpretação atualizada (D-009):** o responsável esclareceu que a RoboCopa é **desenvolvida voluntariamente e sem remuneração relacionada ao projeto**. Essa situação concreta corresponde ao caso favorável respondido por Vercel Staff, e não há motivo para presumir que o trabalho seja comercial só pelo vínculo ao IFMA. Reavaliar apenas se as condições concretas mudarem. Não afirmar nem que "é proibido por ser institucional" nem que "está liberado porque é público".

## Decisão atual

- **Primeira preferência:** **Vercel** para PWA estática React/TypeScript, mobile-first; preservar a familiaridade com o deploy gratuito e a stack do projeto. **Hobby compatível em princípio com o voluntariado declarado; verificar limites, titularidade e regras operacionais antes da publicação.**
- **Contingência:** **Cloudflare Pages** (ou outra hospedagem estática compatível), somente se os termos, a colaboração, custo ou disponibilidade não permitirem o Hobby. Não mudar todo o backend por causa do frontend.
- **Persistência e controle:** Supabase Auth/PostgreSQL/Storage e API curta de serviço permanecem; SQLite é só teste. Motor/bots/worker ficam na VM Linux dedicada, fora do frontend. Manter fronteiras, quotas e gates.
- **Portabilidade:** gerar PWA estática, sem API obrigatória ou funcionalidades proprietárias da Vercel como dependência de domínio. Testar fallback apenas quando útil; preferir engenharia enxuta.
- **Dois marcos:** demonstração privada à diretoria com contas sintéticas e estratégias conhecidas antes de piloto com estudantes; nenhuma hospedagem gratuita por si autoriza alunos, bots não confiáveis ou G-PROD.

## Aceite contratual e gates ainda abertos

- [x] Registrar o fato material declarado: **não há remuneração relacionada ao desenvolvimento da RoboCopa**; [D-009](D-009-carater-voluntario-vercel-hobby.md).
- [x] Confrontar com Terms, Fair Use e caso análogo respondido por Vercel Staff: **interpretação favorável ao Hobby com base nas condições declaradas**. **Carta individual não é gate genérico obrigatório**; consulta adicional é facultativa se restar dúvida concreta. A titularidade de conta em nome do IFMA e sua autorização administrativa são questões separadas.
- [ ] Conferir integração Git, tipo da conta/repositório, colaboração, quotas, retenção, disponibilidade e ausência de segredos/PII no build.
- [ ] Revisar a cláusula de uso de conteúdo para treinamento de IA dos Terms §3 e, quando aplicável, **desabilitar Model Training nas Team Settings**; não enviar códigos/dados pessoais de alunos para o deployment/telemetria Vercel.
- [ ] Se os fatos mudarem, surgirem objeções do fornecedor ou restrições relevantes, reavaliar o Hobby e manter Cloudflare Pages como alternativa; não contratar Pro sem decisão humana.
- [ ] Registrar a decisão operacional definitiva nos HYB-09/S08, após evidência, e realizar demonstração técnica autorizada.

**Não feito por este documento:** criação de conta/projeto, deploy, domínio, pagamento, configuração DNS/firewall, VM, processamento de alunos ou homologação institucional. O direito de usar um provedor não substitui testes de isolamento I3/I4/I5 ou proteção de dados educacionais.

**Precedência:** D-008 esclarece **D-006** e ajusta a preferência indicada em **D-007** e **ADR-006**. ADR-005 e feature 001 passam a reconhecer Vercel primeira escolha condicional; Cloudflare segunda escolha. Não apagar a trajetória histórica ou reclassificar provas antigas.

## Precedência D-009 — fato novo de voluntariado (2026-10-10)

O responsável confirmou explicitamente **projeto voluntário, sem remuneração associada**. Portanto, o enquadramento Hobby é **favorável em princípio** e a exigência anterior de carta individual como condição obrigatória deixou de se justificar. A elegibilidade continua dependente dos Terms vigentes e de manter essas condições. Não declarar contrato individual homologado. HYB-09 segue aberto pelas configurações práticas de conta, quotas, colaboração e privacidade. [D-009](D-009-carater-voluntario-vercel-hobby.md).
