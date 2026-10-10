# D-008 — Prioridade de hospedagem Vercel condicionada à elegibilidade do Hobby

**Data:** 2026-10-10. **Tipo:** revisão de preferência aprovada pelo responsável após confrontar as políticas oficiais da Vercel. **Estado:** DIREÇÃO APROVADA, **elegibilidade do Hobby para publicação institucional A CONFIRMAR**. **Revisa apenas** a prioridade Cloudflare Pages da D-007/ADR-006, sem invalidar decisões técnicas já testadas.

## Fundamentação verificada

1. [Vercel Terms of Service §4](https://vercel.com/legal/terms): a modalidade Hobby é gratuita e o texto permite uso **personal or non-commercial**; a Vercel reserva-se o direito de suspender deployments/alterar condições.
2. [Vercel Fair Use Guidelines — Commercial Usage](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage): exige uso pessoal não comercial no Hobby; classifica como comercial uma implantação destinada a ganho financeiro de pessoas envolvidas na produção, **incluindo empregados pagos e consultores**.
3. [Vercel Staff — caso de organização sem fins lucrativos](https://community.vercel.com/t/question-about-commercial-usage/23321/4): uma integrante da equipe confirmou a admissibilidade do projeto de alunos **voluntários e não remunerados** para uma organização sem fins lucrativos. A resposta é contextual, não parecer contratual individual para a RoboCopa/IFMA.
4. [Hobby Plan](https://vercel.com/docs/plans/hobby), [colaboração](https://vercel.com/docs/deployments/troubleshoot-project-collaboration) e [retenção de deployments no Hobby (set/2026)](https://vercel.com/changelog/hobby-projects-now-retain-fewer-deployments-to-free-up-storage): existem limites e regras operacionais que não são garantias de disponibilidade ou aptidão para uso institucional.

**Interpretação prudente:** IFMA público e sem fins lucrativos + RoboCopa gratuita **favorecem** o caráter não comercial, mas **não provam automaticamente** elegibilidade do Hobby. É necessário verificar a natureza concreta do desenvolvimento/manutenção e eventual remuneração funcional. Não afirmar nem que "é proibido por ser institucional" nem que "está liberado porque é público".

## Decisão atual

- **Primeira preferência:** **Vercel** para PWA estática React/TypeScript, mobile-first; preservar a familiaridade com o deploy gratuito e a stack do projeto. **Uso do plano Hobby para divulgação oficial/estudantes condicionado à confirmação do enquadramento e aos limites aplicáveis.**
- **Contingência:** **Cloudflare Pages** (ou outra hospedagem estática compatível), somente se os termos, a colaboração, custo ou disponibilidade não permitirem o Hobby. Não mudar todo o backend por causa do frontend.
- **Persistência e controle:** Supabase Auth/PostgreSQL/Storage e API curta de serviço permanecem; SQLite é só teste. Motor/bots/worker ficam na VM Linux dedicada, fora do frontend. Manter fronteiras, quotas e gates.
- **Portabilidade:** gerar PWA estática, sem API obrigatória ou funcionalidades proprietárias da Vercel como dependência de domínio. Testar fallback apenas quando útil; preferir engenharia enxuta.
- **Dois marcos:** demonstração privada à diretoria com contas sintéticas e estratégias conhecidas antes de piloto com estudantes; nenhuma hospedagem gratuita por si autoriza alunos, bots não confiáveis ou G-PROD.

## Aceite contratual e gates ainda abertos

- [ ] Registrar se desenvolvimento/manutenção se enquadram como atividade profissional remunerada para fins das Guidelines, sem publicar informações pessoais.
- [ ] Obter resposta escrita da Vercel descrevendo projeto público, educacional gratuito, participantes e relação de remuneração, **ou** avaliação formal institucional suficiente para decidir elegibilidade antes de uso oficial com estudantes.
- [ ] Conferir integração Git, tipo da conta/repositório, colaboração, quotas, retenção, disponibilidade e ausência de segredos/PII no build.
- [ ] Revisar a cláusula de uso de conteúdo para treinamento de IA dos Terms §3 e, quando aplicável, **desabilitar Model Training nas Team Settings**; não enviar códigos/dados pessoais de alunos para o deployment/telemetria Vercel.
- [ ] Se confirmação for negativa/inconclusiva, manter PWA portável e optar por Cloudflare Pages ou outro provedor autorizado; não contratar Pro sem decisão humana.
- [ ] Registrar a decisão operacional definitiva nos HYB-09/S08, após evidência, e realizar demonstração técnica autorizada.

**Não feito por este documento:** criação de conta/projeto, deploy, domínio, pagamento, configuração DNS/firewall, VM, processamento de alunos ou homologação institucional. O direito de usar um provedor não substitui testes de isolamento I3/I4/I5 ou proteção de dados educacionais.

**Precedência:** D-008 esclarece **D-006** e ajusta a preferência indicada em **D-007** e **ADR-006**. ADR-005 e feature 001 passam a reconhecer Vercel primeira escolha condicional; Cloudflare segunda escolha. Não apagar a trajetória histórica ou reclassificar provas antigas.
