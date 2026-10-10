# I3-03C — API de controle e cliente worker outbound para DEMO

**Data:** 2026-10-10. **Estado inicial:** PLANEJADO ANTES DO CÓDIGO. **Base:** PR #26 em 33d9bc9 + main após D-012/PR #31. **Ordem:** D-012, I3-03C antes de I3-04. **Limite:** integrar transporte de comandos com PostgreSQL em CI, não implantar Supabase/VM ou fechar I3 integral.

## Reconciliação e fronteiras

Manter PG-01..06/001_control.sql e AD-01..06/002_admission.sql imutáveis. Incorporar D-011, ID-010 e D-012 da main sem remover avanço I3 do índice/estado. Multiescola e OAuth de alunos ficam no Marco B. Nenhum job é concluído/contabilizado neste incremento (I3-04 pendente).

## Decisões de implementação deste recorte

1. API de comandos curtos em JavaScript Web Request/Response, utilizável no Deno das Supabase Edge Functions. Deno e driver postgres 3.4.7 fixados para a prova; PostgreSQL usa conexão restrita rc_worker_api, max pequeno e prepare=false. Ambiente cloud exigirá TLS com validação de CA/hostname e ensaio no pooler real, não comprovados pelo socket CI.
2. A opção mTLS I3-02 continua prova histórica. Não presumir que o gateway gerenciado repassa certificado do cliente. Para este recorte, HTTPS com certificado de servidor verificado + credencial **opaca aleatória de 256 bits por worker/escopo**, TTL máximo de 15 minutos e revogação persistida no PostgreSQL. Não é JWT, login estudantil ou service-role Supabase. Usar secrets/Web Crypto SHA-256, não inventar algoritmo criptográfico.
3. Somente hashes de credenciais em tabela privada; emissão/renovação é administrativa fora da API, com fixture efêmera no CI. Nenhum endpoint de autoinscrição, refresh ou concessão de privilégios. O worker guarda seu segredo apenas no processo de controle (arquivo 0600 no teste), nunca em bot, payload, URL, log ou artefato. Rotação com sobreposição e revogação devem ser testadas; automação operacional de emissão permanece pendente.
4. Nova migration 003_worker_api.sql adiciona rc_worker_api NOLOGIN sem privilégio elevado, credenciais e recibos idempotentes sob RLS forçada. Uma única função autorizada recebe digest/command/request_id/arguments; obtém worker_id/scope **do registro de credencial**, não do corpo. Não conceder claim bruto/tabelas a esse papel, usuário ou bot. As roles anteriores conservam contratos prévios.
5. Comandos claim/start/heartbeat/fail: nenhuma versão/código é executado. Não expor enqueue/admin/list/cancel alheio/complete, nem credenciais DB ao worker. Para claim, retornar somente descritor aprovado/IDs/lease sem PII; recuperar fonte e executar motor é incremento posterior. Novas requisições por worker são serializadas, possuem intervalo mínimo e no máximo uma lease ativa; mesma request_id/conteúdo retorna recibo sem segundo efeito. request_id com outro corpo falha. Recibo antigo não retorna lease obsoleta nem prorroga deadline; revogação/expiração da credencial e worker conferidas antes de qualquer reaproveitamento.
6. Handler falha fechado: habilitação explícita OFF por padrão; somente POST/path único HTTPS; sem query, Origin/cookies, redirects, JSON duplicado, valores não finitos, campos extras ou mais de 2 KiB. Limite de leitura/tempo de corpo, validação estrita de UUID/fence/reason; códigos sanitizados/cache no-store. Nenhuma CORS aberta. Requisição não autenticada não recebe dados de job.
7. Cliente Python worker inicia HTTPS para endpoint configurado confiável, verifica certificado/hostname, não segue redirect e ignora proxies de ambiente; tempo/tamanho de resposta limitados, valida correlação request_id/op/scope/schema e descritor retornado. Retry é explícito **com o mesmo request_id**, nunca nova reserva silenciosa. Não executa subprocesso/bot; falha de rede tem resultado UNKNOWN até reconsulta idempotente.
8. Supabase: função de serviço segregada pode exigir verify_jwt=false pois a credencial não é JWT Supabase; **somente** nessa função e com autenticação obrigatória por digest/SQL. Funções de alunos NÃO são alteradas. Configuração demonstrativa não é autorização de deploy. Sem chave publishable usada como autenticação de worker e sem distribuir sb_secret/service-role.

