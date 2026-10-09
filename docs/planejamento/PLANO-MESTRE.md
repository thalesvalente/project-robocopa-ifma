# Plano mestre de execução — RoboCopa IFMA

**Versão operacional:** 0.1.1 · **Data:** 2026-10-09

> Visão gerada de backlog.json. Os caminhos são saídas planejadas, não provas de entrega.

## Direção e limites

MVP hospedado na máquina do responsável; participação pelo computador e celular, incluindo autoria, treino e inscrição. ChatGPT Pro é o ambiente principal; Codex e R4 são exceções justificadas. Spec Kit apoia especificações e tarefas por funcionalidade.

As sprints são ciclos por objetivo, não equivalem a semanas ou mensagens. Testar a cada incremento. A primeira fatia vertical real é a S06. A S08 concentra regressão e operação. A S09 exige piloto e homologação reais.

Uma abordagem de autoria, um formato de competição, dados mínimos e acesso inicial controlado. Aplicativos nativos independentes, múltiplas linguagens, competição pública aberta e IA obrigatória ficam fora do primeiro MVP.

## Uso do planejamento

`A_FAZER → EM_EXECUCAO → EM_REVISAO → CONCLUIDA`, com `BLOQUEADA` quando necessário. Conclusão exige evidência. Minutas paralelas não encerram dependências. Issues espelham o backlog; tarefas técnicas vivem em specs/. Detalhes: docs/processo/EXECUCAO.md.

## Sprints e tarefas
## S00 — Fundação, governança e Spec Kit

**Objetivo:** Preparar o repositório, o método de trabalho e a ferramenta, sem antecipar a implementação do produto.

**Critério de saída:** Pacote publicado em branch de trabalho, acesso efetivo verificado, CLI inicializada sem sobrescrever documentos e constituição ratificada.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S00-T01 | **Verificar acesso e publicar a base**. Testar leitura e escrita reais; publicar a base em branch e registrar commit/PR. | README.md; docs/planejamento/ESTADO-ATUAL.md | Leitura e publicação verificadas por retorno do GitHub; nenhuma credencial ou dado real no diff. | ChatGPT Pro / P | — | CONCLUIDA |
| S00-T02 | **Preparar e ativar o Spec Kit**. Fixar upstream e commit; inicializar generic em staging e preservar documentos existentes. | tools/speckit.lock.json; .specify/; .agents/commands/ | CLI da versão fixada executada no ambiente autorizado; templates e comandos presentes; sem sobrescrita silenciosa. | ChatGPT Pro e CI; host local pelo responsável / M | S00-T01 | CONCLUIDA |
| S00-T03 | **Estabelecer a constituição e o processo**. Documentar inclusão, finalidade pedagógica, segurança, rastreabilidade e uso de ChatGPT/Codex/R4. | AGENTS.md; .specify/memory/constitution.md; docs/processo/EXECUCAO.md | Minuta consistente e versionada; a ratificação humana fica explicitamente para T06. | ChatGPT Pro / P | — | CONCLUIDA |
| S00-T04 | **Publicar backlog e modelos de acompanhamento**. Publicar 10 sprints/60 tarefas, dependências, modelos de issues/PR e evidências. | docs/planejamento/backlog.json; docs/planejamento/PLANO-MESTRE.md; .github/ | IDs únicos; dependências sem ciclos; tarefas com saída e aceite; publicação efetivamente confirmada. | ChatGPT Pro / M | S00-T01, S00-T03 | CONCLUIDA |
| S00-T05 | **Levantar o ambiente de hospedagem**. Coletar somente inventário técnico sanitizado; não alterar a máquina ou publicar dados residenciais. | docs/operacao/inventario-sanitizado.md | Informações verificadas pelo responsável e lacunas registradas; nenhuma configuração de rede alterada nesta tarefa. | Responsável no host; apoio ChatGPT Pro / P | — | BLOQUEADA |
| S00-T06 | **Ratificar a base de trabalho**. Revisar constituição, plano, riscos e critérios de avanço; registrar aceite e ressalvas. | docs/planejamento/decisoes/D-001-governanca.md | Aceite explícito; nada marcado aprovado apenas por ter sido gerado por IA. | Responsável; apoio ChatGPT Pro / P | S00-T02, S00-T03, S00-T04, S00-T05 | BLOQUEADA |

