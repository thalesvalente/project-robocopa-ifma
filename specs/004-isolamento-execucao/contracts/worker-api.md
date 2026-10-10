# Contrato I3-03C — comandos autenticados do worker (DEMO)

**Plano pré-código:** [CW-01..06](../i3-03c-worker-api-plan.md). **Estado:** PLANEJADO. O endpoint é somente serviço de worker, não API de aluno/browser. Exposição cloud ainda não aprovada.

## Requisição

`POST /worker-control` (harness CI) ou `/functions/v1/worker-control` (alvo configurado), HTTPS, `Authorization: Bearer rcw_<64 hex minúsculos aleatórios>`, `Content-Type: application/json`, sem query/Origin/cookie. Máximo 2048 bytes e 2 segundos para corpo. Um objeto plano, chaves únicas, sem nesting arbitrário:

```json
{"schema_version":1,"request_id":"UUID-v4","operation":"claim"}
```

`start` e `heartbeat`: acrescentar `job_id`, `attempt_id` UUIDs, `fence` string decimal positiva (evitar arredondamento de bigint em JavaScript). `fail`: mesmos campos e `reason` em `WORKER_STOPPED/ENGINE_FAILURE/RESOURCE_LIMIT`. Qualquer `worker_id`, `owner_id`, `scope_id`, token/banco em corpo ou operação fora da lista falha. A identidade e escopo vêm da credencial ativa no banco.

Credenciais 256bit opacas, emitidas somente por componente administrativo confiável, TTL<=900s; banco guarda SHA-256 sobre o token completo, não token. API conhece apenas papel DB `rc_worker_api` que executa `rc_control.worker_command(text,uuid,text,jsonb)`. Tokens de worker não são tokens Google, de aluno ou Supabase privilegiados.

## Transação e resposta

Autenticação/estado/escopo + idempotência + operação + recibo ocorrem numa transação. Resposta de sucesso somente após commit:

```json
{"schema_version":1,"request_id":"UUID","operation":"claim","scope_id":"lab-a","worker_id":"UUID","result":null}
```

`result=null` significa nenhuma tarefa disponível, não erro; nova consulta usa novo request_id e respeita intervalo. Reserva contém `job_id/attempt_id/fence` (fence string), `lease_until/deadline_at/descriptor` (hashes e referência imutável, sem fonte/PII). `start/heartbeat` retornam `state/fence/lease_until`; `fail` retorna `state`. Sem resultado COMPLETED/placar ou replay neste contrato.

Mesma request_id/op/args devolve recibo válido sem executar novamente; mesmo ID diferente conteúdo => conflito. Autenticação é refeita antes de recibo. Se lease/deadline/tentativa/worker não estiver vigente, replay falha em vez de devolver autorização antiga. Worker mantém no máximo uma lease ativa e só segue processamento se serviço confirmar estado. Recolher expirados continua API administrativa separada; não expor reap global a worker.

Erros sanitizados: 401 credencial negada; 400 estrutura; 403 requisição proibida; 409 conflito/lease antiga/worker ocupado; 429 intervalo; 503 gate/storage; nunca stack SQL, token, DSN, payload ou path. Sem cache, sem redirects, sem CORS. Falha de transporte/commit => resultado desconhecido, reconsultar o mesmo ID, não executar robô por suposição.

## Testes e gates

Doubles de Fetch/DB para unidade; prova real Deno HTTPS + Postgres separado com CA/contas/segredos efêmeros em CI; testes adversos de replay/cross-worker/expiry/TLS/commit e limpeza. Nenhum resultado CI equivale a Supabase gateway/TLS/pooler implantados. Não integra supervisor de bot nem dados de alunos nesta fase.
