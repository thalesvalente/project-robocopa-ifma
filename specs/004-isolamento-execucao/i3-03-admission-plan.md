# I3-03B — Integrar a admissão RoboDSL ao núcleo PostgreSQL

**Data:** 2026-10-10. **Plano inicial:** `9824bda2e88813694dc81ba3edad1d477cf0a9fb`, publicado ANTES DO CÓDIGO. **Estado atual AD-01..06:** VALIDADO_NO_CI. **I3-03 integral:** EM_EXECUCAO. **Branch:** feat/s04-i3-03-postgres-leases, PR #26, base inicial 4575b151c253463bf6f8ecb8d3a95ac79296878e. Continuar o PR existente, sem implementação paralela ou merge automático. **Macro S04-T04:** EM_EXECUCAO; G-PROD e jornada completa da demonstração não aprovados.

## Contexto, hipóteses e Constituição

O núcleo PG-01..06 comprova transações SQL, mas recebe descriptor que pressupõe admissão prévia. O I1 valida RoboDSL. Este incremento liga ambos por driver PostgreSQL real, sem inventar autenticação de usuário/worker. D-009 mantém Vercel Hobby preferencial no contexto voluntário informado, Supabase como destino canônico e VM dedicada apenas para computação. Experimentos SQLite/mTLS anteriores permanecem preservados.

Mapeamento: FR-003/004/010/011/013/016/017/020, TH-01/05/09/14/16, T008..T016/T028/T030/T037 e HYB-01/02/03, somente seus subconjuntos experimentais. Nenhuma caixa macro/checklist de homologação fecha por este trabalho. G-EXP permite fixtures sintéticas no CI; não autoriza host pessoal, serviços pagos, dados reais, deploy ou abertura de rede.

## Decisões técnicas especificadas antes do runtime

1. Reusar `services.worker_agent.contracts.admit` e o compilador existente, sem portar a linguagem nem habilitar código geral. O contexto de ator vem SOMENTE de chamador interno confiável, separado do JSON; não é autenticação JWT. A API futura deverá autenticar e autorizar o ator antes de chamar o serviço.
2. Migration 002, sem reescrever 001: projeção privada de versões previamente aprovadas com owner/escopo/version_id, hashes de fonte/programa/Java, ativo e revisão. Sem fonte, chave ou PII no schema de controle. Registro de versões pertence à futura API de autoria; aqui a fixture administrativa registra exemplos conhecidos.
3. Papel NOLOGIN `rc_admission`: somente consulta de versão autorizada/enfileiramento admitido; sem tabelas, gate, claim, heartbeat ou privilégio de worker. Após 002, revogar de `rc_broker` a entrada direta `enqueue`; o owner interno a utiliza pela função de admissão. Broker de execução não conserva bypass de admissão.
4. Consulta inicial curta, compilação fora da transação. Antes de inserir, uma segunda transação confere owner/escopo/versão, revisão ativa e hashes, com lock settings -> versão -> job. Revogação/mudança de política durante compilação deve negar; hashes imutáveis, nova versão significa novo registro.
5. JSON restrito a schema_version/version_id/idempotency_key/rounds. Cliente não escolhe autoridade, política/hashes, job/attempt ou deadline. UUIDs internos descartáveis satisfazem o contrato I1 legado; PostgreSQL gera os IDs canônicos e prazo. Retry idêntico preserva job/deadline originais, sem fila SQLite/pgmq paralela.
6. Adaptador Python com SQL fixo e parâmetros separados, transações curtas, commit antes de sucesso, erros sanitizados e `prepare_threshold=None`. Psycopg 3 fixado por versão/hash. Nenhuma DSN padrão, credencial de produção ou destino escolhido no payload. Falha de commit tem resultado possivelmente desconhecido: reconciliação com mesma chave, nunca inserção silenciosa com nova chave.
7. Supabase Edge Functions permanece candidata para API curta. Adaptador Python NÃO roda no Deno por pressuposição; SQL é compartilhável, mas JWT, cliente Deno/HTTP, Supabase real e worker outbound são subentregas pendentes. Não contar este núcleo como deploy ou autenticação pública.

