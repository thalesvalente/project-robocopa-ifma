# D-012 — Priorizar demonstração funcional à diretoria antes de multiescolas

**Data:** 2026-10-10 · **Origem:** correção explícita do responsável após proposta de priorizar ID-011. **Estado:** DIREÇÃO PRIORITÁRIA APROVADA PARA PLANEJAMENTO; nenhuma execução nova ou homologação presumida. **Precedência:** reorganiza a ordem das tarefas, **não revoga** a escolha D-011 de Google acadêmico OU Gmail pessoal nem os requisitos de segurança de D-006/ADR-005.

## Objetivo do marco imediato

Demonstrar à diretoria do Campus Itapecuru-Mirim que a RoboCopa permite **programar robô virtual pelo navegador/celular**, validar uma estratégia **RoboDSL básica**, solicitar uma batalha **real no Tank Royale** em execução isolada, observar **placar e replay verificáveis** e recuperar o estado após interrupção do worker. Reaproveitar I1/I2 e núcleo PostgreSQL/admissão I3-03 em PRs ainda draft. A interface demonstrada não é apenas de acompanhamento: deve permitir autoria real de estratégia no escopo limitado.

## Dois marcos distintos (não confundir)

**Marco A: demonstração técnica controlada à diretoria.** Contas e IDs **sintéticos**, conjunto limitado de estratégias RoboDSL validadas, público restrito aos avaliadores, com demonstração autorizada sem estudantes reais; controle de entrada da demonstração implementado e testado, não simples segredo em URL. Pode usar backend de demonstração isolado do ambiente público, com credenciais escopadas e nenhuma execução arbitrária de participantes. Exige integridade de jobs/resultados, sandbox na VM ou runner equivalente autorizado, retenção/recovery e ensaio. **Não usar G-PROD de estudantes como sinônimo do gate de demonstração.**

**Marco B: piloto com estudantes e expansão a escolas externas.** Supabase Auth + OAuth Google Workspace/Gmail pessoal (D-011), identificação/verificação de menores, `schools`/`school_memberships`/turmas, autorização RLS tenant-aware, convites, suspensão, auditoria e aprovação institucional. O fato de o app estar demonstrado não habilita automaticamente esse marco.

## Caminho crítico reordenado para Marco A

1. **Integração e consistência Git.** Preservar PRs #23/#24/#26, conciliar decisões vigentes da main, sem força/merge de código inseguro nem retrabalho em ID-011.
2. **I3-03 primeiro: fechar recorte operacional para a demonstração.** PG-01..06 (núcleo PostgreSQL) e AD-01..06 (admissão RoboDSL) passaram em CI, mas **I3-03 INTEGRAL continua EM EXECUÇÃO**. O recorte I3-03C ainda precisa de API/broker cloud, identidade de serviço e worker outbound autenticado, claims/leases/fencing e testes TLS/roles/compatibilidade do Supabase. Planejar contrato e testes antes do código. Quando aceites de Auth/RLS estudantil continuarem adiados ao piloto, não declarar I3-03 integral fechado.
3. **I3-04 depois do recorte I3-03C.** Resultado oficial do árbitro, ledger e replay com commit transacional e efeito único; rejeitar tentativas obsoletas, canceladas, duplicadas e falhas de gravação. Planejar antes do código.
4. **I3-05/I3-06/I3-07.** Quotas, rate limiting, suspensão, falhas/restart, recuperação e integração de ponta a ponta no ambiente de testes.
5. **I4.** Testar VM Linux independente e isolada do computador pessoal, mediante autorização específica.
6. **HYB/S08.** Integrar PWA Vercel, Supabase PostgreSQL/Storage, autoria RoboDSL, solicitações, placar e replay, com acesso DEMO restrito.
7. **I5.** Ensaiar falhas/recuperação, backup/restauração, limites gratuitos e teste no celular; decisão separada de G-DEMO. G-PROD de alunos permanece bloqueado.

**Não são bloqueadores para iniciar o Marco A**: ID-011 (`schools`, `school_memberships`, convite/autorização multiescola), ID-001..009 OAuth real de aluno, login Workspace/SUAP, perfis/admin da escola externa e abertura de torneio público. Isso **não autoriza deixar API pública sem autenticação**: implementar um mecanismo restrito **do ambiente de demonstração**, separado e testado, com negação a usuários reais e controles de segredo/abuso. Se a arquitetura escolhida vier a usar Google no Marco A, a integração terá de ser planejada/testada, não simulada como real.

## Critérios de fechamento

A demonstração poderá aprovar **um recorte I3-03C** com atores sintéticos e acesso controlado, mas isso **não encerra o I3-03 integral**. O incremento completo permanece EM EXECUÇÃO até satisfazer todos os seus critérios, inclusive os de autenticação/autorizações de estudantes que forem planejados para o piloto. Não reclassificar evidências históricas nem transformar G-DEMO em G-PROD.

## Critérios de go/no-go da demonstração

- [ ] Jornada real editável no celular, com RoboDSL básica e falhas visíveis sem travar interface.
- [ ] Persistência remota e fila durável com identidade DEMO confiável e quotas; ação só em versão admitida.
- [ ] Batalha real isolada, timeout/cleanup, sem permitir linguagem geral/código hostil ou acesso ao host.
- [ ] Resultado vinculado a job/attempt/fence e efeito único do placar; replay íntegro com autorização.
- [ ] Queda de VM/worker e retorno recuperam fila sem dupla pontuação nem acesso a dados do PC.
- [ ] Backup/restauração, limites gratuitos, privacidade e ensaio real repetível demonstrados.
- [ ] Avaliação G-DEMO documentada, com riscos residuais; sem declarar G-PROD/piloto liberado.

## Regra de planejamento e documentação

Antes de cada incremento novo publicar plano Spec Kit, contratos, tarefas e testes/gates; ao terminar sincronizar `ESTADO-ATUAL`, planos, relatórios, manifestos de evidência e PR. Se ocorrer necessidade não planejada, registrar adendo antes do código. Não marcar ID-011 concluída; registrar **ADIADA PARA MARCO B** e preservar sua especificação para evitar replanejamento quando chegar a fase de estudantes.

**Sem operação nesta decisão:** não implantou cloud, executou bot, usou alunos, modificou VM/host, liberou rede/credencial, alterou firewall ou homologou produção. [Plano detalhado do Marco A](../../../specs/004-isolamento-execucao/demo-diretoria-mvp.md).