# Feature 001 / Extensão planejada — MVP híbrido Vercel + Supabase + VMs locais

**Data:** 2026-10-10 · **Status:** ESPECIFICADO/PLANEJADO; nenhuma tarefa de implantação ou migração concluída.
**Decisões:** [D-006](../../docs/planejamento/decisoes/D-006-hospedagem-hibrida-e-persistencia-remota.md) e [ADR-005](../../docs/arquitetura/ADR-005-hospedagem-hibrida-mvp.md).
**Base anterior:** a feature 001 original comprova Compose local de Postgres + sonda; seu histórico/aceites não são reescritos. Esta extensão é sobre o **MVP futuro**.
**Gates:** S00-T06, S03-T06, S04-T01/T05, S04-T04/I3-I4-I5, S08 e G-PROD seguem abertos/bloqueados.

## Histórias e critérios de aceite verificáveis

**US-H1 — Persistência remota:** como estudante, quero salvar minha estratégia, retornar por outro dispositivo e manter a versão íntegra, mesmo que o PC do executor esteja desligado. Aceite: PostgreSQL no Supabase como registro canônico; versão imutável por hash; CRUD autenticado e RLS que impeça ver dados de outro estudante; repetir upload de versão não duplica histórico.

**US-H2 — Treino assíncrono:** como participante, quero pedir treino mesmo que o PC da arena esteja temporariamente offline, com status verdadeiro. Aceite: job persiste no PostgreSQL; worker somente recebe comandos por identidade autorizada, pull/outbound; indisponibilidade deixa QUEUED ou status seguro; leases/fencing fazem retry controlado sem duplicate score.

**US-H3 — Replays remotos:** como organizador, quero replays e evidências permanentes disponíveis para usuários autorizados. Aceite: Storage privado, upload validado com hash e tamanho, URL temporária de leitura, metadados e auditoria no Postgres; teste de expiração de URL, tampering, quota e correlação com job/attempt.

**US-H4 — Computação residencial isolada:** como mantenedor, quero executar só o cálculo em VM Linux separada, sem expor Docker, banco, LAN ou arquivos pessoais a estudantes. Aceite: VM dedicada sem drives pessoais, credenciais escopadas, conexões iniciadas de saída, política efetiva inspecionada, sem fallback para host; power-off/reconnect comprovados. Depende de autorização separada do operador em I4.

**US-H5 — Recuperação e custos:** como operador, preciso recuperar resultados e dados remotos sem depender de um único computador nem exceder orçamento inesperadamente. Aceite: backup/restauração do banco e buckets verificados, TTL/sanitização/spool local mínimos, controle de quota e revisão de condições Vercel/Supabase, plano de contingência para VM offline. Não presumir Free como nível de disponibilidade de evento público.

## Plano de implementação — antes de qualquer código ou deploy

- [ ] **HYB-01** [US-H1] Especificar esquema PostgreSQL canônico: perfis/papéis, robôs, versões imutáveis, jobs, tentativas, leases, eventos, scores, manifestações de evidência e objetos Storage; contratos de IDs/índices e autorizações por recurso. Entrega: proposta de migrations versionadas e testes; sem conexão a projeto real.
- [ ] **HYB-02** [US-H1] Desenvolver migrações e testes PostgreSQL isolados no CI para RLS de usuário, role de serviço mínima, queries de transição e rollback; casos negativos entre participantes e Admin; não usar PostgreSQL pessoal como homologação.
- [ ] **HYB-03** [US-H2] Reconciliar **I3-03**: substituir/adaptar SQLite experimental por repositório PostgreSQL para fila real, usando reserva transacional, SKIP LOCKED ou técnica equivalente verificada, fencing token e clock/lease; testes para concorrência, crash antes/depois de COMMIT, reentrega e ausência de dupla pontuação.
- [ ] **HYB-04** [US-H2] Definir onde operar broker/API que conectam cloud ao worker; avaliar limites de Vercel Functions e disponibilidade para mTLS, autenticação e rate limiting. Não assumir que o probe TLS de CI funciona no runtime cloud. Só depois implementar conexão de saída autenticada da VM.
- [ ] **HYB-05** [US-H3] Criar buckets privados e políticas de objetos, assinatura de URLs curtas e validação de replay/manifesto, sem enviar credencial administrativa à VM ou navegador.
- [ ] **HYB-06** [US-H4] Planejar e testar VM Linux dedicada no PC com hipervisor/disco próprios, isolamento de rede e ausência de mounts pessoais. Procedimento de host e autorização explícitos são pré-requisitos: não executar automaticamente.
- [ ] **HYB-07** [US-H2/US-H4] Ensaio PC offline/internet indisponível: persistência da fila e edição web intactas; sem executar novas partidas; lease vencido/recovery/idempotência e reapresentação de artefatos após religar.
- [ ] **HYB-08** [US-H5] Preparar backup independente e restaurar Postgres + Storage em laboratório; política de retenção, consentimento para menores e auditoria de acesso; não expor dados de alunos em logs.
- [ ] **HYB-09** [US-H5] Adotar **Vercel Hobby como primeira opção de PWA**, com enquadramento não comercial favorável segundo declaração D-009 de desenvolvimento voluntário sem remuneração pelo projeto, confrontada com Terms §4/Fair Use e resposta pública de Vercel Staff. **Sem exigir carta individual como gate genérico**. Antes de deploy oficial, conferir tipo/titularidade da conta, colaboração Git, quotas/limites, retenção, quem pode aceitar os Terms se a conta for institucional e ausência de PII/segredos nos builds; registrar opt-out de Model Training. Cloudflare Pages continua fallback para frontend apenas. Validar limites Supabase Free/Storage/egress e contingência. HYB-09 só se encerra após essas provas operacionais.
- [ ] **HYB-10** [US-H1..US-H5] Revisão arquitetural independente e aceite de integração/homologação G-PROD após I3/I4/I5, especificação de S03 e participação/backup/segurança comprovadas.

