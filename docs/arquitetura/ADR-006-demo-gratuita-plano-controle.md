# ADR-006 — Baseline da demonstração gratuita e plano de controle PostgreSQL

**Data:** 2026-10-10. **Estado:** direção aprovada em D-007; implementação/implantação não homologadas. Complementa ADR-005 sem alterar seus resultados históricos.

## Arquitetura e trade-offs

PWA estática portável React/TypeScript -> Cloudflare Pages (preferência Free) -> Supabase Auth/API curta -> PostgreSQL canônico + Storage privado. VM dedicada no PC inicia HTTPS de saída ao serviço autorizado; navegador e banco não expõem a máquina residencial. O banco guarda jobs, tentativas e leases; a VM guarda apenas sistema e staging limitado. Não há fallback SQLite nem banco mestre local.

Cloudflare Pages substitui a dependência exclusiva de Vercel Hobby; a documentação atual limita o Hobby a uso pessoal/não comercial. Conferir termos/conta institucional antes de deploy. Pages Free tem 500 builds mensais documentados; isso não promete SLA. Edge Functions Free documenta 500.000 invocações e limites de 150 s de duração, 2 s CPU e 256 MB: usar chamadas curtas, não hospedar batalhas. Polling com backoff é requisito, não um laço permanente de invocações. Supabase Free e SMTP padrão não são garantia de operação de turma: preparar contas sintéticas antes da demonstração; cadastro institucional, recuperação, email e consentimentos permanecem no marco do piloto.

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
