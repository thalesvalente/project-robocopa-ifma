# Contrato interno 004 — Plano de controle ↔ worker isolado

**Status:** PROPOSTA; não é endpoint público, não está implementado e ainda exige decisão de autenticação/transporte (Q-07).  
**Regra:** o worker não recebe URL de Docker, credencial de banco, comando shell, argumentos arbitrários de processo, paths de host nem dados pessoais de aluno.

## Entrada lógica (exemplo de forma, valores fictícios)

```json
{
  "schema_version": 1,
  "job_id": "5fd435a1-a6a1-4f5a-923d-703537df5be2",
  "attempt_id": "eacdd8d4-7a24-4070-91c8-d6bdc58c223b",
  "version_id": "demo-version-001",
  "program_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "language_id": "robodsl/0.1",
  "trust_class": "T1",
  "engine_ref": "tank-royale/1.4.0",
  "policy_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "operation": "training",
  "rounds": 3,
  "idempotency_key": "demo-job-001",
  "deadline_at": "2026-10-09T23:59:00Z"
}
```

O payload de RoboDSL trafega em canal separado com tamanho limitado e hash comparado ao pedido; não colocar programa em nomes de arquivos, tokens, logs ou path. O valor `deadline_at` acima é apenas demonstração de sintaxe, não execução planejada nem timeout definido.

## Validações obrigatórias

1. Rejeitar campos inesperados, tipos errados, strings fora de limites, IDs repetidos e JSON ambíguo.
2. Validar que `version_id`, `program_sha256`, `language_id` e classe T1 foram previamente autorizados.
3. Verificar assinatura/autorização do canal worker e `policy_sha256` vigente antes de alocar recurso.
4. Não interpolar texto da submissão em shell, argumentos Docker livres, variáveis ambientais administrativas, paths ou imagens escolhidas pelo usuário.
5. `operation=competition` permanece inacessível até S07 com versões congeladas e regulamento aprovado.
6. Expiração ou repetição de `attempt_id` em outro worker deve ser rejeitada.
7. `rounds` e recursos só podem ser definidos por política do sistema; não usar números enviados livremente pelo navegador.
8. Daemon Docker, worker e conexões do árbitro nunca recebem credenciais do PostgreSQL.

## Saída lógica (sem dados pessoais)

```json
{
  "schema_version": 1,
  "job_id": "5fd435a1-a6a1-4f5a-923d-703537df5be2",
  "attempt_id": "eacdd8d4-7a24-4070-91c8-d6bdc58c223b",
  "state": "COMPLETED",
  "engine_ref": "tank-royale/1.4.0",
  "policy_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "program_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "rounds_completed": 3,
  "result_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "replay_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "cleanup_status": "VERIFIED"
}
```

**Não aceitar placar da stdout do bot**: somente saída verificável do árbitro/replay oficial e controle independente da submissão podem alimentar o ledger. Os resultados apresentados neste documento são fictícios.

## Erros previstos

`INPUT_REJECTED`, `POLICY_DISABLED`, `WORKER_UNAVAILABLE`, `POLICY_MISMATCH`, `RESOURCE_LIMIT`, `TIMEOUT`, `CANCELLED`, `ENGINE_INVALID`, `RESULT_INVALID`, `CLEANUP_FAILED`. Erros não devem incluir segredo, caminho privado, stack trace ou parte não autorizada do código.

## Idempotência, replay e integridade

- Chave de efeito único: `job_id + version_id + engine_ref + policy_sha256`, transacional e revisável.
- `attempt_id` diferencia retries; somente tentativa efetivamente autorizada pode finalizar o job.
- Replay/output devem possuir limites de tamanho, identidade do bot, rounds e hashes coerentes; no erro, sem pontuação.
- A saída do worker é tratada como **não confiável** até validação; comprometimento do árbitro requer barreira e auditoria adicionais (TH-15).

## Transporte e autenticação

Um canal autenticado worker↔broker, sem exposição de Docker remoto, é candidato (pull com escopo e expiração curta ou método equivalente). **Não fixar mTLS, fila ou configuração de rede antes de verificar compatibilidade, uso local e requisitos S03/S04.** Não há implementação pública nesta feature.

## Alinhamento I1/I3 e status do canal (2026-10-10)

O envelope implementado no I1 exige adicionalmente **`source_sha256`**, vinculado ao conteúdo imutável e ao `program_sha256`; o exemplo acima foi corrigido. O contrato continua PROPOSTA para transporte remoto: [I3-01](../iteration-3.md) só implementa fila interna/offline. Não existe handshake autenticado, token de aluno, endpoint público, claim remoto ou ledger oficial. Autenticidade da identidade `owner_ref` dependerá de Q-07/I3-02. Os campos de lease/resultado demonstrados acima NÃO foram implementados por efeito dessa correção documental.