### Evidências e pendências

**S00-T01:** Base publicada na branch de trabalho; checkout e validação do commit de entrada executados.; https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842; docs/qualidade/evidencias/SPECKIT-CI.json

**S00-T02:** CLI oficial fixada executada; templates/comandos conferidos e constituição preservada. Ambiente: GitHub-hosted, não host do MVP.; https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842; docs/qualidade/evidencias/SPECKIT-CI.json

**S00-T03:** Minuta de constituição e processo versionada; ratificação humana continua em S00-T06.; https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842; docs/qualidade/evidencias/SPECKIT-CI.json

**S00-T04:** Backlog 10/60, modelos e visões publicados e verificados; acompanhamento adicional por issues não altera os contratos.; https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/37884957842; docs/qualidade/evidencias/SPECKIT-CI.json

**S00-T05:** Inventário e coletor preparados; não há sessão de execução na máquina alvo.

**S00-T06:** Execução autorizada pelo responsável; ratificação integral e inventário local ainda pendentes.


## S01 — Ideação e Business Model Canvas

**Objetivo:** Definir o problema, o público e a proposta de valor antes de escolher a solução completa.

**Critério de saída:** Problema e proposta de valor coerentes; BMC v1 revisado; hipóteses separadas de evidências reais.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S01-T01 | **Delimitar problema e público**. Caracterizar barreiras de custo, equipamentos, deslocamento e formação; distinguir relatos e hipóteses. | docs/descoberta/problema-publico.md | Problema delimitado, beneficiários identificados e fontes/hipóteses explícitas. | ChatGPT Pro; revisão do responsável / P | S00-T06 | A_FAZER |
| S01-T02 | **Mapear jornadas e proto-personas**. Modelar aluno com celular, aluno com computador, professor e organizador sem pressupor web/mobile. | docs/descoberta/jornadas.md | Jornada inclui aprender, programar, testar e competir; proto-personas não são apresentadas como pesquisa de campo. | ChatGPT Pro; revisão do responsável / M | S01-T01 | A_FAZER |
| S01-T03 | **Pesquisar referências e alternativas**. Comparar competição física, motores virtuais e plataformas educacionais com fontes e limitações. | docs/descoberta/benchmark.md | Comparação citada e datada, com critérios e limitações; Robocode permanece hipótese técnica até o spike. | ChatGPT Pro; revisão do responsável / M | S01-T01 | A_FAZER |
| S01-T04 | **Convergir a ideação e o corte do MVP**. Priorizar valor pedagógico, inclusão, esforço e risco; escolher um recorte e registrar exclusões. | docs/descoberta/ideacao-priorizacao.md | Uma proposta de MVP e lista explícita do que ficará para depois. | ChatGPT Pro; revisão do responsável / M | S01-T02, S01-T03 | A_FAZER |
| S01-T05 | **Construir o BMC v1**. Preencher nove blocos; distinguir estudante beneficiário, instituição apoiadora e sustentabilidade. | docs/negocio/bmc-v1.md | Nove blocos coerentes; apoio institucional e financiamento são hipóteses, não compromissos; sem receita fictícia. | ChatGPT Pro; revisão do responsável / M | S01-T04 | A_FAZER |
| S01-T06 | **Planejar e registrar validação inicial**. Definir hipóteses, perguntas e critérios; incorporar entrevistas somente após realização real. | docs/descoberta/hipoteses-validacao.md | Registro de validado, refutado ou não testado; decisão de prosseguir consciente das incertezas. | ChatGPT Pro e responsável / M | S01-T05 | A_FAZER |

### Evidências e pendências


## S02 — Projeto, desenho pedagógico e pitch

**Objetivo:** Transformar a ideia em um projeto institucional executável e comunicável.

