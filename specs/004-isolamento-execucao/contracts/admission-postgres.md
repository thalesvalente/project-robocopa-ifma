# I3-03B — Contrato interno de admissão e persistência

**Data:** 2026-10-10. **Especificação inicial:** commit aedbd379, antes do código. **Estado atual:** implementado/testado apenas em CI, [plano AD-01..06](../i3-03-admission-plan.md), [evidências](../../../docs/qualidade/evidencias/S04-T04-I3-03B.md). NÃO é rota pública nem prova de autenticação.

## Entradas e identidades

`AdmissionService.submit(raw: bytes, source: str, actor: ServiceActor)` recebe JSON até1024bytes: `{"schema_version":1,"version_id":"demo-v1","idempotency_key":"request-1","rounds":3}`. Rejeitar extras/duplicatas/bool numérico/NaN/UTF-8 inválido/identificadores fora do contrato. Fonte limitada pelo compilador básico existente.

`ServiceActor(owner_id: UUID canônico, scope_id: str)` só pode ser construído por chamador de serviço confiável depois de autenticação/autorização **ainda não implementadas aqui**. Nenhuma autoridade owner/scope/role/worker/job/attempt/gate/deadline vem do JSON. Dataclass não autentica. Não há listenerHTTP.

## Dados e transações

`approved_versions(owner_id,scope_id,version_id)` guarda hashes fonte/programa/Java, active=false por padrão e revision. Sem fonte/email/nome/segredo. Trigger torna identidade/hashes imutáveis e aumenta revisão a cada UPDATE. O teste cadastra fixture administrativa; API de autoria futura deve manter essa projeção autorizada.

`admission_snapshot(owner,scope,version)` devolve hashes/revisão/política quando gate e versão estão ativos. VERSION_UNAUTHORIZED não distingue alheia/inexistente/revogada. Somente rc_admission recebe EXECUTE. A compilação fica fora da transação.

O serviço reutiliza admitI1 com fonte/hashes e UUIDs temporários internos exigidos pelo envelope legado, descartados antes da gravação. Confere ainda Java gerado contra o catálogo; sem motor/Docker. PostgreSQL gera IDs de job/tentativa canônicos.

`enqueue_admitted(owner,scope,key,descriptor,revision)` trava settings -> versão, reconfere active/revision/owner/escopo/hashes/política, usa enqueue interno e devolve job_id/state/duplicate. Primeiro deadline vem do banco; retryidêntico conserva prazo original. Repetição após revogação/política pode ser recusada. Após migration002, **rc_broker perde enqueue bruto**; chamada interna pertence ao owner, entrada externa ao papel rc_admission. Outras operações PG-01..06 permanecem; não existe COMPLETED/score.

**Semântica da revogação:** bloqueia novas admissões e snapshots antigos; não implica cancelamento automático das tentativas já aceitas. Política de cancelamento em massa/ciclo de vida ainda precisa ser definida antes da operação cloud.

Adaptador parametriza valores e confirma commit antes de sucesso. Se commitfalhar, STORAGE_UNAVAILABLE pode representar resultado desconhecido; reconciliar com mesma chave, nunca retry automático comnova chave. Resposta de banco fora do contrato provoca rollback, não sucesso.

## Driver e fronteiras

Factory de conexão vem da configuração confiável do serviço, não do payload. Conexão nova semautocommit; timeouts de statement/lock/idle locais e prepare_threshold=None. `psycopg==3.3.6`/typing_extensions fixados porhash. Não garante conexãoTLS/pooler Supabase remotos, que ainda dependem de teste. AdaptadorPython não é runtimeDeno.

LoginSCRAM sintético restrito via Unixsocket testado emPostgreSQL real. Bootstrap administrativo foi separado; SETROLE de outras fixtures não é chamado de autenticação de aluno. O catálogo privado não substitui RLS da aplicação. Erros são enums sanitizados, não source/DSN/SQL/path/mensagem de driver.

## Aceite observado e pendências

Run38079697510:22 integrações reais de I1/Psycopg/PostgreSQL;25 unidades explícitas comdoubles, incluídas em407 regressões locais. Owner/escopo/revisão/revogação/Java/política, duplicação concorrente, parâmetros, roles/RLS e migrationnondestrutiva comprovados no limite. Artifact de relatório/hash/CRC auditado fora do runner; não revisão independente.

I3-03 integral continua aberto: JWT, identidade operacional, API/clientes cloud, RLS dos usuários, Supabase real e workeroutbound. Nenhuma conta, deploy, aluno, VM doresponsável, cobrança ou gateG-PROD foi habilitado.
