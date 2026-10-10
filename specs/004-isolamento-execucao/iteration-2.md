# S04-T04 — Incremento I2: batalha com bot e árbitro separados

**Data:** 2026-10-10. **Estado:** PLANEJADO; publicar antes da implementação. **Base:** I1 no PR #17, commit 668d82b034cf5e0fab909e13552399c2de7213d5. **Branch:** feat/s04-i2-engine-isolation.

## Autorização e escopo

O responsável pediu continuidade das implementações planejadas e planejamento prévio de qualquer necessidade descoberta. D1 mantém RoboDSL básica; D2 autoriza VM dedicada como direção. D-005/G-EXP permite experimentos finitos em runner GitHub-hosted descartável. G-PROD permanece bloqueado. Nenhuma instalação de VM, mudança do Windows/WSL/Docker Desktop, firewall doméstico, .env, Compose ou banco está autorizada por este incremento.

**Objetivo verificável:** duas referências oficiais conhecidas executam em contêineres com PID, rede e filesystem distintos do árbitro. O árbitro conclui batalha real; uma credencial de bot não permite agir como controlador/observador; o bot só tem caminho de jogo necessário, sem acesso aos outros bots, à administração ou a serviços sintéticos do host. Registros e replay oficiais ficam preservados e coerentes.

Não aceita submissão de alunos, não amplia RoboDSL, não cria API pública/fila/ledger e não afirma homologação da VM no host. A rede em CI não substitui teste futuro de Hyper-V/guest.

## Lacunas identificadas antes do código

1. BattleRunner 1.4.0 inicializa bots com BooterManager local mesmo em externalServer. I2 deve verificar a API cliente/controller oficial ou outro adaptador controlado, sem executar bot no árbitro.
2. `network=none` impede comunicação de jogo entre contêineres. Bridge `internal` sozinha ainda pode permitir acesso ao host. Candidata para experimentar: uma rede bridge **internal + gateway_mode_ipv4=isolated por bot**, apenas árbitro e bot nessa rede; IPv6 desabilitado, IP forwarding do árbitro desligado, DNS externo negado, sem portas publicadas. Se indisponível ou negativo falhar, bloquear em vez de degradar para bridge comum.
3. Separar segredos de **bot**, **controller** e **observer**, conforme o protocolo efetivo v1.4.0. Confirmar implementação upstream, rejeição real e ausência de credencial de controle nos contêineres de bots. Não presumir que hashes autenticam árbitro comprometido.
4. Provas negativas precisam de controles positivos: endpoint de jogo acessível; listener sintético do runner realmente iniciado; destino peer realmente ativo; role legítimo aceito. Timeout isolado não basta para concluir autorização negada.
5. Perfis JVM são distintos do perfil diagnóstico 64 MiB do I1. Orçamentos iniciais do experimento: árbitro até 1 GiB/2 CPUs/128 PIDs; cada bot até 512 MiB/1 CPU/64 PIDs; tmpfs e saída limitados; timeout externo total até 240 s por batalha. São valores de teste, não capacidade/SLA de produção.
6. Código-fonte e artefatos oficiais necessários à compatibilidade devem ser fixados, com hashes e atribuição. São referências confiáveis, não entradas livres fornecidas por alunos.

## Tasks (subconjuntos do catálogo T001–T039)

