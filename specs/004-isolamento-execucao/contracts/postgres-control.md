# Contrato I3-03 — funções PostgreSQL privadas

**Data:** 2026-10-10. **Baseline original:** especificada antes da migration 001; [plano PG-01..06](../i3-03-postgres-plan.md). **Atualização I3-03B:** após migration 002, a entrada de admissão e os privilégios foram separados; [contrato da ponte](admission-postgres.md). Não é endpoint, autenticação HTTP, autorização de aluno ou Supabase implantado.

## Privilégios e versões do contrato

`rc_control_owner`: NOLOGIN, sem SUPERUSER/BYPASSRLS/CREATEROLE. Schema privado, RLS forçada e política só do owner. SECURITY DEFINER com search_path=pg_catalog e nomes qualificados; funções internas não são disponibilizadas ao cliente.

**Somente migration 001:** `rc_broker` recebia EXECUTE em enqueue/claim/heartbeat/fail_attempt/cancel/reap, sem tabelas ou alteração de gate. As 30 provas históricas PG-01..06 referem-se a esse estado.

**Migrations 001 + 002:** `rc_admission` recebe somente `admission_snapshot` e `enqueue_admitted`; `rc_broker` perde EXECUTE em enqueue bruto e conserva operações de execução. Apenas o owner interno chama enqueue por dentro da função admitida. Não orientar clientes novos a usar o contrato legado direto. A função `lock_lease`, o catálogo de versões e as tabelas permanecem privados. PUBLIC/anon/authenticated/worker não recebem permissões.

O futuro serviço cloud autentica usuário/worker e deriva referências; os parâmetros owner/worker não são prova de identidade e não devem vir diretamente do navegador. Nenhum papel/chave administrativa/DSN vai à VM de bots. A fixture de LOGIN SCRAM demonstra privilégio de banco, não JWT/HTTPS.

## Entrada vigente de admissão, após 002

- `admission_snapshot(owner UUID, scope TEXT, version TEXT)`: gate ON, versão ativa pertencente ao owner/escopo; retorna hashes, revisão e política. Alheia, inexistente ou revogada produzem VERSION_UNAUTHORIZED.
- `enqueue_admitted(owner UUID, scope TEXT, key TEXT, descriptor JSONB, revision BIGINT)`: lock settings -> versão, reconfere revisão ativa/hashes/política e chama enqueue interno. Deadline inicial do banco, duplicata idêntica preserva o original. Compilação ocorre fora da transação. Reativação de versão gera nova revisão.

O catálogo privado guarda somente hashes/refs. Trigger impede mudar identidade/hashes de versão; seu cadastro é administrativo na fixture, futura projeção da API de autoria. Revogação bloqueia novas admissões, não cancela automaticamente jobs já aceitos.

## Operações de execução preservadas

- `enqueue(owner,scope,key,descriptor,deadline)`: função **interna após 002**; gate, descriptor admitido, unicidade owner/chave, capacidade atômica e retorno job_id/state/duplicate. Repetição igual de scope/descriptor/deadline é idempotente; divergência conflita. Banco gera job_id.
- `claim(worker UUID)`: worker ativo/escopo/gate, reserva por FOR UPDATE SKIP LOCKED, retorna job_id/attempt_id/fence/lease_until/deadline/descriptor; NULL se nada elegível. Reserva não inicia robô.
- `heartbeat(worker,job,attempt,fence,start BOOLEAN=false)`: nega worker revogado, geração/tentativa incorreta e lease/deadline vencido. start=true indica RUNNING; nunca prolonga além do deadline.
- `fail_attempt(worker,job,attempt,fence,reason)`: somente WORKER_STOPPED, ENGINE_FAILURE ou RESOURCE_LIMIT; invalida tentativa/reencaminha com backoff mínimo dentro do prazo/limite. Não publica resultado.
- `cancel(job,owner)`: dono validado no serviço, idempotente para terminais, invalida fencing e impede nova reserva.
- `reap()`: lote máximo256; lease/deadline vencidos ou worker revogado finalizam a tentativa e liberam/terminalizam job. Funciona com novas admissões suspensas.

Descriptor exato: version_id até64, source_sha256/program_sha256/java_sha256/policy_sha256 64hex, engine_ref=tank-royale/1.4.0, rounds inteiro1..3. Sem fonte, caminho, segredo, comando, owner_ref ou Docker flags. JSONB não substitui parser bruto que recusa duplicatas; a ponte valida antes do SQL.

## Falhas e limites

Clock PostgreSQL; prazo inicial até240s, lease1..60s, até3tentativas, configurações experimentais. Commit/rollback atômico e sucesso somente após commit. Lease vencida é inválida antes de reap; nova geração bloqueia escrita tardia. Não termina fisicamente processo antigo: watchdog/reconciliação VM ainda necessários.

Não há COMPLETED/placar. I3-04 deverá validar resultado e efeito único por job/attempt/fence. [I3-03B evidências](../../../docs/qualidade/evidencias/S04-T04-I3-03B.md): 22 casos reais após002; a suite histórica001 é separada. PG-01..06 e AD-01..06 não fecham cloud↔VM, autorização pública ou I3 integral.