**Critério de saída:** Projeto v1 e pitch v1 alinhados ao BMC, ao público e ao recorte do MVP; sem resultados ou parcerias inventados.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S02-T01 | **Redigir o termo de abertura e o projeto**. Consolidar justificativa, objetivos, beneficiários, entregas, escopo e sucesso; não presumir enquadramento institucional. | docs/projeto/projeto-v1.md | Objetivos verificáveis e limites claros; projeto não se confunde com especificação técnica. | ChatGPT Pro; revisão do responsável / M | S01-T06 | A_FAZER |
| S02-T02 | **Planejar entregas, recursos e custos**. Organizar EAP e categorias de custo; não confundir hospedagem própria com custo zero. | docs/projeto/entregas-recursos-custos.md | Custos distinguem valores levantados e estimativas; capacidade da máquina ainda não é promessa. | ChatGPT Pro; revisão do responsável / M | S02-T01, S00-T05 | A_FAZER |
| S02-T03 | **Definir a trilha pedagógica**. Planejar lógica, exemplos, prática, competição e avaliação além do ranking. | docs/projeto/plano-pedagogico.md | Participação não depende de o aluno já ter cursado desenvolvimento web/mobile; avaliação não se limita ao ranking. | ChatGPT Pro; revisão do responsável / M | S02-T01 | A_FAZER |
| S02-T04 | **Definir governança e proteção dos participantes**. Estabelecer papéis, decisões, riscos, dados mínimos e revisões institucionais necessárias. | docs/projeto/governanca-riscos.md | Responsáveis e aprovações identificados; dados reais não entram no repositório público. | ChatGPT Pro; revisão do responsável / M | S02-T01 | A_FAZER |
| S02-T05 | **Criar o pitch v1**. Produzir narrativa de 60 segundos, roteiro de 3 minutos e estrutura de 8–10 slides. | docs/pitch/pitch-v1.md | Narrativa consistente; promessas técnicas e impacto ainda não medido identificados como proposta. | ChatGPT Pro; revisão do responsável / M | S02-T02, S02-T03, S02-T04 | A_FAZER |
| S02-T06 | **Revisar a coerência do conjunto**. Conferir BMC, projeto, pitch e prioridades; registrar briefing para requisitos. | docs/projeto/revisao-v1.md | Nenhuma funcionalidade prometida no pitch fora do MVP sem indicação de evolução futura. | ChatGPT Pro; revisão do responsável / P | S02-T05 | A_FAZER |

### Evidências e pendências


## S03 — Requisitos, regras e experiência de uso

**Objetivo:** Definir o que o MVP deve fazer e como será aceito.

**Critério de saída:** RF, RNF, restrições, regras e histórias rastreáveis; jornadas móveis revisadas; ausência de ambiguidades críticas.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S03-T01 | **Especificar requisitos funcionais**. Especificar acesso, robôs, versões, treino, inscrições, competição, resultados e administração. | docs/requisitos/RF.md | Cada RF tem ID, ator, comportamento, condições e critério de aceite. | ChatGPT Pro; revisão do responsável / M | S02-T06 | A_FAZER |
| S03-T02 | **Especificar RNF e restrições**. Definir metas e métodos de segurança, acessibilidade, desempenho, operação e limites do piloto. | docs/requisitos/RNF-RES.md | Metas têm método de medição; valores ainda não acordados aparecem como pendentes, não como garantias. | ChatGPT Pro; revisão do responsável / M | S03-T01 | A_FAZER |
| S03-T03 | **Especificar regras da competição**. Definir formato, pontuação, desempates, prazos, congelamento de versões, falhas e reexecuções. | docs/requisitos/RN.md | Regras testáveis, sem ambiguidade de pontuação e sem permitir trocar código após o fechamento. | ChatGPT Pro; revisão do responsável / M | S03-T01 | A_FAZER |
| S03-T04 | **Validar os fluxos móveis**. Projetar e validar onboarding, autoria, salvar, testar, inscrever, assistir e consultar resultados. | docs/ux/fluxos-mobile.md | Estudante consegue percorrer a jornada completa; espectador não é confundido com participante. | ChatGPT Pro e responsável / M | S03-T01, S03-T03 | A_FAZER |
| S03-T05 | **Consolidar especificações com Spec Kit**. Criar histórias e aceites por feature; R4 somente com justificativa e reconciliação. | specs/<feature>/spec.md; docs/requisitos/matriz-rastreabilidade.md | Uma única baseline; R4, se usado, tem entrada/versão/saída registradas e não cria catálogo concorrente. | ChatGPT Pro; Codex/R4 somente com escalada / G | S03-T02, S03-T03, S03-T04 | A_FAZER |
| S03-T06 | **Auditar e aprovar a baseline**. Aplicar checklist/analyze, eliminar conflitos críticos e revisar rastreabilidade e escopo. | docs/requisitos/revisao-baseline-v1.md | RF/RNF/RN → história → aceite; bloqueios críticos resolvidos antes da arquitetura final. | ChatGPT Pro; aceite do responsável / M | S03-T05 | A_FAZER |