## Regras obrigatórias para execução do plano

A **fonte de verdade do MVP** será PostgreSQL cloud; Storage cloud para binários. O SQLite do I3-01 só é fixture. A persistência local permitida é a do sistema VM e staging efêmero/limitado do worker, apagado após confirmação de commit remoto. Não guardar banco mestre/replay definitivo no host nem credenciais de alto privilégio na VM de execução. Se falhar a nuvem, nenhuma pontuação deve ser confirmada prematuramente.

A PWA pode estar disponível sem a VM, mas a arena não executa partidas com worker offline. Frontend nunca executa código submetido nem chama Docker. Conexão da arena deve iniciar outbound com identidade verificada; **não abrir porta no roteador** pelo simples aceite do desenho.

**Ordem no repositório:** publicar ADR e Spec Kit → revisar I3-03 antes do código → testar Postgres/RLS/leases no CI → planejar broker cloud/worker outbound → I4 host autorizado → I5 operações/backup/revisão. Adicionar lacunas ao Spec Kit ANTES do patch. Nenhuma caixa HYB marcada como concluída por haver apenas uma decisão ou documento.

## Fontes externas e restrições revisadas em 2026-10-10

[Supabase connection pooling](https://supabase.com/docs/guides/database/connecting-to-postgres); [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security); [Storage privado](https://supabase.com/docs/guides/storage/buckets/fundamentals); [Supabase Free pausing](https://supabase.com/docs/guides/platform/free-project-pausing); [Vercel Hobby](https://vercel.com/docs/plans/hobby); [Vercel WebSocket beta](https://vercel.com/changelog/websocket-support-is-now-in-public-beta).


## Esclarecimento D-008 — frontend preferido, sem alterar os gates (2026-10-10)

**PWA:** Vercel é primeira preferência, **Hobby sujeito à conformidade contratual**; Cloudflare Pages é fallback sem trocar Supabase/PostgreSQL/Storage ou a VM. O [registro D-008](../../docs/planejamento/decisoes/D-008-revisao-hobby-vercel-ifma.md) e [ADR-005](../../docs/arquitetura/ADR-005-hospedagem-hibrida-mvp.md) se baseiam em fontes oficiais, não em pressuposto de que ser instituição pública/sem fins lucrativos basta.

A construção deve continuar portável (build estático React/PWA, nenhuma lógica crítica dependente de runtime Vercel); o serviço de controle do worker continua **fora** da hospedagem estática. **HYB-09 permanece [ ]** porque a conta real, quotas, colaboração, privacidade e deploy ainda não foram verificados, **não** por remuneração do projeto (declarada inexistente); S00/S03, I3/I4/I5 e G-PROD não são ratificados por esta revisão.

**HYB-09 / privacidade Vercel:** auditar a opção de treinamento de IA sobre conteúdo enviado no Hobby ([Terms §3](https://vercel.com/legal/terms)), documentar opt-out em Team Settings quando aplicável e assegurar que apenas artefatos estáticos sem PII/chaves sejam implantados. O login e as estratégias dos estudantes permanecem no Supabase com acesso autorizado. Tarefa HYB-09 não se encerra por esta nota.

**Esclarecimento D-009 (2026-10-10):** o desenvolvimento da RoboCopa é voluntário e sem remuneração associada, segundo declaração expressa do responsável; isso torna favorável o enquadramento no Hobby pela leitura dos [Terms §4](https://vercel.com/legal/terms), [Fair Use](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage) e [resposta de Vercel Staff](https://community.vercel.com/t/question-about-commercial-usage/23321/4) sobre caso semelhante. Não impor carta individual como obrigação genérica; reavaliar se houver mudança de finalidade/remuneração ou posição contrária da Vercel. A decisão não marca outros gates como concluídos. [D-009](../../docs/planejamento/decisoes/D-009-carater-voluntario-vercel-hobby.md).

## Dependência de identidade acadêmica — D-010 (2026-10-10)

Acesso dos estudantes ao MVP: **Google OAuth via Supabase Auth com a conta acadêmica Google administrada pelo IFMA**, não Gmail pessoal, sem senha RoboCopa. O domínio `acad.ifma.edu.br` é **candidato** e será verificado no Workspace/SUAP antes do deploy; OIDC `hd` assinado é necessário para afirmar pertença ao domínio, enquanto a vinculação turma/campus/competição deve ser autorizada em tabelas/RLS, nunca inferida do email. A [feature 005](../005-identidade-academica/spec.md) descreve ID-001..009 e testes, inclusive autorização Google para apps terceiros usados por menores de idade. HYB-01/02 devem incorporar essa identidade e autorização. **Nenhuma tarefa HYB foi concluída por esta decisão**.
