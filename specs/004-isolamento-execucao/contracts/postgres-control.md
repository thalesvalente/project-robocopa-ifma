# Contrato I3-03 — funções PostgreSQL privadas

**Data:** 2026-10-10. **Estado:** especificação anterior à migration; segue [plano](../i3-03-postgres-plan.md). Não é endpoint, autenticação HTTP, autorização de aluno ou conexão Supabase já instalada.

## Privilégios

`rc_control_owner`: NOLOGIN, sem SUPERUSER/BYPASSRLS/CREATEROLE. Schema `rc_control` privado, tabelas com RLS forçada e somente política do owner. `rc_broker`: NOLOGIN, sem DML de tabelas, sem habilitar gate, somente EXECUTE das funções públicas deste contrato. PUBLIC/anon/authenticated/worker sem privilégios. A função interna lock_lease não pode ser executada pelo broker. SECURITY DEFINER exige search_path=pg_catalog e nomes de relações qualificados.

O futuro serviço cloud autentica o usuário/worker, deriva suas referências e chama SQL com permissão específica. Nenhum papel/chave administrativa/connection string será enviado à VM de bots. Os parâmetros owner/worker deste contrato não são prova de identidade e não podem vir diretamente do navegador.

## Operações

- `enqueue(owner UUID, scope TEXT, key TEXT, descriptor JSONB, deadline TIMESTAMPTZ)`: gate ligado pelo operador confiável, descriptor já aprovado pela admissão I1, retorna job_id/state/duplicate. Chave única por owner; igualdade de scope/descriptor/deadline significa duplicata sem novo efeito, divergência gera IDEMPOTENCY_CONFLICT. Limite de capacidade global com lock transacional. Banco gera job_id.
- `claim(worker UUID)`: worker ativo e escopo registrado, gate ligado, reserva elegível por FOR UPDATE SKIP LOCKED e retorna job_id/attempt_id/fence/lease_until/deadline/descriptor. Retorno NULL indica fila sem trabalho elegível. A reserva SQL não inicia robô.
- `heartbeat(worker,job,attempt,fence,start BOOLEAN=false)`: rejeita worker revogado, geração/attempt errados, prazo de lease/deadline vencido. start=true indica RUNNING; heartbeat nunca prolonga além do deadline nem altera fencing.
- `fail_attempt(worker,job,attempt,fence,reason)`: apenas WORKER_STOPPED, ENGINE_FAILURE ou RESOURCE_LIMIT, invalida tentativa atual e reencaminha com backoff mínimo de um segundo dentro de deadline/limite; não publica resultados.
- `cancel(job,owner)`: dono validado pelo serviço, idempotente para estados terminais, invalida fencing e não permite nova reserva; sem acesso entre donos.
- `reap()`: recolhe no máximo 256 trabalhos por chamada; lease/deadline vencidos ou worker revogado finalizam a tentativa e liberam ou terminalizam o job. Pode executar com novas admissões suspensas.

Descriptor exato: version_id (identificador até 64), source_sha256/program_sha256/java_sha256/policy_sha256 (64 hex minúsculos), engine_ref=tank-royale/1.4.0, rounds inteiro 1..3. Sem fonte, comando, caminho, segredo, owner_ref ou flags de Docker. O SQL recebe JSONB interno já validado; não substitui o parser bruto do I1 que recusa chaves duplicadas.

## Semântica de falhas

Relógio do PostgreSQL; deadline de inserção até 240s; lease configurável 1..60s; até três tentativas, parâmetros experimentais e não quotas do produto. SQL faz commit/rollback indivisível; serviço não deve responder sucesso antes do commit. Reserva expirada é invalida mesmo antes de reap. Após reap/novo claim a geração aumenta, impedindo atualização tardia pela tentativa antiga. Isso não termina fisicamente um processo antigo na VM: watchdog/reconciliação operacional continuam necessários.

Não há COMPLETED, placar ou API de publicação nesta migration. I3-04 deverá validar resultado e commit de efeito único com os vínculos job/attempt/fence. PG-01..06 são núcleo de persistência do I3-03, não a integração cloud↔VM nem I3 integral.
