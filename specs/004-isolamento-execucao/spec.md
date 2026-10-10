# Feature Specification: Isolamento da execução de robôs (S04-T04)

**Feature Branch**: `docs/s04-t04-isolamento-speckit`  
**Created**: 2026-10-09  
**Status**: Draft — especificação técnica preparada; sem implementação, homologação ou teste de ataques  
**Input**: solicitação do responsável para planejar a S04-T04 usando o Spec Kit, antes de implementar.  
**Gates**: constituição S00-T06, requisitos S03-T06, arquitetura S04-T01, motor S04-T02 e autoria S04-T03 ainda não possuem todos os aceites formais.

## Contexto e escopo

A RoboCopa executará robôs programados por estudantes no servidor de propriedade do responsável. O host Windows 11 Pro já possui Docker Desktop/WSL 2, projetos próprios, serviços e dados que **não** podem ficar ao alcance de um robô, do compilador de submissões ou de processos filhos. O laboratório atual de autoria usa RoboDSL restrita e o servidor Python local possui acesso à CLI Docker. Os onze controles Docker observados no experimento com bots conhecidos **não comprovam contenção de código malicioso**.

Definir aqui o contrato de segurança de **submissão → validação → preparação → execução → resultado → descarte**. Testes destrutivos, de exfiltração, saturação e de fuga devem ocorrer **apenas em ambiente descartável e separado, previamente autorizado**, com dados fictícios. No computador pessoal, nesta etapa, **somente documentação e comandos de leitura**; nenhuma configuração de rede, daemon ou VM será alterada.

### Classes de confiança

| Classe | Exemplo | Política preliminar |
|---|---|---|
| T0: referência confiável, fixada por hash | Walls e Spin Bot oficiais | Laboratório atual, local, ainda sem publicação |
| T1: expressão controlada | Programa RoboDSL analisado em AST com template fixo | **Entrada não confiável**, requer isolamento verificado antes de receber alunos |
| T2: binário ou código geral | Java, JavaScript ou executável livre | **Fora do MVP inicial**, negar execução até nova arquitetura, avaliação e aceite explícitos |

A restrição T2 não converte T1 em código confiável nem elimina os riscos de parser, compilação, runtime e sistema operacional.

## User Scenarios & Testing

### User Story 1 — Bloquear execução não autorizada (Priority: P0)

Como mantenedor, preciso impedir que uma solicitação pública chegue ao Docker ou ao sistema de arquivos pessoal sem atravessar os controles de autorização, validação e liberação do executor.

**Independent Test**: enviar requisições inválidas e observar que nenhuma execução foi criada e nenhum acesso ao daemon foi disparado.

**Acceptance Scenarios**:

1. **Given** a integração pública desabilitada, **When** um participante envia submissão, **Then** recebe recusa segura sem criação de job de execução.
2. **Given** uma entrada fora da RoboDSL aprovada, **When** tenta utilizar Java livre, caminho de arquivo, importação ou comando de sistema, **Then** a entrada é rejeitada antes de qualquer compilação/execução.
3. **Given** um pedido válido de treino, **When** o controlador de domínio o aceita, **Then** somente uma requisição tipada e imutável, sem credenciais nem texto de comando de shell, pode ser emitida ao componente executor autorizado.

### User Story 2 — Conter um job dentro de sua fronteira (Priority: P1)

Como operador, preciso que o robô fique isolado dos dados pessoais, de outros projetos, dos demais participantes e do plano de controle.

**Independent Test**: em laboratório descartável, rodar provas negativas sintéticas de arquivos, redes, credenciais e separação entre jobs e verificar recusa, sem acesso ao computador pessoal.

**Acceptance Scenarios**:

1. **Given** um job em ambiente descartável, **When** tenta ler arquivos fora da área autorizada, **Then** a operação é negada e não há conteúdo protegido na saída.
2. **Given** um job ativo, **When** tenta acessar socket Docker, endpoint administrativo, banco, outros jobs ou internet, **Then** o acesso é negado; apenas canal estritamente necessário ao motor poderá existir após avaliação específica.
3. **Given** saída do jogo, **When** o resultado atravessa a fronteira, **Then** passa por esquema, limites, identidade e integridade antes de ser persistido.

### User Story 3 — Limitar abuso de recursos e recuperar falhas (Priority: P1)

Como operador, quero limites, encerramento e limpeza auditáveis para que robôs travados ou adversariais não ocupem indefinidamente a máquina.

**Independent Test**: testes de estresse com cargas sintéticas e limites baixos, dentro de runner/VM descartável, com medição e verificação de órfãos.

**Acceptance Scenarios**:

