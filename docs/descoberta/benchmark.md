# Referências e alternativas

**Versão:** 0.1.0 · **Data da consulta:** 2026-10-09 · **Tarefa:** S01-T03.
**Estado:** pesquisa documental preparatória. Não houve instalação comparativa ou teste com estudantes nesta tarefa.

## Critérios

Avaliar separadamente: autoria de estratégia, necessidade de instalação pelo participante, integração com servidor, experiência móvel, administração de competição, isolamento de código e finalidade pedagógica. Um motor de batalha não é automaticamente uma plataforma escolar completa; um editor visual não é um motor de competição.

| Referência/alternativa | Evidência documental | Utilidade para a RoboCopa | Limitação e trabalho necessário |
|---|---|---|---|
| Robocode clássico | O projeto oficial apresenta o ambiente de programação de robôs de batalha [1] | Referência de atividade baseada em estratégia e programação | Não tratar sua experiência local como uma jornada móvel já pronta; integração teria de ser avaliada |
| Robocode Tank Royale | Arquitetura com servidor e clientes, comunicação WebSocket, bots e papéis de controle/observação; diferenças em relação ao clássico [2] | Candidato principal a motor das batalhas no servidor | Autoria, acesso, persistência, inscrições e experiência móvel são responsabilidades adicionais da plataforma |
| Blockly | Biblioteca para construir editores visuais baseados em blocos [3] | Candidato a componente de autoria de lógica para iniciantes | Não entrega sozinho o jogo, a semântica de execução, o servidor ou o regulamento; toque/usabilidade precisam de teste |
| Editor textual orientado | Alternativa de projeto, não produto avaliado nesta pesquisa | Pode permitir exemplos pequenos, estrutura reduzida e correspondência direta com a lógica | Digitação, seleção, indentação e mensagens em tela pequena são riscos a medir |
| Competição com robôs físicos | Referência conceitual trazida pelo idealizador, sem levantamento de preços ou evento específico nesta execução | Mantém experiências de construção e interação material que a simulação não substitui | Comparação de custo e acesso exige recorte real; não se pode concluir superioridade universal da alternativa virtual |

## Achado técnico prioritário

A documentação do Tank Royale esclarece que o ambiente não fornece, por si, limitação de recursos como CPU e memória dos processos dos bots [2]. Assim, escolher o motor não resolve o problema de executar código não confiável na máquina de uso pessoal. O executor, seus limites e sua separação dos dados da plataforma precisam ser projetados e testados em S04-T04 e S06-T03.

A comunicação por WebSocket também não entrega automaticamente uma interface móvel completa. Será necessário decidir como o participante produz a estratégia e como a plataforma controla a execução, associa resultados a versões e apresenta o acompanhamento [2].

## Recomendação candidata

Manter Tank Royale como hipótese de motor para o experimento técnico, sem fechar a arquitetura antes de uma batalha real de referência. Comparar duas opções de autoria no celular: texto orientado com superfície pequena e blocos com semântica restrita. Selecionar somente uma para o MVP após observar criação e alteração de lógica por participantes representativos.

Não desenvolver simultaneamente um motor próprio, dois editores completos e aplicativos nativos. Esse recorte aumenta o trabalho antes de demonstrar a proposta central. A recomendação é uma decisão de escopo, não resultado de benchmark de desempenho.

## Lacunas e licenças

Não foram avaliados exaustivamente todos os produtos educacionais ou organizadores de torneios existentes; não há base para alegar pioneirismo ou ausência de concorrentes. A licença de cada componente e de seus recursos deve ser conferida no repositório e na versão selecionada antes de incorporação. A licença do site de documentação não deve ser confundida com a licença de todo o código do motor.

O Spec Kit já incorporado tem sua licença preservada em `licenses/spec-kit-MIT.txt` e identificação em `THIRD-PARTY-NOTICES.md`.

## Fontes primárias

[1] Robocode, site oficial: https://robocode.sourceforge.io/

[2] Robocode Tank Royale, documentação de arquitetura e diferenças: https://robocode.dev/articles/tank-royale.html

[3] Blockly, documentação oficial: https://docs.blockly.com/guides/get-started/what-is-blockly/

As conclusões de usabilidade, capacidade, aprendizagem e adequação ao campus permanecem não testadas.