### Evidências e pendências


## S04 — Arquitetura e provas de viabilidade

**Objetivo:** Reduzir os riscos de motor, autoria móvel, isolamento e hospedagem antes da construção principal.

**Critério de saída:** Batalha real de referência executada, autoria móvel escolhida, isolamento validado no limite do experimento e arquitetura registrada em ADRs.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S04-T01 | **Comparar e escolher a arquitetura candidata**. Comparar interface, API, banco, fila, adaptador e executor antes de fixar tecnologias. | docs/arquitetura/ADR-001-stack.md | Decisões justificadas; uma única máquina física não significa um único processo com todos os privilégios. | ChatGPT Pro / M | S03-T06 | A_FAZER |
| S04-T02 | **Executar spike do Tank Royale**. Executar batalha real de referência e capturar resultado usando interface e versão verificadas. | spikes/tank-royale/; docs/arquitetura/spike-motor.md | Log e resultado reais; mocks isolados; licenças e interface efetiva verificadas. | ChatGPT Pro; Codex se pesado / G | S04-T01 | A_FAZER |
| S04-T03 | **Executar spike de autoria pelo celular**. Comparar autoria textual orientada, blocos ou linguagem restrita e escolher uma abordagem. | spikes/autoria-mobile/; docs/arquitetura/ADR-002-autoria.md | Teste em celular; alteração do comportamento do robô demonstrada; parametrizar aparência não conta como programar. | ChatGPT Pro; Codex se pesado; responsável no celular / G | S04-T01 | A_FAZER |
| S04-T04 | **Validar a estratégia de isolamento**. Modelar ameaças e testar limites de CPU, memória, rede, arquivos e controle de execução. | docs/arquitetura/ameacas-sandbox.md; spikes/isolamento/ | Tentativas controladas de exceder recursos/acessar ativos proibidos registradas; limitações conhecidas; sem exposição pública nesta fase. | ChatGPT Pro; Codex se pesado / G | S04-T02, S04-T03 | A_FAZER |
| S04-T05 | **Definir a topologia de hospedagem própria**. Definir ambiente segregado, serviços privados, acesso, backup e implantação reversível. | docs/arquitetura/ADR-003-hospedagem.md | Plano executável e sanitizado; acesso remoto ainda condicionado aos testes e aprovação. | ChatGPT Pro e responsável / M | S04-T01, S00-T05 | A_FAZER |
| S04-T06 | **Fechar arquitetura e plano técnico**. Consolidar decisões sustentadas pelos spikes e detalhar contratos, dados e tarefas. | specs/<feature>/plan.md; specs/<feature>/tasks.md; docs/arquitetura/visao.md | Spikes sustentam decisões; tarefas técnicas mapeadas ao backlog; riscos bloqueantes tratados. | ChatGPT Pro; revisão do responsável / G | S04-T02, S04-T03, S04-T04, S04-T05 | A_FAZER |

### Evidências e pendências


## S05 — Fundação da plataforma e jornada do participante

**Objetivo:** Entregar um incremento navegável com acesso, autoria persistida e foco móvel.