1. **Given** um job de teste, **When** ultrapassa um limite de CPU, memória, processos ou tempo, **Then** a política aplica contenção/encerramento, registra motivo padronizado e libera o slot.
2. **Given** falha, cancelamento ou reinício do executor, **When** o supervisor retoma operação, **Then** o job converge para estado terminal único e não duplica placares.
3. **Given** N testes sequenciais, **When** finalizam, **Then** não restam contêineres temporários, arquivos ou processos ativos da rodada, conforme escopo da VM.

### User Story 4 — Provar identidade e integridade dos resultados (Priority: P1)

Como organizador, preciso confiar que cada resultado corresponde à versão inscrita e que erros/artefatos manipulados não alteram a classificação.

**Independent Test**: replay oficial e saída associada a hash de programa e execução; manipular somente fixtures de testes para verificar rejeição de divergências.

**Acceptance Scenarios**:

1. **Given** versão imutável, **When** uma partida termina, **Then** os campos de resultado são vinculados ao job, hash da versão, configuração do motor e regras vigentes.
2. **Given** resultado malformado, truncado, duplicado, com hash divergente ou rounds inconsistentes, **When** o controlador valida, **Then** o job é marcado inválido, sem atualizar a pontuação.
3. **Given** repetição/cancelamento de job, **When** o resultado é recebido mais de uma vez, **Then** a persistência é idempotente.

### User Story 5 — Operar uma chave de suspensão de segurança (Priority: P2)

Como mantenedor, preciso desabilitar imediatamente novos trabalhos caso um controle crítico falhe, sem depender de alterar containers de projetos alheios.

**Independent Test**: negar novos jobs com flag de liberação desligada e comprovar preservação dos recursos não relacionados em ambiente de teste.

**Acceptance Scenarios**:

1. **Given** falha de verificação de isolamento ou perda do worker segregado, **When** alguém solicita execução, **Then** o sistema falha fechado e não faz fallback para o Docker Desktop pessoal.
2. **Given** suspensão de segurança, **When** ocorre tentativa de treino, **Then** há erro operacional legível e evidência de evento, sem vazamento de internals.
3. **Given** retomada, **When** o operador solicita habilitação, **Then** requer evidências de regressão e aceite expresso conforme gate.

### Edge Cases

- Duas solicitações simultâneas, reconexão do navegador e cliente repetindo requisições.
- Desligamento do Windows/WSL, queda do daemon, falta de disco, container parcialmente iniciado, job encerrado sem replay.
- Entrada com milhares de linhas, Unicode irregular, JSON ambíguo, escapes, arquivos ZIP externos, caminhos com `..` e links simbólicos.
- Rede interna necessária à comunicação Tank Royale por WebSocket, mas sem saída para serviços do host nem internet: **ainda requer prova funcional da topologia**.
- Erros que poderiam incluir fragmentos do código do participante, nomes de arquivos, endereços ou variáveis de ambiente em logs.
- Resultado em que `totalScore` coincide para dois robôs, mas `rank` difere: regra de classificação pertence a S03-T03; issue #15 não é defeito confirmado.
- Dependência comprometida, imagem alterada, tag de contêiner substituída ou replay falsificado.
- Suspeita de comprometimento do motor/árbitro por bot malicioso; separar fronteira e revisar confiança nas evidências.
- Quota/timeout alcançados ao mesmo tempo em que ocorre solicitação de cancelamento.
- Executor indisponível ou inseguro: falhar fechado; **nunca** iniciar automaticamente no host pessoal como alternativa.

## Requirements

### Functional Requirements

