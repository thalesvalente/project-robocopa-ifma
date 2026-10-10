# Data Model — contrato lógico de execução segura (proposta)

**Status:** modelagem de design; **não** há migração criada ou decisão da baseline S03.  
**Objetivo:** impedir que job, resultado ou tentativa sejam identificados apenas por nomes visíveis de bot, porta ou texto livre.

## Entidades e campos

### SubmissionVersion

| Campo | Regra proposta |
|---|---|
| `version_id` | ID opaco imutável, único |
| `owner_ref` | referência pseudonimizada; não enviar identidade para a VM |
| `source_sha256` | SHA-256 do texto submetido (64 hex) |
| `program_sha256` | SHA-256 do programa AST canônico (64 hex) |
| `language_id` | enum: `robodsl/0.1` candidato |
| `trust_class` | enum T0, T1, T2; T2 nunca permitido automaticamente |
| `frozen_at` | momento da criação imutável; hash não muda em retry |

### ExecutionRequest

| Campo | Regra proposta |
|---|---|
| `job_id` | UUID gerado pelo plano de controle |
| `attempt_id` | UUID novo por tentativa |
| `version_id`, `program_sha256` | devem existir no catálogo autorizado |
| `engine_ref` | versão/digest aprovado, ex.: Tank Royale 1.4.0 |
| `isolation_policy_id` | digest imutável e aprovado para worker |
| `operation` | enum `training`, `competition` (competição fora da feature) |
| `rounds` | inteiro positivo, validado contra regra de treino |
| `deadline_at` | instante absoluto aprovado; limite calibrado |
| `idempotency_key` | identificador opaco de deduplicação |
| `lease` | validade curta, exclusiva da tentativa; sem autoridade para outros jobs |

### IsolationPolicy

`policy_id`, `policy_sha256`, `allowlisted_image_digests`, `uid_gid`, `cpu_limit`, `memory_bytes`, `pids_limit`, `tmpfs_bytes`, `wall_timeout_ms`, `network_allowlist`, `read_only`, `capabilities`, `user_namespace_mode`, `runtime_profile`, `max_concurrency`. Valores concretos e suporte pelo runtime precisam ser comprovados; não copiar os 2 GiB de spikes como baseline automática.

### ExecutionAttempt

`attempt_id`, `job_id`, `worker_id`, `state`, `claimed_at`, `started_at`, `finished_at`, `failure_reason`, `policy_sha256`, `runtime_attestation_ref`. `failure_reason` é enum (não log bruto com código/segredo).

### EvidenceManifest

`job_id`, `attempt_id`, `version_id`, `program_sha256`, `engine_ref`, `policy_sha256`, `result_sha256`, `replay_sha256`, `rounds_completed`, `cleanup_status`, `verified_at`. Não inclui caminho pessoal, usuário do SO ou IP doméstico.

### SecurityGateDecision

`gate_id`, `policy_sha256`, `reviewer_ref`, `decision` (`APPROVED`/`BLOCKED`), `evidence_refs`, `unresolved_critical_risks`, `decided_at`. Apenas revisão formal pode autorizar transição; existência do arquivo não constitui aprovação.

## Máquina de estados proposta

```text
RECEIVED -> REJECTED
        -> VALIDATED -> QUEUED -> CLAIMED -> RUNNING -> COMPLETED
                                           |        -> FAILED
                                           |        -> TIMED_OUT
                                           |        -> CANCELLED
                                           -> FAILED (claim perdido)
```

- `COMPLETED` pressupõe resultado do motor e replay validados, não só exit-code 0.
- Qualquer estado terminal recebe no máximo um efeito de pontuação. Novas tentativas reutilizam `job_id` mas têm `attempt_id` distintos; resultados velhos não substituem os atuais.
- `REJECTED`, `FAILED`, `TIMED_OUT`, `CANCELLED` não contam como vitória; regra de competição é definida separadamente em S03-T03.
- Replicar/convergir estado após queda do broker é requisito de implementação ainda não cumprido.
- A fronteira do worker conhece somente referências pseudônimas e programa validado, sem acesso à tabela de participantes.

## Retenção e deleção

Logs de erro e replays só devem persistir pelo tempo estritamente necessário aos objetivos do evento e à política institucional. **Prazo não está definido** (Q-08); não publicar artefatos com dados de participantes no repositório.
