# Feature 003 — Autoria móvel ligada ao motor real

**Rastreabilidade:** S04-T03. Experimento antecipado autorizado pelo responsável após reprodução de S04-T02 no host. A baseline S03 e a decisão definitiva de autoria não estão homologadas.

## US1 — Escrever lógica em tela pequena
Como participante em avaliação de protótipo, quero escrever eventos, ações e condições em português, com exemplos e erros de linha, sem precisar desenvolver uma página ou aplicativo.

Aceite: editor utilizável por teclado/toque, instruções com sintaxe documentada, rascunho salvo/recuperado neste navegador; erros não apagam o código; botões de 44px ou mais; ausência de overflow horizontal nos viewports testados. O teste em aparelho físico é aceite separado.

## US2 — Alterar a estratégia e executar no servidor
Como avaliador, quero enviar a versão atual da estratégia e observar uma batalha real, para verificar que a edição muda o comportamento do robô e não apenas sua aparência.

Aceite: linguagem restrita, sem eval/Java livre; compilador gera somente modelo fixo com números validados; hash do programa ligado ao resultado; três rounds oficiais Aprendiz × Walls; uma execução de cada vez; ambiente descartável sem rede, mounts ou credenciais da plataforma.

## US3 — Interpretar resultados reais
Como avaliador, quero consultar pontos e replay de movimento do motor, para comparar minhas hipóteses.

Aceite: resultado vem de BattleResults; replay tem eventos de início/fim e três rounds; placares/identidades coincidem; métricas de velocidade vêm dos ticks oficiais; amostra visual identificada como incompleta (não desenha tiros). Comparação de programas deve mostrar hash e movimento diferentes; não presumir que duas partidas medem superioridade ou aprendizado.

## Limites
Servidor temporário somente 127.0.0.1:18081; operação pelo responsável, sem contas/alunos, sem inscrição, sem internet pública, sem alterações do Compose/PostgreSQL. Emulação Chromium não equivale a smartphone físico. A linguagem candidata será ratificada após avaliação pedagógica. O protótipo não comprova sandbox de código hostil nem conformidade completa de acessibilidade.
