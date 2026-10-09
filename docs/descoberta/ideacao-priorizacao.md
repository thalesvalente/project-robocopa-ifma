# Ideação, alternativas e recorte do MVP

**Versão:** 0.1.0 · **Data:** 2026-10-09 · **Tarefa:** S01-T04.
**Estado:** proposta de convergência, sujeita à revisão do responsável. Fundamentação: problema relatado, jornadas propostas e pesquisa documental; sem pesquisa de campo concluída.

## Alternativas consideradas

| Alternativa | Vantagem esperada | Compromisso ou risco | Decisão proposta |
|---|---|---|---|
| Evento somente com robôs físicos | Experiência material de construção e sensores | Não atende ao objetivo inicial de dispensar kit individual | Não é o MVP deste projeto; pode coexistir no futuro |
| Ambiente virtual instalado em cada computador | Uso de ferramentas existentes e processamento distribuído | Não resolve participação completa pelo celular e exige preparação local | Não adotar como único canal |
| Aplicativo apenas para acompanhar resultados | Menor escopo de interação | Exclui autoria e submissão pelo celular, requisito central do idealizador | Insuficiente como MVP |
| Plataforma web responsiva com execução central | Um fluxo comum para celular e computador; versões e resultados centralizados | Exige executor seguro, conectividade e operação do host | Alternativa escolhida como direção de trabalho |
| Aplicativos nativos separados mais servidor | Possível experiência específica por plataforma | Mais código, distribuição e testes antes de provar o valor central | Adiar |

## Proposta convergente

Uma plataforma de acesso controlado, hospedada na máquina do responsável, em que um estudante usa exemplos orientados para programar a estratégia de um robô virtual, salva versões, realiza treinos, inscreve uma versão e consulta os resultados. O professor conduz a aprendizagem e o organizador opera um evento inicial.

O primeiro marco técnico útil é executar essa jornada com motor real e autoria pelo celular. Um site com cadastro, telas bonitas e ranking alimentado manualmente ainda não demonstra a proposta.

## Priorização por necessidade

**Obrigatório para o primeiro MVP:** acesso e papéis mínimos; orientação inicial; autoria de lógica no celular e computador; persistência e versões; validação; treino com motor real; executor isolado; inscrição vinculada a versão congelada; um formato de competição; pontuação verificável; administração essencial; testes e recuperação da hospedagem.

**Condicionado à prova de valor e esforço:** instalação PWA; replay navegável; exportação de resultados; visualização avançada da batalha. Acompanhamento compreensível é necessário, mas não exige prometer todos esses recursos na primeira versão.

**Fora do primeiro MVP:** múltiplas linguagens e editores em paralelo; aplicativo nativo independente; colaboração simultânea; mercado de robôs; pagamentos; rede social; geração de estratégia por IA como dependência; inscrições públicas ilimitadas; múltiplos servidores; integração com hardware físico.

## Decisões ainda abertas

A autoria poderá usar texto orientado ou blocos; ambas precisam expressar decisões/ações e permitir que a alteração afete o comportamento. O formato da competição e as regras serão definidos na S03. O motor será confirmado em experimento da S04. Não confundir direção de produto com seleção antecipada de framework, banco ou protocolo de dados interno.

## Regra de mudança de escopo

Para incluir uma funcionalidade, registrar: necessidade atendida, evidência, requisito afetado, custo de implementação/teste/operação, risco e impacto nas entregas obrigatórias. Na ausência de evidência, preservar a menor solução que permita o experimento. Não retirar autoria móvel, isolamento ou rastreabilidade para acomodar recursos secundários.

## Critério proposto de demonstração

Um participante altera a lógica no celular, confirma o salvamento de uma versão, executa treino no servidor, identifica a versão testada, inscreve-a e acompanha um resultado calculado a partir do motor. A demonstração deve incluir ao menos uma falha recuperável e comprovar que modificar o projeto depois do fechamento não muda a versão inscrita. Esse critério ainda não foi executado.
