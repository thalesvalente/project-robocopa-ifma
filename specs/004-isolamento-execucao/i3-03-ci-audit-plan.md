# I3-03 — Auditoria de CI e correções planejadas antes do patch

**Data:** 2026-10-10. Complementa [plano PG-01..06](i3-03-postgres-plan.md). Não altera os aceites de segurança, a arquitetura ou os gates de produção.

## F01 — Falha na primeira consulta SQL do harness

Run `38073651799`, fonte `b858117f74ed85c10068ca012ec1c6e054896b55`: PostgreSQL foi criado, mas a primeira consulta `SHOW server_version` em setUpClass retornou `SQL_OPERATION_FAILED`. **Zero testes executados**; não são 29 falhas funcionais nem 29 testes aprovados. A remoção do contêiner/volume owned foi confirmada pelo passo always. O stderr foi ocultado pelo sanitizador, por isso a causa específica ainda não está demonstrada.

Hipótese a testar: o `pg_isready` do socket Unix pode responder durante o servidor temporário de inicialização da imagem, antes da criação final do banco. A documentação oficial explica que pg_isready não exige banco/usuário corretos; o entrypoint da imagem inicia um servidor temporário sem TCP e só depois inicializa e reinicia o serviço. Não presumir conexão válida somente a partir dessa sonda.

**Patch planejado:** exigir prontidão TCP interna a 127.0.0.1 no próprio contêiner (`--network none` e sem portas publicadas continuam), depois confirmar `SELECT 1` no banco real antes da suíte. No harness, classificar erros de conexão/transporte e registrar apenas exit code/SQLSTATE, sem imprimir SQL, credenciais ou payloads. Repetir também a prontidão após restart. A correção deve demonstrar que o teste saiu de setUpClass e executou as funções da migration; se a hipótese estiver errada, registrar o diagnóstico e corrigir a causa real, sem transformar falha genérica em PASS.

Fixar o digest da imagem efetivamente observada na primeira execução: `postgres:17-alpine@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`. Isso estabiliza a reprodução deste experimento, não é política definitiva de atualização do MVP.

## C01 — Cobertura CI da regressão I2

Os paths do workflow da arena não incluem os novos arquivos PostgreSQL. A obrigação de PG-06 continua: ampliar os filtros I2 para código/testes/planos I3-03, executar duas batalhas/abortos/timeout no mesmo head e conferir suas evidências. Não apresentar um workflow que não disparou como aprovado. O runtime do I2 permanece inalterado.

## Fontes oficiais

- https://www.postgresql.org/docs/current/app-pg-isready.html
- https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh
- https://www.postgresql.org/docs/current/app-psql.html

**Estado de F01/C01:** pendentes de implementação e reteste. Nenhum aceite PG-02..06 encerrado neste documento.