## Subtarefas e aceites

- [ ] CW-01 Publicar este plano e contrato antes do código; reconciliar main/#26 preservando runtime/histórico e prioridades.
- [ ] CW-02 Migration003 privada: credencial/worker/escopo, TTL/revogação/rotação, comandos allowlist e idempotência/locks/recibos. Reaplicação segura ou recusa explícita sem perda de dados.
- [ ] CW-03 Handler Deno/Fetch e adaptador PostgreSQL parametrizado, configuração cloud separada de harness local, dependências fixadas e nenhum segredo em fonte/logs.
- [ ] CW-04 Cliente Python outbound HTTPS com verificações de TLS, resposta, deadline/correlação, sem execução de motor.
- [ ] CW-05 Testes reais em runner descartável: Python -> HTTPS Deno -> driver -> PostgreSQL; positivo claim/start/heartbeat/fail, sem credencial, incorreta/expirada/revogada, cross-worker/cross-scope, duplicata concorrente/lost response, stale lease/fence, gates desligados, SQL/RLS/commit/restart, TLS CA/hostname inválidos e cleanup. Unidades/fakes declarados separadamente.
- [ ] CW-06 Regressões I1/I2/PG/AD/autoria/identidade; fonte/runs e contagens sanitizadas; atualizar plan/tasks/estado/PR e limitações. Não marcar I3-03 integral/G-DEMO como aprovados por prova CI.

## Prova e limites de implantação

Runner Ubuntu GitHub-hosted, banco postgres17 já fixado no projeto, --network none/sem portas; socket/HBA próprios e volume owned. Deno/HTTPS vinculado apenas a 127.0.0.1 em porta efêmera; CA/chaves de teste geradas em TemporaryDirectory e não exportadas. Não executar contra PC/VM/Supabase real nem aluno. O pacote source do CI não pode conter segredos. Limpar processo HTTPS, certificado, banco/volume/socket e validar ausência após consulta bem-sucedida.

**Permanece aberto:** deploy/compatibilidade Supabase Edge/pooler/TLS real, bootstrap/renovação operacional de credenciais, admissão DEMO cloud, obtenção da fonte do robô pelo worker, ligação ao supervisor I2, VM I4, resultado/replay I3-04 e gates de piloto. Bearer roubado pode ser usado até expiração/revogação; TLS e escopo reduzem risco, não são prova de posse mTLS/DPoP. Intervalo mínimo por worker não protege de todo DoS pré-auth; quota de plataforma/piloto em I3-05. Não alegar proteção de rede pública por testes loopback.

## Fontes oficiais confrontadas em 2026-10-10

- Supabase auth: https://supabase.com/docs/guides/functions/auth e https://supabase.com/docs/guides/functions/auth-headers — separar segredo de projeto/usuário de credencial específica de serviço.
- Supabase Postgres: https://supabase.com/docs/guides/database/connecting-to-postgres e https://supabase.com/docs/guides/functions/connect-to-postgres — driver server-side e prepare=false para transaction pooling.
- PostgreSQL funções: https://www.postgresql.org/docs/17/sql-createfunction.html — search_path fixo e grants mínimos.
- Driver postgres 3.4.7: https://github.com/porsager/postgres/tree/v3.4.7 — JavaScript/Deno sem dependências de runtime adicionais.

Toda necessidade nova requer adendo pré-patch. Resultado real de CI deve preceder alteração de checkbox.