**Critério de saída:** Participante convidado entra pelo celular, recebe orientação, cria um projeto de robô e salva versões; regras de acesso cobertas por testes.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S05-T01 | **Criar a base de código e testes**. Estruturar aplicação, dependências, padrões, migrações, testes e CI. | apps/; packages/; tests/; .github/workflows/ | Build/lint/testes executados e evidências anexadas; CI sem segredos desnecessários. | ChatGPT Pro; Codex se pesado / M | S04-T06 | A_FAZER |
| S05-T02 | **Implementar acesso e papéis**. Implementar participante, professor e administrador com privilégio mínimo. | apps/api/; tests/auth/ | Testes positivos e negativos de autorização; participante não acessa dados de outro. | ChatGPT Pro; Codex se pesado / M | S05-T01 | A_FAZER |
| S05-T03 | **Implementar a interface responsiva**. Entregar navegação e telas-base acessíveis em computador e celular. | apps/web/; tests/ui/ | Navegação usável por toque e teclado, inclusive em tela pequena; conteúdo essencial legível. | ChatGPT Pro; Codex se pesado / M | S05-T01 | A_FAZER |
| S05-T04 | **Implementar projetos e versões de robôs**. Criar, editar, salvar e recuperar projetos com histórico e propriedade verificáveis. | apps/api/robots/; tests/robots/ | Dados persistem após nova sessão; dono/permissões corretos; histórico de versão verificável. | ChatGPT Pro; Codex se pesado / M | S05-T02, S05-T03 | A_FAZER |
| S05-T05 | **Implementar onboarding e exemplos**. Orientar primeiro robô e primeiras alterações sem pressupor formação em web/mobile. | apps/web/onboarding/; docs/pedagogia/exemplos.md | Aluno acompanha um exemplo, modifica estratégia e salva; telas indicam limites atuais de treino. | ChatGPT Pro; revisão pedagógica do responsável / M | S05-T04 | A_FAZER |
| S05-T06 | **Testar o incremento da sprint**. Verificar acesso, persistência, mensagens, navegação e acessibilidade do incremento. | docs/qualidade/evidencias/S05.md | Caminho feliz e erros críticos testados; ainda não apresentar este incremento como competição funcional. | ChatGPT Pro; responsável nos testes reais / M | S05-T05 | A_FAZER |

### Evidências e pendências


## S06 — Programação, treino e integração real

**Objetivo:** Completar a primeira fatia vertical: programar no celular, executar no servidor e observar resultado real.

**Critério de saída:** Jornada ponta a ponta demonstrada com dois robôs e evidência do motor real, sem depender do processamento do celular.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S06-T01 | **Implementar o editor escolhido**. Implementar autoria de lógica, exemplos, validação e erros recuperáveis. | apps/web/editor/; tests/editor/ | Lógica editável por toque/teclado; erros recuperáveis; formato de autoria documentado. | ChatGPT Pro; Codex se pesado / G | S05-T06 | A_FAZER |
| S06-T02 | **Implementar validação e limites de submissão**. Validar propriedade, formato, tamanho, integridade e política antes da execução. | apps/api/submissions/; tests/submissions/ | Casos malformados e não autorizados rejeitados; nenhum caminho de bypass conhecido. | ChatGPT Pro; Codex se pesado / G | S06-T01 | A_FAZER |
| S06-T03 | **Implementar fila e executor isolado**. Implementar jobs persistentes, limites de recursos, timeout, cancelamento e recuperação. | services/runner/; tests/runner/ | Bot travado não bloqueia indefinidamente a fila; acesso a ativos proibidos negado; jobs têm identidade e versão. | ChatGPT Pro; Codex indicado para implementação pesada / G | S06-T02, S04-T04 | A_FAZER |
| S06-T04 | **Integrar o motor e capturar resultados**. Controlar batalhas reais e vincular resultados às versões e jobs corretos. | services/engine-adapter/; tests/engine/ | Resultado é do motor fixado e corresponde às versões submetidas; mensagens não confiáveis não alteram placar. | ChatGPT Pro; Codex indicado para implementação pesada / G | S06-T03 | A_FAZER |
| S06-T05 | **Implementar treino e observação**. Solicitar treino, acompanhar estado, tratar falhas e recuperar resultados após desconexão. | apps/web/training/; tests/training/ | Participante solicita treino, acompanha e consulta resultado após reconectar; sem prometer renderizador próprio completo. | ChatGPT Pro; Codex se pesado / M | S06-T04 | A_FAZER |
| S06-T06 | **Demonstrar a fatia vertical no celular**. Demonstrar criação, alteração de lógica, salvamento e treino com motor real no servidor. | docs/qualidade/evidencias/S06.md | Vídeo/logs sanitizados ou evidência equivalente; mudança de código afeta a estratégia; falha de bot testada. | ChatGPT Pro e responsável no dispositivo real / G | S06-T05 | A_FAZER |