Fontes primárias: [parâmetros Psycopg](https://www.psycopg.org/psycopg3/docs/basic/params.html), [transações](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), [prepared statements](https://www.psycopg.org/psycopg3/docs/advanced/prepare.html), [pooler Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres), [funções/privilégios](https://supabase.com/docs/guides/database/functions), [Edge Auth](https://supabase.com/docs/guides/functions/auth), [PostgreSQL SECURITY DEFINER](https://www.postgresql.org/docs/17/sql-createfunction.html). SSL/pooler remotos devem ser comprovados no deploy, não presumidos por Unix socket.

## Plano executável e resultado no recorte

- [x] **AD-01** [US1/US4] Plano `9824bda` e [contrato](contracts/admission-postgres.md) `aedbd379` publicados antes de migration/runtime. Plan/tasks/índice/estado sincronizados com evidência, sem alterar 39 tarefas amplas.
- [x] **AD-02** [US1/US4] Migration 002 com catálogo/revisão, imutabilidade, lookup/enqueue mínimos e papel restrito. Provas de versão alheia, revogada, revisão antiga, RLS e bloqueio do enqueue bruto no CI 38079697510. Migration 001 preservada.
- [x] **AD-03** [US1] Serviço e adaptador DB-API/Psycopg implementados: parser estrito, contexto separado, validação I1/Java hash, gate OFF, SQL parametrizado, commit/rollback e erros sanitizados. Sem robôs/listener/DSN de requisição.
- [x] **AD-04** [US1/US3/US4] 25 testes unitários PASS com doubles explícitos. Não são contados como PostgreSQL/autenticação real. Testam parser/contexto, parâmetros, falha de commit/rollback, gate e ausência de execução.
- [x] **AD-05** [US1/US3/US4] 22 testes reais I1 -> Psycopg 3.3.6 -> PostgreSQL 17.11 no CI; concorrência, idempotência, owner/escopo, revisão/política alteradas durante compilação, privilégio mínimo e injeção parametrizada. Login SCRAM restrito por Unix socket, sem portas; somente socket/HBA temporários montados, nenhum dado pessoal.
- [x] **AD-06** [US5] Sete workflows do código `4179e5b` PASS; 407 regressões locais (incluem os 25 novos casos), artefato de admissão e hashes/CRC conferidos fora do runner. Relatório/JSON, contratos/estado e planos sincronizados. PR #26 continua draft; não há merge ou liberação macro.

## Procedimento, falhas e evidências

Workflow `i3-admission.yml`, GitHub-hosted Ubuntu descartável. Postgres fixado no digest já usado em PG-01..06, `--network none`, volume/data exclusivo, sem porta publicada. Driver com senha SCRAM aleatória; bootstrap administrativo por docker exec. Somente diretório de socket/HBA criado nesta execução é montado, nunca repositório, pasta do usuário ou socket Docker. Cleanup rotulado, com consultas bem-sucedidas antes de afirmar ausência de recursos.

O primeiro workflow foi rejeitado antes de jobs (run38079559910) por contexto runner.temp no nível jobs.env. [Plano de correção](i3-03-admission-ci-fix.md) `40714b8` precedeu patch `4179e5b`; env passou a ser calculada em step. Erro sintático de continuação do teste unitário foi corrigido em `50c358d` dentro de AD-04, sem considerar o arquivo inválido aprovado. Não houve falha observada na regra de admissão nesses eventos.

Fonte de CI: `4179e5b6a001a5ed6471caa5d9f70d1d2f5df15c`. Fonte de regressão local: `7e8f014c48b5ca6ccf1564758051298696b71a4e`; comparação Git confirmou runtime/migrations/testes idênticos, diferença somente em workflow e documento de correção. [Relatório e limites](../../docs/qualidade/evidencias/S04-T04-I3-03B.md), [manifesto](../../docs/qualidade/evidencias/S04-T04-I3-03B.json).

## Gate do recorte e próximos passos

O recorte comprova integração da admissão ao banco sob identidade interna confiável; não garante a autenticidade do chamador futuro. Versão revogada não pode ser novamente admitida; cancelamento automático de jobs já enfileirados por revogação NÃO está implementado e depende da política operacional. Compilação não segura transação longa; autoridade é reconferida no commit. Falha de armazenamento nunca retorna sucesso antecipado.

I3-03 integral permanece EM_EXECUCAO: JWT/identidade operacional, API cloud/cliente Deno se escolhido, registro de versões da aplicação, RLS de alunos, teste de roles/pooler/TLS Supabase real e worker outbound faltam. I3-04/05/06/07, I4/I5 e HYB completos seguem pendentes. Novas necessidades/falhas fora deste contrato exigem adendo ANTES do patch. Nenhum host pessoal, aluno ou serviço pago foi habilitado.