- **FR-001**: classificar submissões como T0/T1/T2 e aplicar política explícita de aceitação; T2 fica negada por padrão no MVP.
- **FR-002**: rejeitar sintaxe/AST, tamanhos, tokens, argumentos, profundidade e contextos incompatíveis antes de criar um job executável.
- **FR-003**: manter API pública e credenciais do banco fora do processo/ambiente que executa estratégia de participante.
- **FR-004**: impedir que rotas de usuário invoquem diretamente a CLI/socket Docker; permitir somente um broker tipado, autenticado, com privilégios mínimos.
- **FR-005**: isolar execução de cada job e demonstrar proteção contra leitura/escrita de arquivos e recursos do computador pessoal e de outros projetos.
- **FR-006**: negar egressão de rede por padrão; permitir apenas comunicações indispensáveis ao árbitro, explicitamente testadas em topologia segregada.
- **FR-007**: proibir montagens do host, Docker socket, modo privileged, compartilhamento de PID/rede do host, dispositivos/GPU e capabilities não necessárias.
- **FR-008**: aplicar limites observáveis de CPU, memória, PIDs, armazenamento temporário e concorrência, com valores calibrados antes do aceite.
- **FR-009**: impor deadline por job, cancelar, terminar processos descendentes e registrar razão normalizada de interrupção.
- **FR-010**: limpar recursos temporários por job e recuperar jobs abandonados sem afetar infraestrutura de outros projetos.
- **FR-011**: vincular artefatos e resultados a IDs, hashes imutáveis de submissão/versão, configuração do motor e tentativa.
- **FR-012**: rejeitar resultados/replays truncados, malformados, duplicados ou divergentes; não usar saída textual do bot como fonte de pontuação.
- **FR-013**: garantir que tentativas repetidas, timeout e reinício não causem dupla pontuação nem publicação de resultado de outro job.
- **FR-014**: produzir auditoria sanitizada de decisões, falhas, limites e limpeza, sem segredos, IP residencial ou dados identificáveis de alunos.
- **FR-015**: manter lista de dependências/imagens aprovadas, com origem, hash/digest e política para atualização sem execução de downloads durante o job.
- **FR-016**: suspender novas execuções automaticamente quando controle crítico não puder ser comprovado; não usar fallback ao host.
- **FR-017**: resistir a requisições concorrentes, spam e esgotamento de filas por limites de taxa/cotas e admissão controlada.
- **FR-018**: verificar o isolamento efetivo por inspeção de runtime e por provas negativas sintéticas, não apenas por arquivos de configuração.
- **FR-019**: garantir que os mecanismos e comandos de teste não alterem `.env`, Compose, banco, firewall, VHDX, redes ou contêineres existentes do responsável.
- **FR-020**: bloquear publicação do serviço para estudantes até gates de constituição, requisitos, topologia, testes de segurança, operação e aceite humano.

### Key Entities

- **SubmissionVersion**: ID, proprietário lógico, hash do código/AST, versão da linguagem, estado imutável.
- **ExecutionRequest**: ID, versão permitida, política autorizada, idempotency key, parâmetros de treino, referência à configuração do motor.
- **ExecutionAttempt**: ID, job, tentativa, transições, deadline, motivo de término.
- **IsolationPolicy**: versão/digest, limites, capacidades negadas e canal de comunicação estritamente permitido.
- **EvidenceManifest**: hashes de resultado/replay, IDs, contagem de rounds, verificações de integridade e limpeza.
- **SecurityGateDecision**: decisão de liberar/bloquear, responsável, evidências, versão da política e data.

Detalhamento de contratos e campos: [data-model.md](data-model.md) e [job-protocol.md](contracts/job-protocol.md).

## Success Criteria (propostos; requerem ratificação)

- **SC-001**: 100% das requisições rejeitadas na matriz negativa deixam **zero jobs executados**.
- **SC-002**: 100% das sondas de acesso a ativos proibidos no ambiente descartável são **negadas**, com evidência coletada; isso não prova ausência de vulnerabilidades desconhecidas.
- **SC-003**: 100% dos testes de limites observam a política efetiva de CPU, memória, PIDs e tempo; tolerância temporal a definir por medição.
- **SC-004**: 20 execuções/cancelamentos sintéticos consecutivos deixam **zero recursos temporários órfãos** na VM/runner, sem afetar outros projetos.
- **SC-005**: 100% dos fixtures com hash/replay/rounds divergentes são rejeitados antes de persistir pontuação.
- **SC-006**: 100% das transições terminais de teste são idempotentes, inclusive falha e retry concorrentes.
- **SC-007**: zero segredos ou identificadores pessoais nos artefatos de CI, documentação e logs de teste revisados.
- **SC-008**: sem sandbox aprovado, nenhuma submissão de aluno chega a job executável nem ao Docker Desktop do responsável.

## Assumptions, exclusions and gates

- A arquitetura **candidata** usa VM Linux segregada com mecanismo de execução próprio, para não compartilhar daemon, arquivos e credenciais com os projetos pessoais. É hipótese a validar, não instalação.
- O primeiro recorte público, se ratificado, aceita **somente RoboDSL restrita**; código geral arbitrário fica fora.
- Os limites numéricos usados em spikes anteriores (2 CPUs, 2 GiB, 256 PIDs, 240 s) **não são política de produção homologada**.
- Não contempla autenticação de alunos, HTTPS público, coleta de dados institucionais, expansão de linguagem, avaliação de impacto educacional ou implantação na máquina: pertencem a outras tarefas e gates.
- Esta feature pode ter **documentação preparada em paralelo**, mas a execução de testes de abuso só será autorizada em ambiente descartável separado depois da revisão. S04-T04 continua **A_FAZER** até evidência técnica e aceites formais.
