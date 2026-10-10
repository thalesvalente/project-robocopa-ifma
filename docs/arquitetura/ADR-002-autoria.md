# ADR-002 — Autoria pelo celular: candidato experimental

**Estado:** proposta para teste / S04-T03. Não é aprovação pedagógica nem da baseline completa.

## Comparação de abordagens

| Opção | Benefícios esperados | Custo/risco a validar | Destino nesta rodada |
|---|---|---|---|
| Texto completo Java/JavaScript | Linguagem de uso geral e maior expressividade | Mais sintaxe para digitar; execução arbitrária amplia fronteira de segurança | Não prototipada nesta rodada |
| Blocos visuais | Reduz certos erros de sintaxe e pode facilitar descoberta | Interações de arrastar, zoom, foco e acessibilidade exigem teste próprio em tela pequena | Alternativa preservada; não houve ensaio comparativo com usuários |
| Texto guiado em linguagem restrita | Vocabulário curto, eventos/condições e compilação controlada | Sintaxe nova; limites de expressividade; risco de transferir menos conhecimentos de linguagem geral | **Candidato prototipado: RoboDSL 0.1** |

A escolha é de experimento de baixo escopo; não foi obtida por pesquisa de campo nem comparação de desempenho pedagógico. Após teste físico com estudantes/professores, revisar a decisão antes do MVP.

## Semântica e escopo

“sempre” repete sua sequência a cada turno; “ao detectar” reage ao radar. Ações: velocidade, girar, canhao, atirar. Condições if/else com energia ou distancia; distancia só no evento de radar. Valores, tamanho, quantidade e profundidade são limitados. O aluno pode alterar ações, ordem, condições e limiares; não está apenas trocando cores.

O texto é analisado em AST e compilado por template conhecido. Não há eval, import, acesso a arquivo/rede, Java ou JavaScript livre. A imagem recebe apenas o código gerado pelo compilador local. Isso reduz superfícies, mas não constitui prova completa de sandbox.

## Interface e execução

Editor HTML/textarea com fonte 16px, botões >=44px, teclado/toque, exemplos, inserção de trechos, rascunho neste navegador e erro por linha. Testar envia a versão corrente para o host; Battle Runner 1.4.0 executa Aprendiz × Walls por três rounds. A versão/hash consta no resultado. O canvas reproduz amostra das posições do replay oficial; não simula outra física, não desenha tiros e não é transmissão ao vivo.

Servidor de laboratório em 127.0.0.1:18081, sem multiusuário ou acesso externo. A porta não é acessível por um telefone na rede. Teste em aparelho físico precisa de uma conexão controlada a definir, sem abrir firewall ou túnel automaticamente.

## Fontes primárias consultadas

- API base de ações e go(): https://robocode.dev/api/java/dev/robocode/tankroyale/botapi/BaseBot.html (a documentação web não substitui o teste contra o artefato 1.4.0 fixado).
- Exemplo de sensor distância: https://github.com/robocode-dev/tank-royale/blob/c8ad3a8d19a843f6258d6f6f9db7f29229963903/sample-bots/java/Corners/Corners.java
- Emulação de viewport/toque: https://playwright.dev/python/docs/emulation
- Operação por teclado: https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html

Critérios de layout/teclado não equivalem a auditoria WCAG completa. Chromium emulado não comprova uso em Samsung/iPhone físico.
