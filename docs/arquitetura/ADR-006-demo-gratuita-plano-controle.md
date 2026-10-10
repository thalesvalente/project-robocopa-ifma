# ADR-006 — Baseline da demonstração gratuita e plano de controle PostgreSQL

**Data:** 2026-10-10. **Estado:** direção aprovada em D-007; implementação/implantação não homologadas. Complementa ADR-005 sem alterar seus resultados históricos.

## Arquitetura e trade-offs

PWA estática portável React/TypeScript -> **Vercel (primeira opção, Hobby sujeito à elegibilidade conforme D-008; Cloudflare Pages como alternativa)** -> Supabase Auth/API curta -> PostgreSQL canônico + Storage privado. VM dedicada no PC inicia HTTPS de saída ao serviço autorizado; navegador e banco não expõem a máquina residencial. O banco guarda jobs, tentativas e leases; a VM guarda apenas sistema e staging limitado. Não há fallback SQLite nem banco mestre local.

**A revisão D-008 substitui a preferência inicial por Cloudflare**: Vercel é preferida para hospedagem da PWA, mas o uso Hobby depende da elegibilidade contratual; **Cloudflare Pages é fallback, não hospedagem obrigatória**. Os [Terms §4](https://vercel.com/legal/terms) incluem uso pessoal ou não comercial, enquanto as [Fair Use Guidelines](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage) tratam de ganho financeiro de pessoas envolvidas na produção, inclusive empregados pagos/consultores. O [caso de voluntários em organização sem fins lucrativos respondido pela equipe da Vercel](https://community.vercel.com/t/question-about-commercial-usage/23321/4) não constitui autorização individual para projeto de servidor público. Conferir enquadramento antes de publicação oficial, como HYB-09. Cloudflare Pages Free segue opção conhecida de 500 builds mensais; nenhum provedor gratuito oferece SLA institucional por mera escolha. Frontend deve continuar portátil. Edge Functions Free documenta 500.000 invocações e limites de 150 s de duração, 2 s CPU e 256 MB: usar chamadas curtas, não hospedar batalhas. Polling com backoff é requisito, não um laço permanente de invocações. Supabase Free e SMTP padrão não são garantia de operação de turma: preparar contas sintéticas antes da demonstração; cadastro institucional, recuperação, email e consentimentos permanecem no marco do piloto.

## pgmq versus tabela de jobs

Avaliado Supabase Queues/pgmq: extensão PostgreSQL útil, persistente e com visibilidade temporária. A garantia publicada de entrega única é limitada à janela de visibilidade. Não substitui fencing, correlação com versão/política, autorização de worker, nem commit idempotente do resultado.

**Decisão I3-03:** uma única tabela de jobs com tentativas associadas e reserva por SELECT FOR UPDATE SKIP LOCKED. Ela já é necessária para representar deadline, worker, geração/fencing, cancelamento e estado. Evitar neste MVP sincronizar uma mensagem pgmq com outro estado de job. Trade-off: manter e testar as poucas transições SQL próprias; reconsiderar pgmq se fan-out, vazão ou operação justificarem. Isto não desqualifica pgmq nem afirma que execute exatamente uma vez a computação física.

## Separação de privilégios

Schema privado `rc_control`, fora de `public`/Data API. Tabelas sem grants de cliente, RLS deny-by-default; owner NOLOGIN mínimo. Funções SECURITY DEFINER com search_path fixo e SQL qualificado, EXECUTE revogado de PUBLIC, liberado somente ao papel interno `rc_broker`. Identidade de owner/worker é derivada pelo broker autenticado futuro, não por JSON de usuário. O papel do broker não é credencial de worker, não será entregue à VM e não deve estar acessível pelo PostgREST.

No recorte inicial, enfileirar exige gate OFF por padrão, descriptor admitido e escopo/worker habilitado. Reservar cria attempt UUID e fencing crescente. Start, heartbeat e falha exigem worker+job+attempt+fence atuais e lease válida; deadline vem do relógio do PostgreSQL. Cancelamento/expiração invalidam a geração anterior. I3-04, ainda pendente, deverá exigir esses mesmos vínculos antes de efetivar placar e artefatos.

## Marco A / Marco B

Demonstração privada: contas e estratégias conhecidas, salvamento remoto, uma partida real com resultado validado/replay, indicador de worker offline, reentrega sem duplicidade e restauração ensaiada. Não pronta só por CI verde.

Piloto estudantil: RLS por dono e papéis, login/recuperação/email, consentimentos e retenção, VM-alvo com isolamento/quotas comprovados, resultados idempotentes, backup de banco **e objetos**, rate-limit e aceite institucional. Recursos avançados e transmissão ao vivo ficam depois.

## Fontes primárias verificadas em 2026-10-10

- PostgreSQL: https://www.postgresql.org/docs/current/sql-select.html — SKIP LOCKED para consumidores de tabela semelhante a fila.
- Supabase pgmq: https://supabase.com/docs/guides/queues/pgmq — visibilidade/entrega e persistência.
- Supabase privilégios/RLS: https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase funções: https://supabase.com/docs/guides/database/functions — privilégios EXECUTE e search_path em SECURITY DEFINER.
- Edge limites/preços: https://supabase.com/docs/guides/functions/limits e https://supabase.com/docs/guides/functions/pricing
- Vercel: https://vercel.com/docs/plans/hobby
- Cloudflare: https://developers.cloudflare.com/pages/platform/limits/
- Email: https://supabase.com/docs/guides/auth/auth-smtp
- Planos Supabase: https://supabase.com/pricing

Valores são condições consultadas, não reserva de cota/SLA nem autorização de custo. Nenhum serviço cloud foi criado por esta ADR.

## Precedência posterior de hospedagem — D-008 (2026-10-10)

**Decisão revisada:** Vercel Hobby é **candidata prioritária ao frontend estático**, não isenção contratual obtida; Cloudflare Pages é contingência se for inelegível/inadequada. Isso modifica somente a preferência descrita na primeira edição da D-007/ADR-006, nunca PostgreSQL, pgmq, roles, worker, leases, segurança ou marcos.

**Gates (esclarecidos pela D-009):** o responsável declarou desenvolvimento voluntário e sem remuneração associada, portanto a elegibilidade Hobby é favorável em princípio e **carta individual da Vercel não é condição obrigatória genérica**. HYB-09 permanece aberto para conferir titularidade/representação institucional, colaboração e limites, e avaliar [Model Training no Hobby](https://vercel.com/legal/terms) com opt-out disponível em Team Settings. Não pôr PII, código privado de estudantes ou segredos no build. Nenhum deploy/conta foi criado por esta revisão. Ver [D-008](../planejamento/decisoes/D-008-revisao-hobby-vercel-ifma.md).

## D-009 — fato novo e interpretação favorável ao Hobby

O responsável declarou expressamente **projeto voluntário, sem remuneração vinculada**. A restrição hipotética de desenvolvimento pago não se aplica aos fatos informados, que correspondem ao caso considerado adequado por [Vercel Staff](https://community.vercel.com/t/question-about-commercial-usage/23321/4). O Hobby é primeira opção com enquadramento **favorável em princípio**, sem exigir resposta individual como gate automático. Cloudflare segue alternativa. Permanecem as verificações de conta, limites, autoridade administrativa quando necessária e opt-out de treinamento. A alteração não afeta fila PostgreSQL, motor/VM ou provas do I3. [D-009](../planejamento/decisoes/D-009-carater-voluntario-vercel-hobby.md).
