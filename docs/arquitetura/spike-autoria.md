# S04-T03 — Autoria responsiva com execução real

**Resultado técnico:** PASS no laboratório de CI; teste físico e escolha pedagógica definitiva pendentes. **Referência:** feature 003 do Spec Kit. Trabalho conduzido pelo ChatGPT Pro; Codex e R4 não foram usados.

## Pergunta e resposta

É possível editar uma estratégia em uma interface adaptada a tela pequena, salvar um rascunho, receber erro por linha e executar a versão corrente no Tank Royale, observando mudança de comportamento real?

**Sim, no fluxo testado em Chromium com emulação móvel.** O mesmo robô Aprendiz foi gerado a partir de duas estratégias diferentes, enviadas pelo editor ao servidor local, executadas no motor oficial e observadas nos replays. Isso não substitui validação com um telefone físico, teclado virtual, conectividade móvel ou estudantes reais.

## Entrega

O protótipo contém editor textual guiado em português (RoboDSL 0.1), exemplos, botões de inserção, rascunho salvo neste navegador, validação sintática, treino real e visualização resumida de posições do replay. A linguagem admite eventos, ações ordenadas e condições com alternativas; não se limita a configurar a aparência do robô. A comparação entre texto completo, blocos e linguagem restrita consta na ADR-002 e é uma análise técnica, não pesquisa comparativa com participantes.

O parser Python produz AST com limites e hash; um template conhecido gera Java somente com ações e números validados. A versão do programa identifica o robô e os resultados. O wrapper executa Aprendiz × Walls por três rounds, sem tocar na infraestrutura PostgreSQL já existente. O servidor é apenas um laboratório do responsável em 127.0.0.1:18081, não o backend final do MVP.

## Resultados do lote de referência

[Run 38009658981](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38009658981), fonte `6c101094b75f212de5f65719234fd74614f29e51`. Os dois treinos foram disparados por cliques no editor em viewport 390 × 844 com toque emulado.

| Programa do Aprendiz | Rounds | Pontos Aprendiz | Pontos Walls | Velocidade absoluta média | Fração dos turnos em movimento |
|---|---:|---:|---:|---:|---:|
| Sentinela (parado) | 3 | 44 | 449 | 0,0000 | 0,00% |
| Explorador (movimento e giro) | 3 | 124 | 243 | 5,7989 | 97,77% |

Velocidade em unidades do motor por turno. O cálculo usa os ticks oficiais em que Aprendiz aparece no replay, não uma animação inventada. A sentinela registrou 1507 ticks; o explorador, 2462. A alteração de código gerou hash diferente e movimento diferente. **Não se conclui que o explorador seja superior a outras estratégias:** são duas observações, com condições e posições não fixadas; o teste não é um ensaio estatístico.

O artifact foi baixado e conferido fora do runner: SHA-256 do ZIP, CRC, descompressão gzip, leitura de todos os eventos JSON, identidades, fins dos três rounds, concordância entre o placar final do replay e os campos exportados, recálculo das métricas de movimento e hashes dos replays. Duas execuções tiveram onze controles Docker efetivos aprovados e limpeza confirmada nos manifestos.

## Verificações de interface

Viewports 360 × 800, 390 × 844 e 1280 × 900. Confirmados: ausência de rolagem horizontal, editor com fonte de ao menos 16px, botões com altura mínima de 44px, recuperação do rascunho após recarga, erro preservando texto, verificação do código, reprodução/pausa e ausência de erros JavaScript. As capturas efetivas do desktop e do explorador em 390px foram inspecionadas visualmente.

O replay exibido é uma **amostra das posições reais** a cada oito ticks; não mostra tiros, todos os eventos ou transmissão ao vivo. O resultado e as métricas são também texto. Essas verificações não são auditoria integral de WCAG, leitor de tela ou uso em hardware móvel.

## Testes e rastreabilidade

No lote documentado: 97 testes unitários aprovados (27 planejamento/inventário, 13 infraestrutura, 23 motor e 34 novos de linguagem/HTTP/replay), estrutura nativa do Spec Kit e dois fluxos com motor real. O teste HTTP unitário usa executor falso explicitamente identificado; o teste de navegador usa o executor verdadeiro. Uma regressão adicional cobre token HTTP não ASCII; seu resultado é registrado no run posterior, sem reescrever os números históricos deste lote.

Evidência estruturada: [AUTORIA-MOBILE-CI.json](../qualidade/evidencias/AUTORIA-MOBILE-CI.json). Artifact 11652628410, SHA-256 `2ec0e06d8acf02d689e287d183e73b4ef298422a252ae31b56bb0248f03aad23`, retenção informada até 09/11/2026 UTC. Cópia disponibilizada na conversa; novas execuções não substituem estes placares históricos.

## Pendências para concluir a tarefa macro

A reprodução visual inicial do editor no PC foi informada pelo responsável e registrada em `docs/qualidade/evidencias/AUTORIA-MOBILE-HOST.md`: Sentinela, três rounds, Aprendiz 536 × Walls 226, velocidade média 0. Não houve inspeção independente dos arquivos locais. Ainda faltam execução comparativa do Explorador no PC, avaliação em aparelho físico e ratificação pedagógica. A tarefa S04-T03 não está concluída. O backlog macro não é fechado por esta evidência; os avanços técnicos são detalhados em `specs/003-autoria-mobile/tasks.md`. Os gates S03/S04-T01 e a validação de isolamento S04-T04 não foram aprovados por inferência.

Nenhum túnel, firewall, roteador, VHDX ou conta foi alterado. O servidor local tem acesso à CLI Docker e não pode ser disponibilizado ao público como está. O telefone não acessa o PC usando seu próprio 127.0.0.1: a conexão controlada para teste físico precisa de definição separada.

[Executar no computador hospedeiro](../../spikes/autoria-mobile/README.md) · [ADR-002 candidata](ADR-002-autoria.md) · [Tarefas](../../specs/003-autoria-mobile/tasks.md)
