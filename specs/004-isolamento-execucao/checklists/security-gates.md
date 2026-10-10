# Security Release Gates — Feature 004

**Purpose:** decisões que devem ter evidência real antes de aceitar código de alunos ou expor acesso.  
**Created:** 2026-10-09 · **Status:** **BLOQUEADO — nenhum gate técnico aprovado nesta rodada documental.**

## G0 — Escopo e ambiente

- [ ] SG001 Constituição, baseline de requisitos e ADR-004 ratificadas pelo responsável.
- [ ] SG002 DSL T1/T2 e restrições de competição aprovadas.
- [ ] SG003 Ambiente de testes adversariais separado, descartável e sem arquivos pessoais autorizado.

## G1 — Fronteira efetiva

- [ ] SG004 Worker com plano de execução independente do Docker Desktop pessoal; sem drives compartilhados.
- [ ] SG005 Bot e árbitro separados ou risco residual aceito com alternativa demonstrável.
- [ ] SG006 Canal WebSocket mínimo funciona sem internet, LAN ou acesso ao host.
- [ ] SG007 Sem socket Docker, host mounts, capabilities extras, modo privileged, rede/PID host.
- [ ] SG008 Identidades/credenciais da plataforma e de outros jobs ausentes do sandbox.

## G2 — Execução e integridade

- [ ] SG009 Negativos TH-01..TH-16 registrados com esperado, observado e política efetiva.
- [ ] SG010 Cotas, timeouts, shutdown, recuperação e 20 limpezas controladas passaram.
- [ ] SG011 Hash, replay e resultados vinculados a versão, job, motor e política; fixtures alteradas negadas.
- [ ] SG012 Fila/rate-limit, idempotência e kill-switch demonstrados.
- [ ] SG013 Nenhum segredo, IP residencial nem dado real de estudante no log e artifacts.

## G3 — Operação e autorização

- [ ] SG014 Testes CI/VM documentados sem declarar testes que não ocorreram no host.
- [ ] SG015 Procedimento de backup/restauração/rollback testado para implantação alvo.
- [ ] SG016 Revisão independente de segurança sem achados críticos/altos não tratados.
- [ ] SG017 Autorização explícita de implantação e eventual exposição externa, com autenticação/TLS.
- [ ] SG018 Decisão humana de aprovação publicada com IDs/hashes das evidências.

**Conclusão:** enquanto **qualquer controle crítico** estiver pendente ou inconclusivo, o serviço de submissões deve permanecer desabilitado e sem fallback para Docker Desktop do responsável. Marcar checkbox somente mediante evidência externa de testes reais e responsável pela decisão.
