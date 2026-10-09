# Projeto RoboCopa IFMA — versão inicial

**Versão:** 1.0, minuta · **Data:** 2026-10-09 · **Tarefa:** S02-T01.
**Estado:** proposta para revisão do responsável; não representa aprovação institucional, concessão de recursos ou execução de piloto.

## 1. Identificação e síntese

A RoboCopa IFMA propõe uma experiência educacional de programação baseada em competição de robôs virtuais. O ponto de partida é o IFMA Campus Itapecuru-Mirim, com possibilidade de participação de outras escolas após validação técnica, pedagógica e operacional.

O MVP permitirá que o estudante acesse a plataforma pelo celular ou computador, compreenda um exemplo, programe a lógica de um robô, salve versões, realize treinos e inscreva uma versão em uma competição. As batalhas serão executadas em servidor hospedado na máquina do responsável, com isolamento do código dos participantes e classificação baseada nos resultados reais do motor selecionado.

## 2. Justificativa

O idealizador pretende reduzir barreiras associadas à aquisição de kits e ao deslocamento em atividades competitivas com robôs físicos. A alternativa virtual não substitui experiências de eletrônica, montagem e sensores, mas permite investigar uma forma de participação centrada em lógica e estratégia.

A autoria móvel é parte do problema educacional: não basta oferecer um aplicativo para acompanhar resultados quando o estudante também precisa programar e testar sem computador pessoal. Além disso, a participação não deve pressupor que o aluno já tenha cursado desenvolvimento web ou dispositivos móveis. Essas competências pertencem à construção da plataforma, não à entrada obrigatória do competidor.

Não há, nesta versão, evidência de impacto educacional, economia efetiva ou adesão do público. Essas hipóteses serão tratadas no piloto e não são apresentadas como resultados.

## 3. Objetivo geral

Desenvolver e validar um MVP de competição educacional de robôs virtuais, com autoria e participação pelo celular e computador, execução centralizada na máquina do responsável e operação rastreável e recuperável.

## 4. Objetivos específicos e verificação

| Objetivo | Como verificar |
|---|---|
| OE-01 — Viabilizar autoria móvel | Participante altera lógica, salva e solicita treino em dispositivo real |
| OE-02 — Relacionar código e comportamento | Versão executada identificável e resultado proveniente do motor real |
| OE-03 — Administrar competição íntegra | Inscrições, versões congeladas, confrontos, pontuação e desempates testados |
| OE-04 — Reduzir risco ao host pessoal | Isolamento e limites de execução avaliados por testes negativos e modelo de ameaças |
| OE-05 — Sustentar operação do piloto | Instalação, limites de capacidade, backup, restauração e rollback demonstrados |
| OE-06 — Avaliar a experiência inicial | Registro sanitizado das jornadas, dificuldades e explicações de estratégia |

## 5. Escopo do MVP

Inclui acesso por convite e papéis mínimos; interface responsiva; orientação inicial; uma abordagem de autoria; projetos e versões; validação; treino com motor real; executor isolado; inscrições; um formato de competição; congelamento de versões; resultados e administração essencial; testes, implantação própria e piloto controlado.

Exclui aplicativos nativos separados, múltiplas linguagens ou editores simultâneos, hardware físico, mercado de robôs, pagamentos, rede social, colaboração em tempo real e inscrição pública ilimitada. Geração de estratégias por IA não é dependência da atividade do estudante.

## 6. Público, participação e governança

O primeiro grupo será convidado pelo responsável e por mediadores a definir. Turmas, idades, quantidade e condições de acesso dependem de levantamento. Professores mediam atividades; o operador administra serviços; o organizador conduz o regulamento; o responsável aprova escopo e liberação. Acumulação de papéis é possível, mas suas tarefas e permissões devem permanecer distinguíveis.

Nenhuma escola, setor ou profissional é designado como parceiro ou colaborador confirmado apenas por esta minuta. O enquadramento como ação de ensino, extensão ou pesquisa será definido institucionalmente.

## 7. Método de desenvolvimento e execução

ChatGPT Pro é o ambiente principal para ideação, documentos, especificações, planejamento, revisão e implementação delimitada. Codex será usado somente em trabalho pesado ou no R4 quando justificado. O Spec Kit versionado no repositório apoia o fluxo por funcionalidade; backlog, tarefas técnicas, testes e commits mantêm rastreabilidade.

S00 prepara a base; S01 e S02 refinam proposta e projeto; S03 estabelece requisitos; S04 testa riscos de motor, autoria e isolamento; S05–S07 constroem incrementos; S08 verifica qualidade e operação; S09 realiza piloto e homologação. As sprints são ciclos por entrega, sem duração em semanas presumida.

## 8. Marcos de decisão

M1: problema e proposta revisados. M2: requisitos e regulamento verificáveis. M3: provas de viabilidade técnica concluídas. M4: jornada real de autoria e treino pelo celular. M5: competição completa ensaiada. M6: hospedagem testada e piloto autorizado. M7: MVP homologado e comunicação atualizada.

Produzir documentos de um marco não equivale a comprovar seus testes ou obter aceite humano.

## 9. Recursos e sustentabilidade

A hospedagem própria foi definida pelo responsável. CPU Core i9 e 128 GB de memória são informações relatadas, ainda sem inventário técnico nesta execução. Disponibilidade, armazenamento, conectividade, segregação e capacidade serão verificados antes de dimensionar o piloto. Recursos, custos e premissas estão em [entregas e custos](entregas-recursos-custos.md).

## 10. Critérios de encerramento

Requisitos obrigatórios atendidos; jornada móvel demonstrada; motor real integrado; competição e pontuação verificadas; ausência de falhas bloqueantes conhecidas no escopo liberado; restauração e rollback testados; piloto documentado; aceite do responsável. O conjunto proposto está em [aceite do MVP](../qualidade/ACEITE-MVP.md).

A entrega técnica poderá demonstrar viabilidade e dificuldades observadas. Alegações de impacto educacional exigem evidência e método compatíveis, além do funcionamento do software.