### Evidências e pendências


## S07 — Competição, pontuação e administração

**Objetivo:** Converter o ambiente de treino em uma RoboCopa administrável e auditável.

**Critério de saída:** Mini-competição completa com inscrições, versões congeladas, partidas, pontuação e ranking correto, incluindo tratamento de falhas.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S07-T01 | **Implementar competição e inscrições**. Implementar evento, elegibilidade, inscrições, prazos e estados. | apps/api/competitions/; tests/competitions/ | Estados e prazos respeitados; inscrições inválidas negadas. | ChatGPT Pro; Codex se pesado / M | S06-T06 | A_FAZER |
| S07-T02 | **Congelar as versões inscritas**. Vincular cada inscrição a versão imutável e regulamento aplicável. | apps/api/entries/; tests/entries/ | Edição posterior do projeto não altera robô já congelado; autoria e hash/ID auditáveis. | ChatGPT Pro; Codex se pesado / M | S07-T01 | A_FAZER |
| S07-T03 | **Implementar agendamento de partidas**. Gerar confrontos e controlar fila, pausas, falhas e reexecuções autorizadas. | apps/api/scheduling/; tests/scheduling/ | Partidas previstas executadas uma vez em termos de efeito; retries não duplicam pontuação. | ChatGPT Pro; Codex se pesado / G | S07-T02 | A_FAZER |
| S07-T04 | **Implementar pontuação e desempates**. Calcular classificação a partir de resultados e regras versionadas. | packages/scoring/; tests/scoring/ | Pontuação e desempates reproduzem fixtures; falhas/desclassificações seguem regulamento. | ChatGPT Pro; Codex se pesado / M | S07-T03 | A_FAZER |
| S07-T05 | **Implementar painel e resultados**. Entregar ranking, histórico, painel do organizador e trilha de ações administrativas. | apps/web/competition/; apps/web/admin/; tests/admin/ | Permissões e trilha auditável; estudante vê resultado compreensível e não ganha acesso administrativo. | ChatGPT Pro; Codex se pesado / M | S07-T04 | A_FAZER |
| S07-T06 | **Ensaiar uma competição completa**. Executar evento de teste incluindo empate, timeout, falha e retomada. | docs/qualidade/evidencias/S07.md | Do cadastro ao ranking final com evidência real; conjunto de regressão preservado. | ChatGPT Pro e responsável / G | S07-T05 | A_FAZER |

### Evidências e pendências


## S08 — Qualidade, segurança e implantação local

**Objetivo:** Preparar a release candidata no ambiente de hospedagem real, com acesso controlado.

**Critério de saída:** Release candidata instalada e recuperável; limites medidos; sem defeitos críticos conhecidos; nenhuma execução pública de código arbitrário antes do gate de segurança.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S08-T01 | **Executar a regressão completa**. Executar testes unitários, integração, contratos e ponta a ponta no commit candidato. | tests/; docs/qualidade/evidencias/S08-regressao.md | Resultados realmente executados, ambiente e commit registrados; testes não executados ficam pendentes. | ChatGPT Pro; Codex para suítes pesadas / G | S07-T06 | A_FAZER |
| S08-T02 | **Testar segurança e abuso**. Testar autorização, sandbox, entradas malformadas, abuso de fila e limites de recursos. | tests/security/; docs/qualidade/evidencias/S08-seguranca.md | Sem falha crítica/alta conhecida no escopo liberado; controles de isolamento testados além do caminho feliz. | ChatGPT Pro; Codex para suítes pesadas / G | S08-T01 | A_FAZER |
| S08-T03 | **Medir carga e usabilidade móvel**. Medir capacidade, recursos, latência e comportamento em condições móveis definidas. | tests/load/; docs/qualidade/evidencias/S08-carga-mobile.md | Limites publicados correspondem à medição; logs distinguem latência web, espera em fila e tempo da partida. | ChatGPT Pro, responsável; Codex se pesado / G | S08-T01 | A_FAZER |
| S08-T04 | **Implantar na máquina de hospedagem**. Instalar serviços segregados, configurar acesso autorizado e identificar versão implantada. | infra/; docs/operacao/implantacao.md | Acesso aprovado validado; nenhum segredo no Git; versão implantada identificável; rollback definido. | Responsável no host; apoio ChatGPT Pro/Codex / G | S08-T02, S08-T03, S04-T05 | A_FAZER |
| S08-T05 | **Testar recuperação e operação**. Testar backup, restauração, reinício, retomada/cancelamento de jobs e rollback. | docs/operacao/runbook.md; docs/qualidade/evidencias/S08-recuperacao.md | Restauração e rollback demonstrados em teste; limites de disponibilidade explícitos, não promessa de SLA. | Responsável no host; apoio ChatGPT Pro / M | S08-T04 | A_FAZER |
| S08-T06 | **Aprovar a release candidata**. Revisar resultados e riscos residuais; decidir liberar ou bloquear piloto. | docs/qualidade/RC-aceite.md | Responsável aceita os riscos residuais; falhas bloqueantes impedem liberação; toda ressalva tem dono e tratamento. | Responsável; apoio ChatGPT Pro / M | S08-T05 | A_FAZER |

