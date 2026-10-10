# I3-03B — Contrato interno de admissão e persistência

**Data:** 2026-10-10. **Estado:** especificado antes do código. [Plano AD-01..06](../i3-03-admission-plan.md). Este contrato NÃO é rota pública nem prova de autenticação.

## Entradas e identidades

`AdmissionService.submit(raw: bytes, source: str, actor: ServiceActor)` recebe JSON de até 1024 bytes: `{"schema_version":1,"version_id":"demo-v1","idempotency_key":"request-1","rounds":3}`. Rejeitar extras, duplicatas, bool em campos numéricos, NaN, UTF-8 inválido e identificadores fora do contrato. Fonte permanece limitada pelo compilador básico já existente.

`ServiceActor(owner_id: UUID canônico, scope_id: str)` é criado exclusivamente pelo chamador de serviço confiável depois de autenticação/autorização (ainda não implementadas nesta entrega). Não aceitar owner, scope, role, worker, job/attempt, gate ou deadline dentro do JSON. A presença do dataclass não autentica ninguém. Nenhuma função desta entrega é exposta via HTTP.

## Dados de controle e transações

`approved_versions(owner_id, scope_id, version_id)` guarda source_sha256/program_sha256/java_sha256, active=false por padrão e revision. Não guarda fonte, email, nome ou segredo. Identidade/hashes são imutáveis por trigger; alteração de active incrementa revision. Sem API de registro: o teste cadastra fixture administrativa, e a aplicação futura deverá popular uma projeção autorizada de versões imutáveis.

`admission_snapshot(owner, scope, version)` retorna hashes, revisão e política ativa, ou VERSION_UNAUTHORIZED (sem diferenciar alheia, inexistente e revogada). O gate desligado não fornece snapshot. Privilégios EXECUTE apenas ao novo papel NOLOGIN rc_admission.

O serviço passa a fonte e hashes ao admit do I1. IDs temporários internos usados somente para satisfazer o envelope legado são descartados; não são job/attempt persistidos. Confere ainda o java_sha256 compilado contra o catálogo. Nenhuma invocação de motor/Docker.

`enqueue_admitted(owner, scope, key, descriptor, revision)` obtém lock settings -> versão, valida novamente active/revision/owner/escopo/hashes/política, usa enqueue interno existente e retorna job_id/state/duplicate. Na primeira gravação, deadline de execução vem do relógio do banco; em retry idêntico, o prazo original é mantido, não prolongado. Repetição após revogação de versão/política pode ser recusada deliberadamente. Revogar EXECUTE do enqueue bruto de rc_broker e deixar a chamada interna ao owner; preservar demais funções de PG-01..06. Não acrescentar conclusão de partida/score.

O runtime abre transações curtas, parametriza valores separadamente e confirma commit antes de responder. Snapshot e compilação não mantêm uma transação longa; o segundo exame da versão evita confiar em autorização desatualizada. Falha de commit é STORAGE_UNAVAILABLE com resultado possivelmente desconhecido, nunca sucesso antecipado; o chamador deverá reconciliar com a mesma chave. Nenhum retry automático com nova chave.

## Banco/driver e fronteiras

O adaptador recebe factory de conexão confiável, nunca DSN do payload, aplica timeouts locais e prepare_threshold=None, não recebe privilégio de registrar versões ou alterar settings. Psycopg é dependência somente do adaptador/CI, não do parser I1. Driver real testado com login sintético restrito; SET ROLE de fixture não será chamado de autenticação de usuário. Produção depende de conexão TLS/pooler do provedor e API que valide identidades; isso permanece pendente.

Erros são códigos enumerados sanitizados; não divulgar SQL, source, DSN, path, parâmetros ou mensagens de driver. SQLSTATE apenas interno se necessário. RLS impede acesso direto inclusive após SELECT indevido acrescentado na fixture. Não confundir schema privado de controle com RLS da futura aplicação de estudantes.

## Casos de aceite

Fluxo real compilador I1 -> Psycopg -> Postgres -> fila/claim/start; identidade de usuário separada; versão alheia/escopo/revogação/Java adulterado; concorrência e idempotência; rechecagem após mudança entre snapshot e gravação; gate desligado; privilégio mínimo; tentativa de SQL injection com parâmetros; erro de commit/rollback sem sucesso; migration reaplicada falha sem perda; ausência de campo fonte na persistência. Catálogo e driver não fecham I3-03 integral ou G-PROD.
