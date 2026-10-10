# Jornadas e proto-personas

**Versão:** 0.1.0 · **Data:** 2026-10-09 · **Tarefa:** S01-T02.
**Estado:** minuta preparatória. As descrições abaixo são instrumentos de projeto, não perfis derivados de entrevistas realizadas.

## Proto-personas sem identidade fictícia

**P1 — Estudante com acesso predominante ao celular.** Pode usar tela pequena e teclado virtual. Precisa entender o que alterar, não perder o trabalho e conseguir testar sem instalar uma cadeia de ferramentas de desenvolvimento. Familiaridade com programação, aparelho e conexão são variáveis a observar, não características presumidas.

**P2 — Estudante com computador disponível.** Pode usar teclado físico e mais espaço de tela. Precisa do mesmo conteúdo pedagógico, formato de submissão e regulamento de P1. O acesso a computador não deve criar funcionalidades competitivas exclusivas.

**P3 — Professor mediador.** Precisa explicar a relação entre lógica e comportamento, reconhecer dificuldades e avaliar o processo de aprendizagem, não só a colocação final. Recursos avançados de análise de turmas não são necessários no primeiro MVP.

**P4 — Organizador-operador.** Precisa abrir inscrições, fechar versões, iniciar ou pausar a competição, tratar falhas e publicar resultados auditáveis sem editar pontuações silenciosamente.

## Jornada central do participante

| Etapa | Ação e retorno esperado | Falha ou dúvida a tratar |
|---|---|---|
| 1. Entrar | Acessar a plataforma por convite e reconhecer seu papel | Convite inválido, sessão expirada ou acesso negado com orientação clara |
| 2. Entender | Ler objetivo, comandos disponíveis e regras essenciais | Linguagem acessível; não pressupor conhecimento de web/mobile |
| 3. Experimentar exemplo | Abrir um robô de referência e relacionar uma instrução ao comportamento | Distinguir código, parâmetro e resultado da execução |
| 4. Programar | Alterar decisões ou ações do robô no editor escolhido | Erro de sintaxe/estrutura deve indicar onde corrigir sem perder o trabalho |
| 5. Salvar | Persistir uma versão identificável e receber confirmação | Não mostrar “salvo” antes da confirmação; conflito e perda de conexão explícitos |
| 6. Treinar | Solicitar execução da versão e acompanhar estado | Diferenciar aguardando, executando, concluído, inválido e falha técnica |
| 7. Interpretar | Ver resultado e relacioná-lo à hipótese de estratégia | Resultado do motor real, sem garantir que cada alteração melhore a pontuação |
| 8. Melhorar | Comparar tentativas e salvar nova versão | Recuperar versões; não confundir o código editado com o já executado |
| 9. Inscrever | Escolher a versão e confirmar sua participação | Prazo, elegibilidade e congelamento claros; alteração posterior não troca a inscrição |
| 10. Acompanhar | Consultar partidas, classificação e encerramento | Reconexão recupera estado; regras de pontuação acessíveis |

A interface móvel deve preservar essas etapas, não somente as duas últimas. “Criar robô” significa autoria de lógica, não apenas escolher nome, cor ou atributos prontos.

## Jornada do professor

Preparar um desafio adequado ao nível de entrada; apresentar exemplo; pedir que o estudante antecipe o comportamento; orientar uma alteração; observar o teste; discutir divergências entre previsão e resultado; solicitar explicação da estratégia e de uma revisão realizada. A execução da aula não pressupõe que o professor administre infraestrutura durante a atividade.

## Jornada do organizador

Configurar evento e regras; disponibilizar convites; verificar condições operacionais; acompanhar inscrições; congelar versões; executar confrontos; revisar falhas conforme o regulamento; conferir classificação; publicar resultados; registrar incidentes e encerrar o evento.

## Restrições de experiência

Salvar no servidor e recuperar estado após reconexão são propostas distintas de funcionar totalmente offline. O MVP não promete competição ou execução de robôs sem conexão. Instalação como PWA, edição offline e visualização de replay dependem de decisão técnica e não devem ser anunciadas antes de validadas.

## Roteiro de avaliação

Observar P1 e P2 realizando a mesma tarefa: abrir exemplo, alterar uma decisão, salvar, testar e explicar o resultado. Registrar conclusão, ajuda necessária, erros de edição, perda de trabalho e entendimento da versão executada. Usar códigos de participante e dados agregados; nenhuma sessão de usuário real foi observada nesta rodada.