### Evidências e pendências


## S09 — Piloto, homologação e entrega do MVP

**Objetivo:** Validar o produto com participantes reais e consolidar a entrega e a comunicação do projeto.

**Critério de saída:** Piloto documentado, aceite do responsável e release v0.1.0 rastreável, sem confundir entrega técnica com impacto educacional já comprovado.

| ID | Tarefa | Saída planejada | Critério de aceite | Executor / porte | Dependências | Estado |
|---|---|---|---|---|---|---|
| S09-T01 | **Preparar e realizar o piloto**. Realizar experiência com convidados reais, orientação, suporte e registro sanitizado. | docs/piloto/plano-piloto.md; docs/piloto/registro-sanitizado.md | Participantes reais completam jornada; dados identificáveis permanecem fora do repositório público. | Responsável e participantes; apoio ChatGPT Pro / G | S08-T06 | A_FAZER |
| S09-T02 | **Medir experiência e indícios de aprendizagem**. Analisar participação móvel, dificuldades e avaliação pedagógica exploratória sem inferir causalidade. | docs/piloto/avaliacao.md | Indicadores têm denominador e método; observação, opinião e evidência técnica são distinguidas. | ChatGPT Pro e responsável / M | S09-T01 | A_FAZER |
| S09-T03 | **Corrigir problemas prioritários**. Corrigir bloqueios e regressões; encaminhar melhorias não essenciais ao pós-MVP. | docs/piloto/triagem.md; tests/regression/ | Defeitos críticos corrigidos e retestados; escopo não cresce silenciosamente. | ChatGPT Pro; Codex se pesado / G | S09-T02 | A_FAZER |
| S09-T04 | **Homologar requisitos e aceite do MVP**. Conferir requisitos, testes, evidências e aceite do responsável. | docs/qualidade/HOMOLOGACAO-MVP.md | Todos os critérios obrigatórios atendidos ou entrega bloqueada; exceções não escondem requisitos centrais. | Responsável; apoio ChatGPT Pro / M | S09-T03 | A_FAZER |
| S09-T05 | **Atualizar BMC, projeto e pitch final**. Incorporar aprendizados e resultados observados, distinguindo limitações e próximos passos. | docs/negocio/bmc-v2.md; docs/projeto/projeto-v2.md; docs/pitch/pitch-final.md | Pitch distingue resultados obtidos, limitações e próximos passos; nenhuma métrica inventada. | ChatGPT Pro; revisão do responsável / M | S09-T02, S09-T04 | A_FAZER |
| S09-T06 | **Publicar a entrega e o próximo backlog**. Publicar release v0.1.0, notas, guias e prioridades pós-MVP após homologação. | CHANGELOG.md; docs/operacao/; docs/pedagogia/; docs/planejamento/pos-mvp.md | Commit/tag identificáveis, restauração documentada e backlog priorizado; publicação autorizada e sem dados pessoais. | ChatGPT Pro; autorização do responsável / M | S09-T04, S09-T05 | A_FAZER |

### Evidências e pendências
