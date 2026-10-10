# Plano técnico — Feature 003

1. Registrar reprodução local de Walls/Spin Bot pelo responsável sem alegar inspeção de replays/manifestos não recebidos.
2. Comparar texto Java completo, blocos visuais e linguagem restrita. Prototipar a terceira opção como candidato de baixo escopo, não escolha pedagógica definitiva.
3. Parser Python stdlib: dois eventos, quatro ações, condições de energia/distância, valores e estrutura limitados. Nenhum trecho de entrada é inserido em Java sem conversão para enum/número conhecido. Canonicalização e SHA-256.
4. HTML/CSS/JS sem dependências de aplicação: editor textual com botões de inserção, referência, localStorage, validação, batalha e replay resumido em canvas com alternativa textual.
5. HTTP de desenvolvimento apenas no loopback: rotas estáticas fechadas, limites de corpo, Host/Origin/token de sessão, uma batalha concorrente, nenhum arquivo da raiz servido.
6. Reusar imagem Tank Royale 1.4.0 verificada; imagem derivada usa Java wrapper fixo. Entrada vai por stdin, artefatos saem por stdout antes de tmpfs desaparecer. Sem montagem de diretórios do host.
7. Unitários de sintaxe, injeção, limites, HTTP e replay. Chromium 1.57.0/Playwright Python nos viewports 360×800, 390×844 e 1280×900. Dois treinos pela UI no viewport móvel, com motor verdadeiro e comparação de velocidade no replay.
8. Guardar artifact de CI e inspecionar screenshots/resultados. Documentar limites de emulação e procedimento local em um comando Python.

A JVM/servidor Python são meios do experimento, não nova baseline da stack do MVP. O servidor HTTP tem acesso à CLI Docker no host, logo não pode ser exposto ao público. Nenhuma alteração de firewall, VHDX ou serviço existente é autorizada por este plano.
