# Contrato experimental I3-02 — Identidade do canal broker ↔ worker

**Estado:** PLANEJADO para G-EXP em runner descartável; **NÃO é** endpoint de produção, registro de aluno, claim, lease ou execução. Ver [plano I3-02](../i3-02-auth-plan.md).

## Fronteira e identidade

```text
worker experimental (cliente TLS)
  | CA privada de CI + certificado clientAuth, URI SAN urn:robocopa:worker:<id>
  | 127.0.0.1, TLS 1.3 mTLS, server_hostname broker.robocopa.invalid
  v
broker/probe CI (servidor TLS)
  | CA privada de CI + certificado serverAuth e DNS SAN de broker
  | autorização em cada conexão: DER leaf SHA-256 + URI SAN + escopo + operação
  v
  resposta sintética probe_ack, job_claim_enabled=false
  X  sem SQLiteQueue, Docker, worker real, API pública ou pontuação
```

CA e chaves são geradas somente pela suíte de CI em `TemporaryDirectory`; nenhum material privado deve ser versionado, exportado como artefato ou logado. Exigir TLSv1.3, TLS client certificate obrigatório e validação de cadeia dedicada; cliente **também** verifica hostname, identidade URI SAN e digest da folha de broker. Fingerprint sozinho não substitui TLS: a autorização sempre usa `ssl.SSLSocket` após handshake efetivamente verificado. Identidade do worker é derivada do certificado, nunca de um campo declarado no payload.

## Frame permitido

Uma conexão por mensagem, timeout curto e máximo **512 bytes** de JSON UTF-8 terminado em `\n`, sem compression, stream, binário livre, duplicidade de chaves, NaN/Infinity ou campos desconhecidos:

```json
{"schema_version":1,"operation":"probe","scope_id":"lab-a"}
```

**Após validação mTLS e do escopo específico ao worker:** `{"schema_version":1,"operation":"probe_ack","worker_id":"worker-a","scope_id":"lab-a","job_claim_enabled":false}` (sem credenciais, jobs, logs ou paths). Erros são códigos constantes ou encerramento da conexão, sem eco de payload/certificado.

Qualquer `claim`, `start`, `complete`, `cancel`, `list`, `owner_ref`, `job_id`, `attempt_id`, escopo diferente ou campo extra é recusado. Não implementar **I3-03** por via de um "probe". O registro de autorização associa exatamente `{digest DER, URI SAN, scope_id, operations=["probe"]}` e sua atualização atômica é exclusiva do componente confiável em teste, não uma RPC. Remover certificado do registro faz novas conexões falharem; um certificado rotacionado precisa estar na CA e na lista de permitidos.

## Falhas de autorização obrigatórias

- Sem certificado de cliente; CA ou hostname incorretos; TLS1.2; role/SAN errado; fingerprint ausente/desconhecido; revogação e renovação com sobreposição.
- Escopo cruzado, operação administrativa disfarçada, identidade alegada no JSON, campos inesperados, UTF-8 inválido, JSON profundo/duplicado, frame >512 bytes, timeout/parcial, frame adicional.
- Nenhum bind fora de `127.0.0.1:0`, execução Windows/WSL/Desktop/local sem runner descartável explicitamente autorizado; nenhuma dependência do daemon.

## Aceites e limites

A verificação deve ocorrer com `ssl` real + certificados efêmeros + testes de integração; simulação de certificados/dicionários não será contada como autenticação. O laboratório não implementa PKI real, revogação persistente, reconexão operacional, seleção de workers, autorização de usuário final, ledger ou política de produção. A decisão sobre autenticação está resolvida somente como **opção experimental**, Q-07 continua aberta para operação real.
