# S04-T04 / I3-02 — Plano de autenticação de serviço e autorização do canal

**Data:** 2026-10-10. **Estado:** PLANEJADO antes de código. **Base:** I3-01 commit `2bb82350cc9d71ce28b3b459a23603309b8ca1a1`, PR #23 (draft). **Relação:** este incremento é uma PR empilhada sobre #23, sem alterar a `main`.
**G-EXP:** exclusivamente fixtures de serviço/certificados efêmeros em runner Ubuntu GitHub-hosted descartável. **G-PROD:** bloqueado.
**Requisitos:** FR-003/004/006/007/010/011/013/014/016/018/019/020; TH-01/04/05/09/11/12/14/16; T008/T010/T011/T012/T015/T016/T027/T037. A lista T001..T039 ampla permanece aberta.

## Auditoria de preparo e escolha limitada para Q-07

O desenho lógico em `contracts/job-protocol.md` não implementa identidade nem prova de canal; I3-01 apenas enfileira sem consumidor, e seu `LabGate` simula worker, NÃO autentica. Não devemos permitir claim, dados de aluno ou trabalho remoto apenas com `owner_ref`, um HMAC improvisado, string de worker no JSON ou uma bridge Docker.

**Decisão experimental I3-D10:** avaliar **mTLS TLS 1.3 com certificados X.509 emitidos por CA de laboratório dedicada**, ambos os lados validando cadeia e identidade. Worker inicia a conexão (projeto future worker pull; não abrir porta de VM); o broker aceita somente uma prova `probe`, sem devolver jobs. O cliente valida hostname do broker `broker.robocopa.invalid` e fingerprint/SAN URI do certificado apresentado; o broker requer certificado de cliente e valida a identidade do worker por SAN URI exato `urn:robocopa:worker:<id>` + SHA-256 do certificado DER em lista aprovada + escopo autorizado. Identidades falsas no payload NÃO contam. Certificados/CA/chaves/paths privados não entram no Git, artefatos ou logs; produção precisa de bootstrap de PKI, armazenamento, rotação automática e revogação durável próprios.

**Operação do protótipo:** biblioteca Python padrão `ssl`/OpenSSL, sem TLS próprio. Somente listener de prova explícito vinculado a `127.0.0.1:0` em runner descartável, recusando Windows/WSL e ambiente não CI; um frame JSON por conexão com limite de bytes/timeout. Não publicar endereço/porta, nenhum HTTP, Docker socket, worker real, job, ledger ou dado estudantil. Toda tentativa de `claim`, `complete`, `cancel`, `list` ou escopo de outro worker falha fechado; não chamar `SQLiteQueue`. O probe bem-sucedido retorna apenas identidade verificada/escopo e `job_claim_enabled=false`.

**Revogação/rotação restritas ao experimento:** registro confiável in-memory, com atualização atômica de allowlist; aceitar duas folhas durante sobreposição e negar imediatamente a folha removida em novas conexões. Certificado curto **não substitui** revogação. Lista durável, CA real, automação/CRL/OCSP, key vault, auditoria independente e teste em VM NÃO estão neste escopo.

## Subtarefas: planejar → implementar → testar → registrar

- [ ] **I3-02a** [US1/US2] Fixar decisões, fronteiras TLS, ameaça de impersonação, plano de certificados e contrato `contracts/worker-channel.md`, sem autorizar prod, antes do primeiro código.
- [ ] **I3-02b** [US2] Criar `services/execution_control/worker_channel.py`: contextos cliente/servidor `ssl` obrigando TLS1.3, `CERT_REQUIRED`, CA exclusiva e hostname no cliente. Credenciais provêm de caminhos locais confiáveis, sem política de geração automática.
- [ ] **I3-02c** [US1/US2] Identidade extraída exclusivamente do socket TLS autenticado (SAN URI + SHA-256 DER); allowlist com objeto/escopo/permissão e revisão monotônica, revogação em novas conexões. Sem `owner_ref` de cliente e sem claim.
- [ ] **I3-02d** [US2] Provar em CI conexão real na interface loopback, um frame delimitado, limite e timeout; negar porta externa, host/WSL, operações administrativas, worker de escopo diferente, payload fora do esquema e erros sem refletir entrada.
- [ ] **I3-02e** [US2] Gerar somente em `TemporaryDirectory` CI certificados sintéticos via `openssl` (argumentos constantes sem shell, chave `0600`). Negativos reais: sem certificado, CA errada, hostname/SAN errados, certificado revogado/não autorizado, certificado de papel incorreto, duplicidade/oversize/claim, rotação e um positivo por identidade.
- [ ] **I3-02f** [US4/US5] Rodar suites e verificadores Spec Kit, I1, I2 arena real e autoria sem regressão; registrar fonte exata, runs, artefatos e ressalvas em `docs/qualidade/evidencias/S04-T04-I3-02.md` e JSON. Deixar PR em draft sem merge até revisão; manter I3-03..I3-07 abertas.

## Critérios de saída do G-EXP / não equivalência

Todos os testes de mTLS devem usar handshake **real** TLS1.3 no runner, sem mocks contados como autenticação. Zero credential file em Git/artifact e zero invocação Docker por esse módulo; cliente não deve aceitar servidor sem CA/hostname/pin correto; broker não deve aceitar cliente sem certificado aprovado, escopo e operação autorizados. A remoção de uma folha deve negar novos probes; só retornam mensagens mínimas sem jobs. CI da versão final sem falhas, sem marcar testes ainda em execução como PASS.

**Conclusão I3-02 experimental ≠ liberação de worker real.** Antes do I3-03/rede real ainda são necessários PKI do ambiente, registro de identidade durável, bootstrap com armazenamento/rotação/revogação seguros, autenticação do operador, portabilidade do transporte e testes de rate-limit/observabilidade/HA; I4/I5 e ratificações S00/S03 continuam pendentes. Novo achado exige adendo documentado antes do patch.

## Fontes técnicas verificadas

- Python `ssl`/TLS contextos: https://docs.python.org/3.13/library/ssl.html
- OWASP, Microservices Security: https://cheatsheetseries.owasp.org/cheatsheets/Microservices_Security_Cheat_Sheet.html
- OWASP ASVS 5.0 comunicação interna: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x21-V12-Secure-Communication.md
- RFC 8705 (padrão de mTLS em outro contexto, não protocolo implementado aqui): https://www.rfc-editor.org/rfc/rfc8705

## Adendo H01 — provas negativas de TLS/certificados (planejado antes do patch)

Após a primeira execução `38066685575` (29 testes PASS), a revisão encontrou **lacuna de cobertura**, não um bypass comprovado: a restrição TLS1.3 era verificada por propriedades do contexto, sem um handshake negativo real usando TLS1.2. O teste de CA incorreta configurava também o cliente para confiar na CA errada e, portanto, podia reprovar por desconfiança do servidor, sem demonstrar a rejeição do certificado do cliente no lado broker.

Antes do patch de testes: **(1)** abrir socket real com cliente TLS1.2 e confirmar falha de negociação/recusa no broker; **(2)** fazer o cliente confiar na CA correta enquanto apresenta certificado de outra CA, comprovando rejeição pelo broker; **(3)** testar separadamente servidor assinado por CA não confiável; **(4)** negar chaves privadas de teste permissivas (0644) e symlink para a chave. Não mudar a política TLS, o runtime de jobs nem considerar nova prova aprovada sem CI. Acrescentar regressão dos cinco casos, mantendo o código de emissão de certificados exclusivamente na fixture CI.