| ID | Vínculo | Entrega e aceite | Estado |
|---|---|---|---|
| I2-01 | T005,T007,T020; FR-005,FR-006 | Investigar fontes upstream fixadas: server CLI, secrets/handshake, controller/observer, inicialização e gravação oficial; registrar contratos e limitações | A_FAZER |
| I2-02 | T007,T019,T022; FR-006,FR-018 | Especificar topologia, perfis e critérios positivos/negativos; validar suporte internal/isolated e não aceitar fallback | A_FAZER |
| I2-03 | T017,T020; FR-011,FR-015 | Construir imagens por papel (árbitro e bot) com upstream versionado; nenhum bot ou código recebido na imagem/processo árbitro | A_FAZER |
| I2-04 | T007,T020; FR-005,FR-012 | Implementar controlador confiável e gravação do replay oficial; iniciar bots independentemente, executar cinco rounds, conferir identidades/resultado | A_FAZER |
| I2-05 | T011,T019,T021; FR-006,FR-018 | Ensaiar credencial inválida, troca bot→controller/observer e comando administrativo por bot; demonstrar rejeição e sobrevivência da conexão legítima | A_FAZER |
| I2-06 | T006,T018,T022; FR-005,FR-007,FR-018 | Verificar namespaces/processos/mounts/segredos e políticas reais por contêiner; só canais previstos, nenhum socket Docker/host bind/porta publicada | A_FAZER |
| I2-07 | T019,T021; FR-006,FR-019 | Testar acesso permitido ao jogo e negado a host sintético, bot vizinho, porta não prevista, DNS externo e TEST-NET; sem scan de LAN/internet | A_FAZER |
| I2-08 | T024,T025; FR-009,FR-010 | Orquestrar com timeouts/saída limitada; limpar só recursos owned pela execução inclusive falha parcial; redes e contêineres sem órfãos | A_FAZER |
| I2-09 | T029,T031; FR-011,FR-012,FR-014 | Revalidar gzip/eventos/rounds/replay versus resultados; manifesto sanitizado sem tokens nem env/inspect bruto | A_FAZER |
| I2-10 | T021,T022,T037; FR-018 | Escrever unitários positivos/negativos para contratos/políticas/extração e fixtures malformadas; regressões existentes preservadas | A_FAZER |
| I2-11 | T007,T020,T036; FR-018,FR-020 | Executar duas batalhas reais e provas de papel/rede em CI efêmero; baixar e auditar artifact; falhas são FAILED/INCONCLUSIVO, nunca PASS fictício | A_FAZER |
| I2-12 | T039; FR-020 | Atualizar spec/plan/tasks/estado e evidências sem fechar T amplas ou G-PROD; registrar próximos I3/I4/I5 e limites | A_FAZER |

## Sequência e segurança de mudanças

I2-01/02 → I2-03 → I2-04/05/06/07/08/09 → I2-10/11 → I2-12. Testes de contrato precedem primeira execução integrada. Nova necessidade relevante exige atualização datada deste plano ou addendum **antes da alteração de código correspondente**. Alterações ficam em PR empilhado sobre #17; sem force push nem merge automático.

Os novos arquivos previstos são `spikes/isolamento/engine-separated/`, `services/worker_agent/engine_isolation.py`, `scripts/run_engine_isolation.py`, `tests/security/test_engine_isolation.py` e `.github/workflows/engine-isolation.yml`. Os antigos runners/UI não serão substituídos nesta etapa.

## Gate de aceite I2

Resultado **PASS no recorte** exige duas batalhas reais (cinco rounds cada), fronteiras distintas verificadas, provas positivas e negativas concluídas, autenticação de papéis observada, replay coerente, segredo ausente dos artifacts e cleanup específico confirmado. Ausência de suporte ou dúvida sobre isolamento bloqueia I2; não usar a palavra seguro para alunos. G-PROD, VM pessoal, vulnerabilidades desconhecidas, flood completo, broker multiusuário e tolerância a comprometimento total do árbitro permanecem fora da prova.

## Fontes técnicas primárias iniciais

- Battle Runner: https://robocode.dev/api/battle-runner.html (conferir contra commit v1.4.0 fixado, não migrar silenciosamente).
- Código upstream fixado: https://github.com/robocode-dev/tank-royale/tree/c8ad3a8d19a843f6258d6f6f9db7f29229963903.
- Gateway isolated exige internal e remove endereço da bridge do host: https://docs.docker.com/engine/network/port-publishing/#gateway-modes.
- Network none oferece apenas loopback: https://docs.docker.com/engine/network/drivers/none/.
